"""
civsim/religion.py
Implements Phase 3 Religion and Extraordinary Miracle Events.
Unexplained phenomena alter the credibility vectors of political and spiritual leaders.
"""

import random
from collections import defaultdict
from civsim.agents import AgentRegistry, Resolution

MIRACLE_CHANCE_PER_TICK = 0.05


def resolve_miracles_and_belief(world, agents: AgentRegistry, settlements, current_tick: int) -> None:
    """Spawns extraordinary events and evaluates how they alter leader credibility."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities or random.random() > MIRACLE_CHANCE_PER_TICK:
        return

    # 1. Trigger an extraordinary miracle event in a dense city hub
    living = agents.raw_living_agents()
    target_city = random.choice(active_cities)
    tile = world.get_tile(target_city.home_x, target_city.home_y)

    # Inject an unexplained resource surge (A localized miracle)
    tile.food_wild = min(tile.max_food_wild * 2.0, tile.food_wild + 100.0)

    # 2. Locate local figures of authority to process the social outcome
    political_leader = agents.agents.get(target_city.leader_id) if target_city.leader_id else None
    
    # Simulate a potential emergent Prophet candidate inside the city grid square
    city_agents = [a for a in living if a.settlement_id == target_city.id and a.resolution != Resolution.COMPRESSED]
    prophet_candidate = max(city_agents, key=lambda a: a.intelligence) if city_agents else None

    # 3. Dynamic Evaluation: Calculate who wins the credibility tug-of-war
    if prophet_candidate and political_leader:
        prophet_roll = prophet_candidate.intelligence * random.random()
        ruler_roll = political_leader.intelligence * random.random()

        if prophet_roll > ruler_roll:
            # Prophet successfully claims the miracle: Boost Credibility
            prophet_candidate.reputation = min(5.0, prophet_candidate.reputation + 1.5)
            political_leader.reputation = max(0.1, political_leader.reputation - 0.5)
            
            # Log the successful divine validation event node inside our causality graph
            target_city.last_miracle_result = f"PROPHET_CLAIMED_BY_{prophet_candidate.id[:8]}"
        else:
            # Political leader disproves the miracle: Destroy Credibility
            prophet_candidate.reputation = max(0.1, prophet_candidate.reputation - 1.5)
            political_leader.reputation = min(5.0, political_leader.reputation + 0.5)
            target_city.last_miracle_result = f"RULER_EXPOSED_SHAM"
    else:
        target_city.last_miracle_result = "UNEXPLAINED_SURGE"
