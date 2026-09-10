"""
civsim/law.py
Implements Phase 3 Social Friction: Density-driven Crime rates 
and Leader-funded City Watch Guard Patrol allocations.
"""

from collections import defaultdict
from civsim.agents import AgentRegistry, Resolution

BASE_CRIME_PER_CITIZEN = 0.005    # Base social friction coefficient per crowded agent
CRIME_CRISIS_THRESHOLD = 0.30    # Crime rate at which leaders divert labor to guard duty
GUARD_EFFICIENCY = 0.80          # Rate at which guard allocations suppress local crime


def resolve_social_friction_and_law(world, agents: AgentRegistry, settlements, current_tick: int) -> None:
    """Calculates density-driven internal crime indexes and processes town guard security loops."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    # 1. Single-pass map of population loads by settlement ID to optimize lookups
    city_populations = defaultdict(int)
    for agent in agents.raw_living_agents():
        if agent.settlement_id:
            city_populations[agent.settlement_id] += 1

    for city in active_cities:
        pop = city_populations.get(city.id, 0)
        if pop <= 0:
            continue

        # 2. Emergent Crime Calculation: Crowding friction creates structural crime pressure
        raw_crime_rate = pop * BASE_CRIME_PER_CITIZEN
        
        # Check if the city has an active leader to coordinate security responses
        has_leader = city.leader_id is not None
        guard_allocation = 0.0
        
        # 3. Guard Patrol Allocation: If crime breaks crisis levels, leaders fund public safety
        if raw_crime_rate > CRIME_CRISIS_THRESHOLD and has_leader:
            # Divert up to 15% of the local population force away from agricultural labor to serve as guards
            guard_allocation = min(0.15, (raw_crime_rate - CRIME_CRISIS_THRESHOLD) * 0.5)
            
        # Final suppressed crime rate accounting for guard patrols
        final_crime_rate = max(0.0, raw_crime_rate - (guard_allocation * GUARD_EFFICIENCY))
        
        # Cache these social variables directly onto the settlement structure for diagnostics
        setattr(city, "crime_rate", round(final_crime_rate, 3))
        setattr(city, "guard_force", round(guard_allocation, 3))

        # 4. The Labor Production Penalty Feedback Loop:
        # If guards are active on a tile, reduce the wild food values slightly to mimic workers leaving fields
        if guard_allocation > 0.0:
            tile = world.get_tile(city.home_x, city.home_y)
            tile.food_wild = max(0.0, tile.food_wild - (guard_allocation * 5.0))
