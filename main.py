"""
Main entry point for the Artificial Civilization Simulator.
Runs the simulation loop silently and outputs a clean post-flight executive summary scorecard.
Synchronized to pass economic, tech, and public treasury matrices to diagnostics.
"""

import sys
import traceback
from civsim.config import SimConfig
from civsim.simulation import Simulation
from civsim.diagnostics import report, print_history_book


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
        
        # FIX: Pass the simulation's settlements database directly so the report can read economies
        history_data = report(sim.world, sim.agents, sim.settlements, sim.current_tick)
        
        # Print out the fully updated, multi-stratified History Chronicle Scorecard
        print_history_book(history_data)
            
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
