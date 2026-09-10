from civsim.config import SimConfig
from civsim.simulation import Simulation
from civsim.diagnostics import report


def main():
    config = SimConfig()
    sim = Simulation(config)

    print(f"Tick 0: {len(sim.agents.living_agents())} living agents")
    sim.run(50)

    diag = report(sim.world, sim.agents, sim.current_tick)
    for key, value in diag.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()