import threading
import json
import time
import random
from flask import Flask, render_template, jsonify, request

# --- CONFIGURATION ---
SIMULATION_MODE = True
GRID_API_KEY = "dNPeu7trUmtvqhFCsnQG8I38u9uVVwaeogiQP7l4"
SERIES_ID = "28"

app = Flask(__name__)

# --- SHARED STATE ---
game_data = {
    "map": "OFFLINE",
    "score_c9": 0, "score_opp": 0,
    "events": [], "roster": {}, "last_update": "N/A",
    "stats_history": {"labels": [], "c9_kd": []},
    # NEW: Store best time
    "leaderboard": {"best_time": 99.9, "last_time": 0}
}

view_state = {
    "active_view": "overview",
    "active_filter": "ALL",
    "active_alert": None,
    "last_command": "None"
}

# --- REPLAY ENGINE (Standard Simulation) ---
def run_simulation():
    try:
        with open('match_replay.json', 'r') as f:
            script = json.load(f)
    except: return

    while True:
        game_data['map'] = "SIMULATION FEED"
        game_data['events'] = []
        # Pre-fill roster
        game_data['roster'] = {
            "Fudge": {"kills": 0, "role": "Top", "risk": "LOW"},
            "Blaber": {"kills": 0, "role": "Jungle", "risk": "LOW"},
            "Jojopyun": {"kills": 0, "role": "Mid", "risk": "LOW"},
            "Berserker": {"kills": 0, "role": "Bot", "risk": "LOW"},
            "Vulcan": {"kills": 0, "role": "Support", "risk": "LOW"}
        }
        
        for step in script:
            time.sleep(step['delay'])
            current_time = time.strftime("%H:%M:%S")
            game_data['last_update'] = current_time

            if step['type'] == 'event':
                if step['action'] == 'killed':
                    actor = step['actor']
                    if actor in game_data['roster']:
                        game_data['roster'][actor]['kills'] += 1
                        msg = f"KILL: {step['actor']} -> {step['target']}"
                        game_data['events'].insert(0, {"time": current_time, "msg": msg})
                elif 'msg' in step:
                    game_data['events'].insert(0, {"time": current_time, "msg": step['msg']})
            elif step['type'] == 'state':
                game_data['map'] = step['map']

# --- ROUTES ---
@app.route('/')
def index(): return render_template('dashboard.html')

@app.route('/api/telemetry', methods=['POST'])
def receive_command():
    cmd = request.json
    view_state['last_command'] = f"{cmd.get('key_name', 'CMD')} -> {cmd['type']}"
    
    if cmd['type'] == 'alert':
        view_state['active_alert'] = cmd['target']
        if cmd['target'] == 'C9': view_state['active_filter'] = 'ALL'
        
        # NEW: Handle Defusal Time
        if cmd['target'] == 'SPIKE_DEFUSED':
            time_taken = cmd.get('time_taken', 0)
            game_data['leaderboard']['last_time'] = time_taken
            if time_taken < game_data['leaderboard']['best_time']:
                game_data['leaderboard']['best_time'] = time_taken

    elif cmd['type'] == 'filter':
        view_state['active_filter'] = cmd['target']
        view_state['active_view'] = 'overview'
        view_state['active_alert'] = None
        
    elif cmd['type'] == 'view':
        view_state['active_view'] = cmd['target']
        view_state['active_filter'] = 'ALL'
        view_state['active_alert'] = None

    return jsonify({"status": "ACK"})

@app.route('/api/sync')
def sync_frontend():
    return jsonify({"game": game_data, "view": view_state})

if __name__ == '__main__':
    t = threading.Thread(target=run_simulation)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=5000)
