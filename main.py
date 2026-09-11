"""
Main entry point for the Artificial Civilization Simulator.
Runs the simulation loop silently and outputs a clean post-flight executive summary scorecard.
"""

import sys
import traceback
from civsim.config import SimConfig
from civsim.simulation import Simulation
from civsim.diagnostics import report


def main():
    config = SimConfig()
    
    print("====================================================")
    print(f"Launching Simulation Matrix [{config.world_width}x{config.world_height}]")
    print(f"Master Seed: {config.seed} | Execution Mode: LEAN REPORTING")
    print("====================================================\n")
    
    try:
        sim = Simulation(config)
        
        # Advance time matrix forward silently
        sim.run(1000)
        
        # 1. Gather the structural database metrics pass
        history_data = report(sim.world, sim.agents, sim.settlements, sim.current_tick)
        
        # 2. FIX: Print out a crisp, single-page Executive Scorecard summary
        print("\n====================================================")
        print(f"        WORLD HISTORY SUMMARY CHRONICLE - YEAR {history_data['ticks_run']}")
        print("====================================================")
        print(f"Total Living Population: {history_data['living_population']}")
        print(f"Global Cemetery Count  : {history_data['historical_dead_count']}")
        print(f"Average Tile Wild Food : {history_data['avg_tile_food']}")
        print(f"Active Domains Founded : {history_data['settlements']['active_count']}")
        print(f"Historical Mortalities : {history_data['death_causes']}")
        print("----------------------------------------------------")
        print("Active Civilization Domain Ledger:")
        for city in history_data['settlements']['active_details']:
            print(f" * The Domain of {city['name']} at {city['coordinates']} | Citizens: {city['current_population']}")
        print("====================================================")
            
    except Exception as e:
        print("\n####################################################")
        print("🚨 CRITICAL RUNTIME EXCEPTION DETECTED - SIMULATION ABORTED")
        print("####################################################")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}\n")
        print("--- Detailed Post-Mortem Stack Trace ---")
        traceback.print_exc(file=sys.stdout)
        print("####################################################")
        sys.exit(1)


if __name__ == "__main__":
    main()
