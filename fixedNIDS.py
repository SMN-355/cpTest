def show_alert(self, alert_type, count, snapshot):
    self.lcd.clear()
    self.lcd.write_string("!! ATTACK ALERT !!")
    self.lcd.cursor_pos = (1, 0)
    self.lcd.write_string(f"{alert_type} x{count}")
    time.sleep(2)

    # Show full packet breakdown
    self.lcd.clear()
    self.lcd.write_string("PKT TYPES:")
    self.lcd.cursor_pos = (1, 0)
    pkt_summary = ' '.join([f"{k}:{v}" for k, v in snapshot.items()])
    self.lcd.write_string(pkt_summary[:16])  # Trim to fit LCD
    time.sleep(2)

    # Final status message
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
