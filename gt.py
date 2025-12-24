import serial
import serial.tools.list_ports  # <--- Vital for auto-detection
import json
import time
import requests
import psutil
import psycopg2
import sys

# --- CONFIGURATION ---
DB_HOST = "db.qhzlenfzebrrahmnngty.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres.qhzlenfzebrrahmnngty"
DB_PASS = "Y8MgA0DGfXov4Sbr"  # <--- Update this!
DB_PORT = "6543"

WEBHOOK_URL = "https://hook.eu1.make.com/3n3zs73263kke45n7rkxeo5rhn7gdqeh"
DEVICE_ID = "SENTINEL-ZERO-01"
BAUD_RATE = 115200

# --- HELPER: FIND PICO AUTOMATICALLY ---
def find_pico_port():
    print("🔍 Scanning USB ports for Pico...")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Pico identifiers usually contain "Board in FS mode" or VID:PID 2e8a:0005
        # We search for "ACM" or generic USB Serial names
        if "ACM" in port.device or "USB" in port.device:
            print(f"   -> Found candidate: {port.device} - {port.description}")
            return port.device
    return None

# --- MAIN LOGIC ---
pico_port = find_pico_port()

if not pico_port:
    print("\n❌ CRITICAL ERROR: No Pico found connected via USB.")
    print("   1. Check USB Cable (Is it a DATA cable?)")
    print("   2. Try the other USB port on the Pi Zero (Inner port).")
    sys.exit(1)

print(f"✅ Connecting to Pico at {pico_port}...")

try:
    # We add a small timeout to not block forever
    ser = serial.Serial(pico_port, BAUD_RATE, timeout=1)
    ser.flush() # Clear old data
    print("🚀 Gateway is Running & Listening...")
except serial.SerialException as e:
    print(f"\n❌ ACCESS DENIED to {pico_port}")
    print(f"   Error details: {e}")
    print("   -> TIP: Run 'sudo fuser -k /dev/ttyACM0' to kill the process holding it.")
    sys.exit(1)

# --- LISTENER LOOP ---
while True:
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').strip()
            
            # Filter garbage
            if not line.startswith("{"):
                continue
            
            data = json.loads(line)
            threat = data.get("threat", "Unknown")
            risk = data.get("risk", 0)
            cpu = psutil.cpu_percent()
            
            print(f"\n⚠️ INTRUSION: {threat} (Risk: {risk})")
            
            # Database & Alert Logic
            # (Insert your save_to_db and trigger_alert functions here)
            
        except Exception as e:
            print(f"Error: {e}")
            
    time.sleep(0.01)
