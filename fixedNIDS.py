#!/usr/bin/env python3
import subprocess
import time
from RPLCD.i2c import CharLCD

class AllPacketsNIDS:
    def __init__(self):
        self.lcd = CharLCD('PCF8574', 0x27)
        self.total_packets = 0
        self.start_time = time.time()
        self.lcd.clear()
        self.lcd.write_string("PACKET COUNTER")
        time.sleep(1)
        self.lcd.clear()
        self.lcd.write_string("INITIALIZING...")
        time.sleep(1)
        print("PROFESSIONAL PACKET COUNTER READY")
    
    def show_status(self, total, rate):
        self.lcd.clear()
        # Line 1: TOTAL packets
        self.lcd.write_string(f"TOTAL: {total:5d}")
        
        # Line 2: RATE packets/second
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"RATE: {rate:3d}/s")
        
        runtime = int(time.time() - self.start_time)
        print(f"TOTAL: {total} packets | RATE: {rate} pps | TIME: {runtime}s")
    
    def show_alert(self, total, rate):
        self.lcd.clear()
        # Line 1: ALERT
        self.lcd.write_string("TRAFFIC ALERT!")
        
        # Line 2: Total + Rate
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"{total:5d} {rate:3d}/s")
        
        print(f"ALERT: {total} packets at {rate} pps")
    
    def count_packets(self):
        # COUNT ALL PACKETS (4 second capture)
        result = subprocess.run(
            ['timeout', '4', 'tcpdump', '-i', 'any', '-n', '-c', '500'],
            capture_output=True, text=True
        )
        # Count ALL non-empty lines = ALL packets
        packet_lines = [line for line in result.stdout.split('\n') if line.strip()]
        return len(packet_lines)
    
    def run(self):
        last_total = 0
        while True:
            # Count packets in 4 seconds
            new_packets = self.count_packets()
            self.total_packets += new_packets
            
            # Calculate rate (packets per second)
            rate = new_packets // 4
            
            if rate > 25:  # ALERT THRESHOLD: 25+ pps
                self.show_alert(self.total_packets, rate)
                print(f"SECURITY ALERT: High traffic detected")
            else:
                self.show_status(self.total_packets, rate)
            
            time.sleep(1)

if __name__ == "__main__":
    nids = AllPacketsNIDS()
    nids.run()
