#!/usr/bin/env python3
import subprocess
import time
from datetime import datetime
from RPLCD.i2c import CharLCD

class PacketTypeNIDS:
    def __init__(self):
        self.lcd = CharLCD('PCF8574', 0x27)
        self.packet_types = {'ICMP': 0, 'ARP': 0, 'TCP': 0, 'UDP': 0}
        self.thresholds = {'ICMP': 15, 'TCP': 50, 'UDP': 40, 'ARP': 8}
        self.init_display()

    def init_display(self):
        self.lcd.clear()
        self.lcd.write_string("PACKET ANALYZER")
        time.sleep(1)
        self.lcd.clear()
        self.lcd.write_string("ANALYZING...")
        time.sleep(1)
        self.log("PACKET TYPE ANALYZER READY")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def show_status(self, top_type, top_count):
        total = sum(self.packet_types.values())
        self.lcd.clear()
        self.lcd.write_string(f"{top_type:<4} {top_count:3d}")
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"TOTAL: {total:4d}")
        self.log(f"STATUS: {top_type}: {top_count} | TOTAL: {total}")

    def show_alert(self, alert_type, count, snapshot):
        # Alert header
        self.lcd.clear()
        self.lcd.write_string("!! ATTACK ALERT !!")
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"{alert_type} x{count}")
        time.sleep(2)

        # Packet breakdown
        self.lcd.clear()
        self.lcd.write_string("PKT TYPES:")
        self.lcd.cursor_pos = (1, 0)
        pkt_summary = ' '.join([f"{k}:{v}" for k, v in snapshot.items()])
        self.lcd.write_string(pkt_summary[:16])  # Trim to LCD width
        time.sleep(2)

        # Final alert message
        self.lcd.clear()
        self.lcd.write_string("SYSTEM UNDER ATTACK")
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"{alert_type} flood")
        time.sleep(2)

        # Log to console
        self.log(f"SECURITY ALERT: {alert_type} FLOOD - {count} packets")
        self.log("Packet Breakdown:")
        for ptype, val in snapshot.items():
            self.log(f"  {ptype}: {val}")

    def analyze_packets(self):
        result = subprocess.run(
            ['timeout', '4', 'tcpdump', '-i', 'any', '-n', '-c', '500'],
            capture_output=True, text=True
        )
        new_counts = {ptype: 0 for ptype in self.packet_types}
        for line in result.stdout.split('\n'):
            line = line.upper()
            for ptype in new_counts:
                if ptype in line:
                    new_counts[ptype] += 1
        for ptype in new_counts:
            self.packet_types[ptype] += new_counts[ptype]
        return new_counts

    def check_alerts(self, snapshot):
        for ptype, threshold in self.thresholds.items():
            if self.packet_types[ptype] > threshold:
                self.show_alert(ptype, self.packet_types[ptype], snapshot)
                return True
        return False

    def get_top_type(self):
        top_type = max(self.packet_types, key=self.packet_types.get)
        return top_type, self.packet_types[top_type]

    def run(self):
        while True:
            snapshot = self.analyze_packets()
            if self.check_alerts(snapshot):
                time.sleep(4)
            else:
                top_type, top_count = self.get_top_type()
                self.show_status(top_type, top_count)
                time.sleep(1)

if __name__ == "__main__":
    PacketTypeNIDS().run()
