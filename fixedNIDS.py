#!/usr/bin/env python3
import subprocess
import time
from RPLCD.i2c import CharLCD

class LCDNIDS:
    def __init__(self):
        # Initialize LCD1602 (address 0x27)
        self.lcd = CharLCD('PCF8574', 0x27)
        self.count = 0
        self.lcd.clear()
        self.lcd.write_string("NIDS READY")
        print("✓ LCD NIDS READY")
        time.sleep(2)
    
    def show(self, msg):
        self.lcd.clear()
        # Truncate to 16 characters
        display_msg = msg[:16]
        self.lcd.write_string(display_msg)
        print(f"LCD: {display_msg}")
    
    def scan(self):
        result = subprocess.run(
            ['timeout', '3', 'tcpdump', '-i', 'wlan1', 'icmp', '-c', '50'],
            capture_output=True, text=True
        )
        return result.stdout.count('ICMP')
    
    def run(self):
        while True:
            pings = self.scan()
            self.count += pings
            print(f"Pings: {self.count}")
            
            if self.count > 10:
                self.show(f"ATTACK! {self.count}")
                print("*** FLOOD DETECTED! ***")
                time.sleep(3)
                self.count = 0
            else:
                self.show(f"OK P:{self.count}")
            
            time.sleep(1)

if __name__ == "__main__":
    nids = LCDNIDS()
    nids.run()
