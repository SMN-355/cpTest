# C9 Tactical Command: The "Spike Defusal" Challenge
A high-pressure **"Spike Defusal" Event Game** where fans race against the clock to disarm a C9 spike, powered by a live-syncing hardware ecosystem that mimics the pressure of the VCT stage.
[cite_start]This project combines a fast-paced **Event Mini-Game** [cite: 134] with a professional **Red Team Scouting Dashboard**, proving that the fun is built on pro-grade tech.

---
## How It Works
The ecosystem consists of two synchronized nodes:

* The C9 Server (Raspberry Pi Zero W):<br>
Acts as the central game authority, validating defusal codes and managing the game state.<br>
Connects to the **GRID Series Events WebSocket** to ingest live match data when in "Analyst Mode".<br>
Runs a Flask Web Server that hosts the **Arena Dashboard**.<br>

* The Field Device (Raspberry Pi Pico WH):<br>
**Mode 1 (Fan Game):** Runs the "Spike Defusal" simulator. Fans must Arm the device and enter a code before the OLED timer hits zero.<br>
[cite_start]**Mode 2 (Analyst Tool):** Acts as a "Tactical Stream Deck." [cite: 135]
[cite_start]Pressing keys on the physical keypad sends commands to the C2 Server to filter the dashboard views instantly (e.g., highlighting only the "Jungle" matchup). [cite: 136]

---
## Hardware Requirements
* [cite_start]Server: Raspberry Pi Zero W (or any Python-capable PC/Pi). [cite: 137]
* [cite_start]Client: Raspberry Pi Pico WH. [cite: 137]
* [cite_start]Display: SSD1306 OLED Display (128x64, I2C). [cite: 138]
* [cite_start]Input: 4x4 Matrix Membrane Keypad. [cite: 138]
* [cite_start]Connectivity: Local Wi-Fi Network. [cite: 138]

---
## Installation

* Part 1: The C9 Server (_Raspberry Pi Zero W_)<br>
Clone this repository:<br>
```bash
git clone [https://github.com/PS-003R32/C9-Tactical.git](https://github.com/PS-003R32/C9-Tactical.git)
cd C9-Tactical/
```

### Install Dependencies:
```bash
pip3 install flask websocket-client requests
```
### Configure API Key:
Open `app.py`.
Set `SIMULATION_MODE = True` for offline booth demos, or paste your `GRID_API_KEY` for live data.

Run the Server: python3 app.py
The dashboard is now live at _**http://<PI_ZERO_IP>:5000**_

Part 2: The Field Device (Raspberry Pi Pico WH)
Flash MicroPython: Ensure your Pico WH has the latest uf2 firmware. 
Upload Libraries: Save ssd1306.py (standard library) to the Pico. 
Configure Network: Open main.py. Update SSID and PASSWORD with your Wi-Fi credentials. Update SERVER_URL to point to your Pi Zero: http://192.168.1.XX:5000/api/telemetry. 
Wiring:  OLED: SDA -> GP4, SCL -> GP5. Keypad Rows: GP6, GP7, GP8, GP9. Keypad Cols: GP5, GP4, GP3, GP2.

Usage Manual
The Physical-to-Logical Mapping. 
| Physical Key | Logical Function | Category | 
|----------------|----------------------|---------------------| 
| 1 | TOP | Lane Filter | 
| 2 | JGL | Lane Filter | 
| 3 | MID | Lane Filter | 
| A | ARM | Game Trigger | 
| 4 | BOT | Lane Filter | 
| 5 | SUP | Lane Filter | 
| 6 | TEAM | Alert/Highlight | 
| B | BANS | View Switcher | 
| 7 | OPP1 | Alert/Highlight | 
| 8 | OPP2 | (Reserved) | 
| 9 | OPP3 | (Reserved) | 
| C | STATS | View Switcher | 
| * | * | Game Input | 
| 0 | 0 | Game Input | 
| # | # | Game Input | 
| D | HOME | System Reset |

Detailed Function Explanation 
A. Game Mode (The Fan Experience) Designed for the Event Booth.
Start: Press 'A' to ARM the device.
The Challenge: A 45-second countdown begins on the OLED.
Action: Enter the secret code (Default: 7359) and press # before time runs out.
Win: The Arena Dashboard turns CYAN (ROUND SECURED). 
Lose: The Arena Dashboard triggers a "DETONATION" event.
B. Analyst Mode (Default) When the game is not running, the keypad acts as a tactical controller for the dashboard.
Lane Filters (1-5): Instantly cuts through the noise.
Action: Press 2 (JGL).
Result: Dims all rows on the dashboard except the Jungle matchup, allowing the coach to focus. 
View Switchers (B, C, D): Changes the screen layout.
STATS (Key 'C'): Switches to the live "Momentum Graph" (Chart.js). 
BANS (Key 'B'): Switches to the Pick/Ban Recommendation engine. 
HOME (Key 'D'): Resets the dashboard to the main Roster View. 
Tactical Alerts (6, 7):

TEAM (Key '6'): Highlights Cloud9 players in Cyan to signal a great play. 


OPP1 (Key '7'): Flags the enemy carry in Red as a "Critical Threat". 

The keypad isn't just a number pad. It is a context-aware controller. During a tactical review, Button '2' focuses the dashboard on the Jungle matchup. But during a fan activation event, that same Button '2' becomes part of the defusal code for the Spike Simulator. This dual-purpose design allows one hardware device to serve both analysts and fans.
