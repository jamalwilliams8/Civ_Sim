"""
civsim/governance_types.py
Implements Phase 3 Government Typology Transitions and Central Banking Credit Engines.
Settlements transition into Monarchies or Councils, managing treasury loan pools.
"""

import random
from collections import defaultdict

def resolve_politics_and_central_banks(world, agents, settlements, current_tick: int) -> None:
    """Handles political system evolution, tax allocations, and bank credit injections."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    # Map general population load using both cohorts and uncompressed agents
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

        # --- DYNAMIC GOVERNMENT TRANSITIONS ENGINE ---
        current_gov = getattr(city, "government_type", "TRIBAL_CHIEFDOM")
        
        # Balance thresholds to match tribal expansion trends perfectly
        if total_pop >= 15 and current_gov == "TRIBAL_CHIEFDOM":
            city_seed = (city.home_x * city.home_y + current_tick) % 2
            if city_seed == 0:
                setattr(city, "government_type", "COUNCIL_REPUBLIC")
            else:
                setattr(city, "government_type", "HEREDITARY_MONARCHY")
        elif total_pop < 5:
            setattr(city, "government_type", "TRIBAL_CHIEFDOM")

        # --- CENTRAL BANK CREDIT ENGINE & LOAN POOLS ---
        gov_mode = getattr(city, "government_type", "TRIBAL_CHIEFDOM")
        has_central_bank = gov_mode in ["COUNCIL_REPUBLIC", "HEREDITARY_MONARCHY"]
        
        treasury = getattr(city, "public_treasury", 0.0)
        active_loans = getattr(city, "outstanding_loans_count", 0)
        interest_rate = 0.05 if gov_mode == "COUNCIL_REPUBLIC" else 0.12
        
        if has_central_bank and treasury > 15.0:
            setattr(city, "central_bank_status", "ACTIVE_RESERVE")
            
            # Evaluate current cell regional climate states for liquidity crunches
            climate_state = getattr(world, "current_weather", "NORMAL")
            tile = world.get_tile(city.home_x, city.home_y)
            if tile.zone_type == "TUNDRA":
                climate_state = getattr(world, "northern_weather", "NORMAL")

            if climate_state in ["DROUGHT", "FREEZE"]:
                # Central Bank issues emergency credit loans to farmers to suppress starvation loops
                num_loans_to_issue = min(5, int(treasury // 10))
                for _ in range(num_loans_to_issue):
                    loan_value = 8.0
                    treasury -= loan_value
                    active_loans += 1
                    
                    # Intervene in carrying metrics: inject synthetic food items to stabilize tile
                    tile.food_wild += loan_value * 1.5
                    
                # Banking return yield: Interest payments hit the treasury fund on future cycles
                treasury += round(active_loans * (8.0 * interest_rate), 2)
                setattr(city, "last_bank_action", "CREDIT_INJECTION")
            else:
                setattr(city, "last_bank_action", "RESERVES_STABLE")
        else:
            setattr(city, "central_bank_status", "NONE")
            setattr(city, "last_bank_action", "NO_BANK_FOUNDED")

        # Sync calculations back to settlement instances safely
        setattr(city, "public_treasury", round(treasury, 2))
        setattr(city, "outstanding_loans_count", active_loans)
