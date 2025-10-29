#!/usr/bin/env python3
import time
import joblib
import pandas as pd
from datetime import datetime
from collections import defaultdict
from RPLCD.i2c import CharLCD
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import threading
from scapy.all import sniff, IP, TCP, UDP

def port_to_service(port):
    if port == 80:
        return 'http'
    elif port == 443:
        return 'http_443'
    elif port == 21:
        return 'ftp'
    elif port == 23:
        return 'telnet'
    elif port == 25:
        return 'smtp'
    elif port == 53:
        return 'domain_u'
    elif port == 22:
        return 'ssh'
    else:
        return 'other'

class AI_NIDS:
    def __init__(self):
        self.lcd = CharLCD('PCF8574', 0x27)
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
        self.oled.fill(0)
        self.oled.show()
        self.font = ImageFont.load_default()

        self.log("Loading AI model...")
        self.model = joblib.load('nids_model.pkl')
        self.encoders = joblib.load('encoders.pkl')
        self.log("AI Model loaded successfully.")
        
        with open('features.list', 'r') as f:
            self.features = [line.strip() for line in f]
        
        self.active_flows = {} 
        self.flow_timeout = 10 
        self.total_packets_processed = 0
        self.total_attacks_detected = 0
        self.init_display()

    def init_display(self):
        self.lcd.clear()
        self.lcd.write_string("AI-NIDS v1.0")
        time.sleep(1)
        self.lcd.clear()
        self.lcd.write_string("Initializing...")
        time.sleep(1)
        self.log("AI-NIDS READY")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def show_status(self):
        self.lcd.clear()
        self.lcd.write_string(f"Flows: {len(self.active_flows):<4} Pkts: {self.total_packets_processed:<6}")
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"Attacks: {self.total_attacks_detected:<4}")
        self.log(f"STATUS: Flows: {len(self.active_flows)} | Pkts: {self.total_packets_processed} | Alerts: {self.total_attacks_detected}")

    def show_alert(self, alert_type, attacker_ip, flow_details):
        self.total_attacks_detected += 1
        
        # LCD alert
        self.lcd.clear()
        self.lcd.write_string("!!AI ALERT!!")
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"{alert_type} "[:16])
        time.sleep(2)

        # LCD packet breakdown
        self.lcd.clear()
        line1 = f"src:{attacker_ip}"
        line2 = f"svc:{flow_details['service']} P:{flow_details['count']}"
        self.lcd.write_string(line1[:16])
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(line2[:16])
        time.sleep(2)
        
        # OLED attacker IPs
        attackers = {attacker_ip: flow_details['count']}
        self.display_oled_alert(alert_type, attackers)

        # Console log
        self.log(f"!! AI SECURITY ALERT: {alert_type} !!")
        self.log(f"  Attacker IP: {attacker_ip}")
        self.log(f"  Flow Details: {flow_details}")

    def display_oled_alert(self, alert_type, attackers):
        self.oled.fill(0)
        image = Image.new("1", (self.oled.width, self.oled.height))
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), f"AI ALERT: {alert_type}", font=self.font, fill=255)
        draw.text((0,14), "Attacker IP:", font=self.font, fill=255)
        
        y=30
        for ip, count in list(attackers.items())[:3]:
            draw.text((0, y), f"{ip} : {count} pkts", font=self.font, fill=255)
            y += 10
        self.oled.image(image)
        self.oled.show()

    def process_packet(self, packet):
        """
        This function is the new "heart". It is called by Scapy
        for EVERY single packet the Pi sees.
        """
        self.total_packets_processed += 1
        if not (IP in packet and (TCP in packet or UDP in packet)):
            return

        try:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            
            if TCP in packet:
                protocol = 'tcp'
                dst_port = packet[TCP].dport
                flag = str(packet[TCP].flags)
            else:
                protocol = 'udp'
                dst_port = packet[UDP].dport
                flag = 'SF' 

            src_bytes = len(packet)
            dst_bytes = 0
            flow_key = f"{src_ip}-{dst_ip}-{dst_port}-{protocol}"

            if flow_key in self.active_flows:
                flow = self.active_flows[flow_key]
                flow['src_bytes'] += src_bytes
                flow['count'] += 1
                flow['last_seen'] = time.time()
            else:
                self.active_flows[flow_key] = {
                    'src_ip': src_ip,
                    'protocol_type': protocol,
                    'service': port_to_service(dst_port),
                    'flag': flag,
                    'src_bytes': src_bytes,
                    'dst_bytes': dst_bytes,
                    'count': 1,
                    'start_time': time.time(),
                    'last_seen': time.time()
                }
        except Exception as e:
            self.log(f"Packet processing error: {e}")

    def analyze_flows(self):
        """
        This is the "brain". It loops over all active flows,
        checks for "idle" flows (ones that are finished),
        and sends them to the AI for a prediction.
        """
        idle_flows = []
        
        for key, flow in self.active_flows.items():
            if time.time() - flow['last_seen'] > self.flow_timeout:
                idle_flows.append(key)

        if not idle_flows:
            return 

        self.log(f"Analyzing {len(idle_flows)} idle flows...")

        for key in idle_flows:
            flow_data = self.active_flows.pop(key) 
            features = {}
            for col_name in self.features:
                if col_name in flow_data:
                    features[col_name] = flow_data[col_name]
                else:
                    features[col_name] = 0
            
            try:
                for col in ['protocol_type', 'service', 'flag']:
                    encoder = self.encoders[col]
                    val = features[col]
                    if val not in encoder.classes_:
                        val = 'other'
                    
                    features[col] = encoder.transform([val])[0]
                
                df_row = pd.DataFrame([features], columns=self.features)
                prediction = self.model.predict(df_row)[0]
                if prediction == 'attack':
                    self.show_alert('AI-DETECTED', flow_data['src_ip'], flow_data)
                
            except Exception as e:
                self.log(f"Error during prediction: {e}")
              
    def run(self):
        """
        This is the new main loop.
        It runs the packet sniffer in a background thread
        and the analyzer/display in the main thread.
        """
        self.log("Starting packet sniffer thread...")
        sniffer_thread = threading.Thread(target=sniff, kwargs={'prn': self.process_packet, 'store': False, 'iface': 'any'})
        sniffer_thread.daemon = True
        sniffer_thread.start()

        while True:
            self.analyze_flows()
            self.show_status()
            time.sleep(2)

if __name__ == "__main__":
    nids = AI_NIDS()
    nids.run()
