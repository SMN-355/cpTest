#!/usr/bin/env python3
import subprocess
import time
from RPLCD.i2c import CharLCD

class FixedLCDNIDS:
    def __init__(self):
        self.lcd = CharLCD('PCF8574', 0x27)
        self.count = 0
        self.lcd.clear()
        self.lcd.write_string("NIDS START")
        print("✓ FIXED NIDS READY")
        time.sleep(2)
    
    def show(self, msg):
        self.lcd.clear()
        display_msg = msg[:16]
        self.lcd.write_string(display_msg)
        print(f"LCD: {display_msg}")
    
    def scan(self):
        # FIXED: ANY interface + NO count limit + longer timeout
        try:
            result = subprocess.run(
                ['timeout', '5', 'tcpdump', '-i', 'any', 'icmp', '-n'],
                capture_output=True, text=True, check=False
            )
            # Count ALL ICMP lines
            icmp_lines = [line for line in result.stdout.split('\n') if 'ICMP' in line]
            count = len(icmp_lines)
            print(f"DEBUG: Captured {count} ICMP packets")
            return count
        except Exception as e:
            print(f"SCAN ERROR: {e}")
            return 0
    
    def run(self):
        while True:
            pings = self.scan()
            self.count += pings
            print(f"TOTAL PINGS: {self.count}")
            
            if self.count > 5:  # LOWERED THRESHOLD
                self.show(f"ATTACK! {self.count}")
                print("*** FLOOD DETECTED! ***")
                time.sleep(3)
                self.count = 0
            else:
                self.show(f"OK P:{self.count}")
            
            time.sleep(2)

if __name__ == "__main__":
    nids = FixedLCDNIDS()
    nids.run()
