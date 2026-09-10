"""
civsim/military.py
Implements Phase 3 Military Defenses and external Raider Incursions.
Wealthy cities attract hostiles, forcing leaders to build defensive wall fortifications.
"""

import random
from collections import defaultdict
from civsim.agents import AgentRegistry

RAIDER_SPAWN_CHANCE = 0.08
BASE_RAIDER_STRENGTH = 15.0


def resolve_military_and_raiders(world, agents: AgentRegistry, settlements, current_tick: int) -> None:
    """Spawns hostile incursions against wealthy cities and processes siege combat evaluations."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities or random.random() > RAIDER_SPAWN_CHANCE:
        return

    # 1. Target the wealthiest city (highest population count acts as proxy for wealth)
    living = agents.raw_living_agents()
    city_pops = defaultdict(int)
    for agent in living:
        if agent.settlement_id:
            city_pops[agent.settlement_id] += 1

    target_city = max(active_cities, key=lambda c: city_pops.get(c.id, 0))
    pop = city_pops.get(target_city.id, 0)
    if pop < 20:
        return  # Ignore tiny, impoverished camps

    # 2. Compute Defense Fortification Levels
    # Blacksmiths and Soldiers on the tile build up a defensive fortification rating over time
    city_agents = [a for a in living if a.settlement_id == target_city.id]
    num_soldiers = sum(1 for a in city_agents if getattr(a, "occupation", "FARMER") == "SOLDIER")
    num_smiths = sum(1 for a in city_agents if getattr(a, "occupation", "FARMER") == "BLACKSMITH")

    current_walls = getattr(target_city, "fortifications", 0.0)
    # Labor builds up permanent physical defensive infrastructure walls
    new_walls = min(50.0, current_walls + (num_smiths * 0.05) + (num_soldiers * 0.02))
    setattr(target_city, "fortifications", round(new_walls, 2))

    # 3. Process the Raider Siege Combat Event
    raider_strength = BASE_RAIDER_STRENGTH + (current_tick * 0.02)
    defense_strength = num_soldiers * 2.0 + new_walls

    if raider_strength > defense_strength:
        # Siege Breach: Raiders plunder food reserves, causing immediate health drops
        tile = world.get_tile(target_city.home_x, target_city.home_y)
        tile.food_wild = max(0.0, tile.food_wild - 30.0)
        
        # Slay a portion of the population forces during the sack of the city
        casualties = min(len(city_agents), random.randint(3, 8))
        for i in range(casualties):
            city_agents[i].die(current_tick, "killed_in_battle")
            
        setattr(target_city, "last_siege_result", "SACKED")
    else:
        # Repelled: Defense holds firm, soldiers gain combat memory attributes
        setattr(target_city, "last_siege_result", "REPELLED")
