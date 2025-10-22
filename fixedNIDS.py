#!/usr/bin/env python3
import subprocess
import time
from RPLCD.i2c import CharLCD

class PacketTypeNIDS:
    def __init__(self):
        self.lcd = CharLCD('PCF8574', 0x27)
        self.packet_types = {'ICMP': 0, 'ARP': 0, 'TCP': 0, 'UDP': 0}
        self.start_time = time.time()
        self.lcd.clear()
        self.lcd.write_string("PACKET ANALYZER")
        time.sleep(1)
        self.lcd.clear()
        self.lcd.write_string("ANALYZING...")
        time.sleep(1)
        print("PACKET TYPE ANALYZER READY")
    
    def show_status(self, top_type, top_count):
        self.lcd.clear()
        # Line 1: TOP packet type
        self.lcd.write_string(f"{top_type:<4} {top_count:3d}")
        
        # Line 2: Total packets
        total = sum(self.packet_types.values())
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"TOTAL: {total:4d}")
        
        print(f"STATUS: {top_type}: {top_count} | TOTAL: {total}")
    
    def show_alert(self, alert_type, count):
        self.lcd.clear()
        # Line 1: ALERT TYPE
        self.lcd.write_string(f"ALERT: {alert_type}")
        
        # Line 2: Count
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"{count:4d}pkts")
        
        print(f"SECURITY ALERT: {alert_type} FLOOD - {count} packets")
    
    def analyze_packets(self):
        # Capture 4 seconds, ALL packet types
        result = subprocess.run(
            ['timeout', '4', 'tcpdump', '-i', 'any', '-n', '-c', '500'],
            capture_output=True, text=True
        )
        
        new_counts = {'ICMP': 0, 'ARP': 0, 'TCP': 0, 'UDP': 0}
        
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            line = line.upper()
            
            if 'ICMP' in line:
                new_counts['ICMP'] += 1
            elif 'ARP' in line:
                new_counts['ARP'] += 1
            elif 'TCP' in line:
                new_counts['TCP'] += 1
            elif 'UDP' in line:
                new_counts['UDP'] += 1
        
        # Update totals
        for ptype in new_counts:
            self.packet_types[ptype] += new_counts[ptype]
        
        return new_counts
    
    def check_alerts(self):
        total_icmp = self.packet_types['ICMP']
        total_tcp = self.packet_types['TCP']
        total_udp = self.packet_types['UDP']
        total_arp = self.packet_types['ARP']
        
        # ALERT THRESHOLDS
        if total_icmp > 15:
            self.show_alert("ICMP", total_icmp)
            return True
        elif total_tcp > 50:
            self.show_alert("TCP ", total_tcp)
            return True
        elif total_udp > 40:
            self.show_alert("UDP ", total_udp)
            return True
        elif total_arp > 8:
            self.show_alert("ARP ", total_arp)
            return True
        
        return False
    
    def get_top_type(self):
        top_type = max(self.packet_types, key=self.packet_types.get)
        top_count = self.packet_types[top_type]
        return top_type, top_count
    
    def run(self):
        while True:
            self.analyze_packets()
            
            if self.check_alerts():
                time.sleep(4)
            else:
                top_type, top_count = self.get_top_type()
                self.show_status(top_type, top_count)
            
            time.sleep(1)

if __name__ == "__main__":
    nids = PacketTypeNIDS()
    nids.run()
