"""
Population dynamics: food consumption, health changes, deaths, and births.
Separate from Agent identity (agents.py) — this module decides *whether*
someone lives, dies, or is born; agents.py just defines what an agent *is*.

FIX (Per-Capita Equity): Instead of evaluating agents sequentially (which causes
the first agents in a dictionary to eat everything and leaves later agents to starve
randomly), this revision groups agents by tile. Food is divided evenly among all 
occupants on a tile. Scarcity causes collective stress/weakness instead of 
lottery-based execution, preserving systemic determinism and explainability.
"""

from collections import defaultdict
from civsim.agents import (
    Agent, AgentRegistry, FOOD_NEED_PER_TICK, HEALTH_GAIN_IF_FED,
    HEALTH_LOSS_IF_UNFED, MAX_HEALTH, OLD_AGE_ONSET, OLD_AGE_MAX,
)
from civsim.world import World

BASE_BIRTH_CHANCE_PER_FERTILE_AGENT = 0.05  # per tick, before food-surplus modifier
SETTLEMENT_STARVATION_BUFFER = 0.5  # settlement members lose less health when unfed (food coordination)


def resolve_old_age(agents: AgentRegistry, rng, current_tick: int) -> None:
    """Without this, no agent ever dies of old age: everyone eventually
    ages past MAX_BREEDING_AGE and the population permanently loses its
    ability to reproduce even with unlimited food. Death probability rises 
    linearly from 0 at OLD_AGE_ONSET to a certainty at OLD_AGE_MAX, so 
    generations turn over instead of accumulating forever."""
    span = OLD_AGE_MAX - OLD_AGE_ONSET
    for agent in agents.living_agents():
        if agent.age < OLD_AGE_ONSET:
            continue
        if agent.age >= OLD_AGE_MAX:
            agent.die(tick=current_tick, cause="old_age")
            continue
        chance = (agent.age - OLD_AGE_ONSET) / span
        if rng.random() < chance:
            agent.die(tick=current_tick, cause="old_age")


def resolve_food_and_health(world: World, agents: AgentRegistry, current_tick: int) -> None:
    """
    Each occupied tile divides its available food equitably among all agents 
    currently standing on it. Net health impacts are scaled to the fraction
    of sustenance received.
    """
    living = agents.living_agents()
    
    # 1. Map tile coordinates to the specific agents standing on them
    tile_occupants = defaultdict(list)
    for agent in living:
        tile_occupants[(agent.x, agent.y)].append(agent)

    # 2. Process resource allocation collectively per tile
    for (x, y), agents_on_tile in tile_occupants.items():
        tile = world.get_tile(x, y)
        total_agents = len(agents_on_tile)
        total_food_needed = total_agents * FOOD_NEED_PER_TICK
        
        if tile.food_wild >= total_food_needed:
            # Case A: Abundance. Everyone eats their full share.
            tile.food_wild -= total_food_needed
            for agent in agents_on_tile:
                agent.health = min(MAX_HEALTH, agent.health + HEALTH_GAIN_IF_FED)
        else:
            # Case B: Scarcity. Divide remaining food entirely equitably.
            available_share = tile.food_wild / total_agents
            tile.food_wild = 0.0  # Tile is entirely stripped of wild food
            
            for agent in agents_on_tile:
                # Calculate what % of their basic diet requirement was satisfied
                fraction_met = available_share / FOOD_NEED_PER_TICK
                
                # Determine baseline starvation penalty based on settlement membership
                loss_magnitude = HEALTH_LOSS_IF_UNFED
                if agent.settlement_id is not None:
                    loss_magnitude *= SETTLEMENT_STARVATION_BUFFER
                
                # Blended impact: Scale health changes linearly by resource ingestion
                net_impact = (fraction_met * HEALTH_GAIN_IF_FED) - ((1.0 - fraction_met) * loss_magnitude)
                agent.health = min(MAX_HEALTH, max(0.0, agent.health + net_impact))

    # 3. Mortality phase: Starve any agents whose health reached zero this tick
    for agent in living:
        if agent.health <= 0:
            agent.die(tick=current_tick, cause="starvation")


def resolve_births(agents: AgentRegistry, rng, current_tick: int) -> list[Agent]:
    """Each fertile living agent has an independent chance of producing a new agent."""
    new_agents = []
    fertile = [a for a in agents.living_agents() if a.is_fertile()]
    for parent in fertile:
        if rng.random() < BASE_BIRTH_CHANCE_PER_FERTILE_AGENT:
            child = agents.create_agent(
                generation=parent.generation + 1,
                x=parent.x,
                y=parent.y,
            )
            new_agents.append(child)
    return new_agents
