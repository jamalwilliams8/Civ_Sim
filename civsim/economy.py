"""
civsim/economy.py
Implements Phase 3 Emergent Market Economics, Supply Chains, Dynamic Prices,
and Currency Token Monetary Inflation feedback loops.
Armored with safe attribute fallbacks to prevent initialization crashes.
"""

import random
from collections import defaultdict

def resolve_market_economics(world, agents, settlements, current_tick: int) -> None:
    """Processes settlement market centers, matching labor supplies to dynamic price indexes."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    city_pops = defaultdict(int)
    for agent in agents.raw_living_agents():
        if agent.settlement_id:
            city_pops[agent.settlement_id] += 1
            
    for cohort in agents.cohorts.values():
        if getattr(cohort, "settlement_id", None):
            city_pops[cohort.settlement_id] += cohort.count

    for city in active_cities:
        total_pop = city_pops.get(city.id, 0)
        if total_pop <= 0:
            continue

        num_farmers = max(1, int(total_pop * 0.50))
        num_smiths = max(1, int(total_pop * 0.20))
        crime_rate = getattr(city, "crime_rate", 0.0)
        
        # Supply & Demand Pricing Index Rules
        or_ratio = num_farmers / total_pop
        base_food_price = 1.0 + max(0.0, (0.50 - or_ratio) * 4.0)
        
        tile = world.get_tile(city.home_x, city.home_y)
        climate_state = getattr(world, "current_weather", "NORMAL")
        if tile.zone_type == "TUNDRA":
            climate_state = getattr(world, "northern_weather", "NORMAL")
            
        if climate_state in ["DROUGHT", "FREEZE"]:
            base_food_price *= 2.0  

        # Currency Token Minting & Inflation Loops
        has_currency = total_pop >= 20
        inflation_multiplier = 1.0
        
        if has_currency:
            if base_food_price > 2.0:
                inflation_multiplier = 1.2 + (num_smiths * 0.05)
                base_food_price *= inflation_multiplier
                crime_rate = min(0.95, crime_rate + 0.08)

        setattr(city, "crime_rate", crime_rate)
        setattr(city, "food_price_index", round(base_food_price, 2))
        setattr(city, "inflation_rate", round((inflation_multiplier - 1.0) * 100, 1))
