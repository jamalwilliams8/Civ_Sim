"""
main.py
Main entry point for the Artificial Civilization Simulator.
Optimized to handle real-time simulation loops completely in RAM memory,
eliminating disk I/O bottlenecks to fix lag and maximize speed controls.
"""

import os
import sys
import time
import threading
import random
from collections import deque
from flask import Flask, jsonify, request, send_from_directory
from civsim.config import SimConfig
from civsim.simulation import Simulation

SUBFOLDER_PATH = os.path.join(os.path.dirname(__file__), "civsim")
sys.path.append(SUBFOLDER_PATH)
from civsim.civisim_GUI import civisim_GUI, register_simulation

app = Flask(__name__, static_folder=SUBFOLDER_PATH)

# High-speed volatile RAM cache (holds the most recent snapshot frame)
ram_telemetry_cache = deque(maxlen=1)

sim_state = {
    "sim_object": None,
    "is_running": True,
    "delay": 0.1,  # Default execution latency throttle
    "god_trigger": None
}

def simulation_worker():
    config = SimConfig()
    sim_state["sim_object"] = Simulation(config)
    sim = sim_state["sim_object"]
    register_simulation(sim)
    
    print("🚀 In-Memory RAM Telemetry Engine Core Online. Lag buffers neutralized.")
    
    while True:
        if sim_state["is_running"]:
            if sim_state["god_trigger"]:
                cmd = sim_state["god_trigger"]
                sim_state["god_trigger"] = None
                execute_god_power(sim, cmd)

            # Advance a single loop cycle step
            sim.step()
            
            # Extract snapshot directly to RAM cache instead of writing to disk
            snapshot = civisim_GUI()
            ram_telemetry_cache.append(snapshot)
            
            # Responsive pacing sleep throttle
            time.sleep(sim_state["delay"])
        else:
            time.sleep(0.1)

def execute_god_power(sim, command):
    tick = sim.current_tick
    if command == "spawn_raiders":
        sim.history.record_event(tick, "WAR", 50, 50, "A marauder army breached the outer borders, raiding trade nodes!")
    elif command == "market_crash":
        sim.history.record_event(tick, "MARKET", 0, 0, "A severe financial panic has wiped out treasury capital reserves.")
    elif command == "gift_knowledge":
        sim.history.record_event(tick, "INNOVATION", 0, 0, "Divine inspiration granted all domains massive breakthroughs.")

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/telemetry', methods=['GET'])
def get_ram_telemetry():
    if len(ram_telemetry_cache) > 0:
        return jsonify(ram_telemetry_cache[0])
    return jsonify({"error": "Cache initializing"}), 202

@app.route('/api/control', methods=['POST'])
def update_controls():
    data = request.json
    action = data.get("action")
    if action == "pause":
        sim_state["is_running"] = False
    elif action == "resume":
        sim_state["is_running"] = True
    elif action == "speed_up":
        sim_state["delay"] = max(0.0, sim_state["delay"] - 0.02)  # Accelerates simulation speed
    elif action == "speed_down":
        sim_state["delay"] = min(1.5, sim_state["delay"] + 0.05)   # Decelerates simulation speed
    elif action.startswith("god_"):
        sim_state["god_trigger"] = action.replace("god_", "")
    return jsonify({"status": "success", "delay": sim_state["delay"]})

@app.route('/api/settlement/<s_id>', methods=['GET'])
def inspect_settlement(s_id):
    sim = sim_state["sim_object"]
    if not sim or not hasattr(sim, "settlements"):
        return jsonify({"error": "Simulation offline"}), 500
        
    target = None
    for item in sim.settlements.settlements.values():
        if str(getattr(item, "id", hash(item.name))) == s_id:
            target = item
            break
            
    if not target:
        return jsonify({"error": "Records unallocated"}), 404
        
    current_pop = 0
    settlement_id_raw = getattr(target, "id", None)
    if sim and hasattr(sim, "agents"):
        if hasattr(sim.agents, "living_agents"):
            current_pop += sum(1 for a in sim.agents.living_agents() if getattr(a, "settlement_id", None) == settlement_id_raw)
        if hasattr(sim.agents, "cohorts"):
            current_pop += sum(c.count for c in sim.agents.cohorts.values() if getattr(c, "settlement_id", None) == settlement_id_raw)

    if current_pop == 0:
        current_pop = getattr(target, "population", random.randint(110, 340))

    vault_wealth = current_pop * random.randint(15, 45)
    upkeep_costs = int(vault_wealth * 0.18)  # 18% structural tax/upkeep burn sink
    net_treasury = max(100, vault_wealth - upkeep_costs)

    return jsonify({
        "name": target.name,
        "population": current_pop,
        "stability": getattr(target, "stability_score", 0.9),
        "coords": f"({target.home_x}, {target.home_y})",
        "treasury": f"{net_treasury:,} Gold (After {upkeep_costs}g Fort Upkeep)",
        "commerce": f"Active Market Corridors",
        "defense_rating": f"Level {random.randint(2, 5)} Citadel",
        "resource_focus": "💎 Mithril Alloys & Industrial Smelting"
    })

if __name__ == "__main__":
    engine_thread = threading.Thread(target=simulation_worker, daemon=True)
    engine_thread.start()
    app.run(port=8000, debug=False, use_reloader=False)
