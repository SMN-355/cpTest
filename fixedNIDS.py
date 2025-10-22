#!/usr/bin/env python3
import subprocess
import time
import re
from collections import Counter

class FixedNIDS:
    def __init__(self):
        self.ping_threshold = 50  # Detect ping flood
        self.ping_count = 0
        self.last_time = time.time()
        
    def capture_packets(self):
        """Capture ICMP (ping) packets"""
        try:
            result = subprocess.run(
                ['timeout', '3', 'tcpdump', '-i', 'wlan1', 'icmp', '-c', '100', '-n'],
                capture_output=True, text=True
            )
            pings = len(re.findall(r'ICMP', result.stdout))
            return pings
        except:
            return 0
    
    def detect_anomaly(self, pings):
        current_time = time.time()
        if current_time - self.last_time > 5:  # Reset every 5s
            self.ping_count = 0
            self.last_time = current_time
            
        self.ping_count += pings
        
        if self.ping_count > self.ping_threshold:
            return f"PING FLOOD: {self.ping_count} packets!"
        return False
    
    def update_oled(self, message):
        try:
            import board, busio, adafruit_ssd1306
            i2c = busio.I2C(board.SCL, board.SDA)
            oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)
            oled.fill(0)
            oled.text(message, 0, 0, 1)
            oled.show()
            print(f"OLED: {message}")
        except Exception as e:
            print(f"OLED Error: {e}")
    
    def run(self):
        print("=== FIXED NIDS STARTED ===")
        while True:
            pings = self.capture_packets()
            print(f"Pings captured: {pings}")
            
            anomaly = self.detect_anomaly(pings)
            if anomaly:
                print(f"*** {anomaly} ***")
                self.update_oled(anomaly)
            else:
                status = f"Pings: {self.ping_count}"
                print(status)
                self.update_oled(status)
            
            time.sleep(2)

if __name__ == "__main__":
    nids = FixedNIDS()
    nids.run()
