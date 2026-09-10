"""
Main entry point for the Artificial Civilization Simulator.
Runs the simulation loop and outputs the world history chronicle.
"""

from civsim.config import SimConfig
from civsim.simulation import Simulation
from civsim.diagnostics import report, print_history_book


def main():
    # 1. Initialize configuration and simulation engine properties
    config = SimConfig()
    sim = Simulation(config)
    
    print(f"====================================================")
    print(f"Initializing Simulation Matrix [{config.world_width}x{config.world_height}]")
    print(f"Master Seed Identity: {config.seed}")
    print(f"Founding Population Size: {config.starting_population} agents.")
    print(f"====================================================\n")

    # 2. Advance time forward through historical blocks
    target_ticks = 500
    print(f"Advancing time matrix forward by {target_ticks} years... Please wait.")
    sim.run(target_ticks)
    
    # 3. Process structural database registries for chronicle logging
    history_data = report(sim.world, sim.agents, sim.settlements, sim.current_tick)
    
    # 4. Print clean observer ledger records 
    print_history_book(history_data)


if __name__ == "__main__":
    main()
