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
from scapy.all import sniff, IP, TCP, UDP, ICMP

# Features our UNSW-NB15 model was trained on:
# 'proto', 'service', 'state', 'spkts', 'sbytes', 'dbytes'

# Helper function to get protocol name as a string
def get_proto(packet):
    if TCP in packet: return 'tcp'
    if UDP in packet: return 'udp'
    if ICMP in packet: return 'icmp'
    return 'other'

# Helper function to guess "service" from port
def port_to_service(port):
    # These are the top services in the UNSW-NB15 dataset
    if port == 80: return 'http'
    if port == 53: return 'dns'
    if port == 443: return 'https'
    if port == 21: return 'ftp'
    if port == 22: return 'ssh'
    if port == 25: return 'smtp'
    return 'other'

# Helper function to get TCP state
def get_tcp_state(flags):
    # Map TCP flags to UNSW-NB15 'state' names
    if flags == 'S': return 'SYN'      # SYN scan
    if flags == 'R' or flags == 'RS': return 'RST' # Reset
    if flags == 'F' or flags == 'FA' or flags == 'FPA': return 'FIN' # Finished
    if flags == 'A' or flags == 'PA': return 'EST' # Established
    return 'other'

class AI_NIDS:
    def __init__(self):
        # 1. --- Hardware Setup ---
        self.lcd = CharLCD('PCF8574', 0x27)
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
        self.oled.fill(0)
        self.oled.show()
        self.font = ImageFont.load_default()

        # 2. --- AI Model Setup ---
        self.log("Loading AI model (UNSW-NB15 v4)...")
        self.model = joblib.load('nids_model.pkl')
        self.encoders = joblib.load('encoders.pkl')
        self.log("AI Model loaded successfully.")
        
        # This list MUST match the training script
        self.features = ['proto', 'service', 'state', 'spkts', 'sbytes', 'dbytes']
        
        # 3. --- NIDS Variables ---
        self.active_flows = {} 
        self.flow_timeout = 10 
        self.total_packets_processed = 0
        self.total_attacks_detected = 0
        self.init_display()

    def init_display(self):
        self.lcd.clear()
        self.lcd.write_string("AI-NIDS v4.0")
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
        line2 = f"svc:{flow_details['service']} P:{flow_details['spkts']}" # Use spkts
        self.lcd.write_string(line1[:16])
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(line2[:16])
        time.sleep(2)
        
        # OLED attacker IPs
        attackers = {attacker_ip: flow_details['spkts']} # Use spkts
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
        This is the new "heart". It is updated to
        extract the new features for the UNSW-NB15 model.
        """
        self.total_packets_processed += 1
        if not IP in packet:
            return 
        try:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            proto = get_proto(packet)
            
            # Default values
            dst_port = 0
            service = 'other'
            state = 'other' # Default state
            
            if proto == 'tcp':
                dst_port = packet[TCP].dport
                service = port_to_service(dst_port) 
                state = get_tcp_state(str(packet[TCP].flags))
            elif proto == 'udp':
                dst_port = packet[UDP].dport
                service = port_to_service(dst_port) 
                state = 'other' # UDP is stateless in this context
            elif proto == 'icmp':
                service = 'icmp'
                state = 'other'

            # Create a unique key for this "flow"
            flow_key = f"{src_ip}-{dst_ip}-{dst_port}-{proto}"

            if flow_key in self.active_flows:
                # Update existing flow
                flow = self.active_flows[flow_key]
                flow['spkts'] += 1 # Increment source packet count
                flow['sbytes'] += len(packet)
                flow['state'] = state # Update to latest state
                flow['last_seen'] = time.time()
            else:
                # Start tracking new flow
                self.active_flows[flow_key] = {
                    'src_ip': src_ip,
                    'proto': proto,
                    'service': service,
                    'state': state,
                    'spkts': 1,
                    'sbytes': len(packet),
                    'dbytes': 0, # We are simplifying; not tracking reply packets
                    'last_seen': time.time()
                }
        except Exception as e:
            self.log(f"Packet processing error: {e}")

    def analyze_flows(self):
        """
        Updated to use the new features.
        The flood/idle logic is the same.
        """
        flows_to_analyze = []
        for key, flow in self.active_flows.items():
            is_idle = (time.time() - flow['last_seen']) > self.flow_timeout
            is_flood = flow['spkts'] > 100 # Check for 100 source packets
            
            if is_idle or is_flood:
                flows_to_analyze.append(key)
                if is_flood:
                    self.log(f"Flood detected! Analyzing flow {key} immediately.")

        if not flows_to_analyze:
            return 

        self.log(f"Analyzing {len(flows_to_analyze)} flows...")

        for key in flows_to_analyze:
            flow_data = self.active_flows.pop(key, None) 
            if flow_data is None:
                continue 
            
            # 1. Build the Feature Vector for the AI
            # We use the hardcoded self.features list
            features = {}
            for col_name in self.features:
                if col_name in flow_data:
                    features[col_name] = flow_data[col_name]
                else:
                    features[col_name] = 0 # Default value
            
            try:
                # 2. Pre-process the features (text to numbers)
                for col in ['proto', 'service', 'state']:
                    encoder = self.encoders[col]
                    val = features[col]
                    
                    if val not in encoder.classes_:
                        val = 'other' # Handle unknown values
                    
                    features[col] = encoder.transform([val])[0]
                
                # 3. Format for the AI
                df_row = pd.DataFrame([features], columns=self.features)
                
                # 4. GET PREDICTION!
                prediction = self.model.predict(df_row)[0]
                
                # 5. ACT!
                # The 'label' column is 1 for attack, 0 for normal
                if prediction == 1: 
                    self.show_alert('AI-DETECTED', flow_data['src_ip'], flow_data)
                
            except Exception as e:
                self.log(f"Error during prediction: {e}")

    def run(self):
        self.log("Starting packet sniffer thread...")
        sniffer_thread = threading.Thread(target=sniff, kwargs={'prn': self.process_packet, 'store': False, 'iface': 'wlan0'})
        sniffer_thread.daemon = True
        sniffer_thread.start()
        
        while True:
            self.analyze_flows()
            self.show_status()
            time.sleep(5) 

if __name__ == "__main__":
    nids = AI_NIDS()
    nids.run()
