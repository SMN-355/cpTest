#!/usr/bin/env python3
import subprocess
import time
from RPLCD.i2c import CharLCD

class ProLCDNIDS:
    def __init__(self):
        self.lcd = CharLCD('PCF8574', 0x27)
        self.count = 0
        self.start_time = time.time()
        self.show_welcome()
        print("✓ PROFESSIONAL NIDS READY")
    
    def show_welcome(self):
        self.lcd.clear()
        self.lcd.write_string("NETWORK IDS")
        time.sleep(1)
        self.lcd.clear()
        self.lcd.write_string("MONITORING...")
        time.sleep(1)
    
    def show_status(self, pings):
        self.lcd.clear()
        # Line 1: Status + Count
        self.lcd.write_string(f"PINGS: {pings:2d}")
        
        # Line 2: Progress bar (0-16 chars)
        bar_length = min(pings, 16)
        bar = "#" * bar_length + " " * (16 - bar_length)
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(bar)
        
        print(f"STATUS: {pings} pings | {'#' * bar_length}{' ' * (16 - bar_length)}")
    
    def show_attack(self, pings):
        self.lcd.clear()
        # Line 1: BIG ALERT
        self.lcd.write_string("*** ATTACK! ***")
        
        # Line 2: Count + Time
        runtime = int(time.time() - self.start_time)
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"{pings}pkts {runtime}s")
        
        print(f"*** SECURITY ALERT! ***")
        print(f"FLOOD: {pings} packets in {runtime} seconds")
    
    def scan(self):
        # Capture 4 seconds of traffic
        result = subprocess.run(
            ['timeout', '4', 'tcpdump', '-i', 'any', 'icmp', '-n'],
            capture_output=True, text=True
        )
        icmp_count = len([line for line in result.stdout.split('\n') if 'ICMP' in line])
        return icmp_count
    
    def run(self):
        while True:
            pings = self.scan()
            self.count += pings
            
            if self.count > 6:  # DETECTS FAST
                self.show_attack(self.count)
                print(f"🚨 INTRUSION DETECTED! {self.count} PINGS")
                time.sleep(4)
                self.count = 0
            else:
                self.show_status(self.count)
            
            time.sleep(1)

if __name__ == "__main__":
    nids = ProLCDNIDS()
    nids.run()
