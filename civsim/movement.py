"""
civsim/movement.py
Handles dynamic agent vector step routing, guiding individual entities and compressed cohorts.
"""
import random
from civsim.agents import Agent, AgentRegistry, DemographicCohort, Resolution

def resolve_movement(world, agents, tech_registry) -> None:
    """Moves agents tile-by-tile across coordinates based on resource maps."""
    living = agents.raw_living_agents()
    for agent in living:
        # Generate basic random walk steps across coordinates cell bounds
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        
        agent.x = max(0, min(world.width - 1, agent.x + dx))
        agent.y = max(0, min(world.height - 1, agent.y + dy))
        
        # If an agent steps onto a city tile, assign them to it organically
        if agent.settlement_id:
            city = world.tiles.get((agent.x, agent.y))
