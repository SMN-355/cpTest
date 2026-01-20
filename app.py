import threading
import json
import time
import random
from flask import Flask, render_template, jsonify, request

# --- CONFIGURATION ---
SIMULATION_MODE = True
GRID_API_KEY = "dNPeu7trUmtvqhFCsnQG8I38u9uVVwaeogiQP7l4"
SERIES_ID = "28"
GRID_WS_URL = f"wss://api.grid.gg/live-data-feed/series/{SERIES_ID}?key={GRID_API_KEY}"

app = Flask(__name__)

# --- SHARED STATE ---
game_data = {
    "map": "OFFLINE",
    "score_c9": 0,
    "score_opp": 0,
    "events": [],
    "roster": {}, 
    "last_update": "N/A",
    "stats_history": {
        "labels": [],
        "c9_kd": []
    }
}

view_state = {
    "active_view": "overview",
    "active_filter": "ALL",
    "active_alert": None,
    "last_command": "None",
    "hardware_status": "ONLINE"
}

# --- REPLAY ENGINE ---
def run_simulation():
    print(">>> STARTING SIMULATION MODE")
    try:
        with open('match_replay.json', 'r') as f:
            script = json.load(f)
    except:
        print("Error: match_replay.json not found.")
        return

    while True:
        # 1. Reset Game State
        game_data['map'] = "SIMULATION FEED"
        game_data['events'] = []
        
        # FIX: PRE-FILL ROSTER TO PREVENT "BLANK" SCREEN
        # This ensures the names are always visible even before the first kill
        game_data['roster'] = {
            "Fudge": {"kills": 0, "role": "Top", "risk": "LOW"},
            "Blaber": {"kills": 0, "role": "Jungle", "risk": "LOW"},
            "Jojopyun": {"kills": 0, "role": "Mid", "risk": "LOW"},
            "Berserker": {"kills": 0, "role": "Bot", "risk": "LOW"},
            "Vulcan": {"kills": 0, "role": "Support", "risk": "LOW"}
        }
        
        game_data['stats_history']['labels'] = []
        game_data['stats_history']['c9_kd'] = []
        
        c9_kills_total = 0
        c9_deaths_total = 0
        
        for step in script:
            time.sleep(step['delay'])
            current_time = time.strftime("%H:%M:%S")
            game_data['last_update'] = current_time

            if step['type'] == 'event':
                if step['action'] == 'killed':
                    msg = f"KILL: {step['actor']} -> {step['target']}"
                    game_data['events'].insert(0, {"time": current_time, "msg": msg})
                    
                    # Update Roster Stats
                    actor = step['actor']
                    # Only update if exists, or create new if not (e.g. Enemy)
                    if actor not in game_data['roster']:
                        game_data['roster'][actor] = {
                            "kills": 0, 
                            "role": step.get('role', 'Unknown'), 
                            "risk": "LOW"
                        }
                    
                    game_data['roster'][actor]['kills'] += 1
                    
                    # Graph Logic
                    c9_kills_total += 1
                    kd_ratio = c9_kills_total / (c9_deaths_total if c9_deaths_total > 0 else 1)
                    
                    game_data['stats_history']['labels'].append(current_time)
                    game_data['stats_history']['c9_kd'].append(round(kd_ratio, 2))
                    
                    if len(game_data['stats_history']['labels']) > 15:
                        game_data['stats_history']['labels'].pop(0)
                        game_data['stats_history']['c9_kd'].pop(0)

                elif 'msg' in step:
                    game_data['events'].insert(0, {"time": current_time, "msg": step['msg']})
            
            elif step['type'] == 'state':
                game_data['map'] = step['map']

# --- FLASK ROUTES ---
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/telemetry', methods=['POST'])
def receive_command():
    cmd = request.json
    view_state['last_command'] = f"{cmd.get('key_name', 'CMD')} -> {cmd['type']}"
    
    if cmd['type'] == 'filter':
        view_state['active_filter'] = cmd['target']
        view_state['active_view'] = 'overview'
        view_state['active_alert'] = None
        
    elif cmd['type'] == 'view':
        view_state['active_view'] = cmd['target']
        view_state['active_filter'] = 'ALL'
        view_state['active_alert'] = None
        
    elif cmd['type'] == 'alert':
        view_state['active_alert'] = cmd['target']
        if cmd['target'] == 'C9':
            view_state['active_filter'] = 'ALL'
            
    return jsonify({"status": "ACK"})

@app.route('/api/sync')
def sync_frontend():
    return jsonify({"game": game_data, "view": view_state})

if __name__ == '__main__':
    t = threading.Thread(target=run_simulation)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=5000)
