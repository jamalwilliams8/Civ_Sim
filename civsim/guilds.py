"""
civsim/guilds.py
Implements Phase 3 Progressive Taxation, Public Infrastructure Funds,
Trade Apprenticeship progressions, and Illicit Underworld Careers (Smugglers, Thieves).
Supports hybrid cohort/individual population scaling.
"""

import random
from collections import defaultdict

def resolve_wealth_and_guild_factions(world, agents, settlements, current_tick: int) -> None:
    """Processes progressive tax deductions, trade skill progression, and illicit black-market thefts."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    # 1. Map occupational distribution counts by reading both cohorts and individuals
    city_pops = defaultdict(int)
    for agent in agents.raw_living_agents():
        if agent.settlement_id:
            city_pops[agent.settlement_id] += 1
            
    for cohort in agents.cohorts.values():
        if getattr(cohort, "settlement_id", None):
            city_pops[cohort.settlement_id] += cohort.count

    # 2. Process Progressive Tax Deductions and Public Revenue Pools
    for city in active_cities:
        total_pop = city_pops.get(city.id, 0)
        if total_pop <= 0:
            continue
            
        tax_pool = getattr(city, "public_treasury", 0.0)
        food_price = getattr(city, "food_price_index", 1.0)
        
        # Calculate proportional labor division based on macro resolution weights
        num_smiths = max(1, int(total_pop * 0.20))
        num_apprentices = max(1, int(total_pop * 0.15))
        num_smugglers = max(0, int(total_pop * 0.05) if city.crime_rate > 0.04 else 0)
        
        # Simulated transaction velocity generation loop across the population matrix
        earned_wealth = round((total_pop * 0.5) + (num_smiths * 1.2 * food_price), 2)
        
        # --- PROGRESSIVE TAX CODE SYSTEM ---
        tax_rate = 0.12 if earned_wealth > 20.0 else 0.04
        deduction = round(earned_wealth * tax_rate, 2)
        
        tax_pool += deduction
        avg_wealth = round((earned_wealth - deduction) / total_pop, 2)
        
        # --- ILLEGAL SMUGGLING & TREASURY BLACK MARKETS ---
        if num_smugglers > 0:
            steal_amount = min(tax_pool, round(num_smugglers * random.uniform(0.5, 1.5), 2))
            tax_pool = max(0.0, tax_pool - steal_amount)
            # Organic crime feedback loop inflation
            current_crime = getattr(city, "crime_rate", 0.0)
            city.crime_rate = min(0.95, current_crime + 0.01)

        # 3. Spend Public Treasury Funds to Accelerate Infrastructure Building
        current_walls = getattr(city, "fortifications", 0.0)
        if tax_pool > 5.0 and current_walls < 50.0:
            investment = min(tax_pool * 0.5, 5.0)
            tax_pool = round(tax_pool - investment, 2)
            setattr(city, "fortifications", round(current_walls + (investment * 0.2), 2))

        # Enable currency systems at lower urban weights organically
        if total_pop >= 20:
            setattr(city, "economy_type", "MONETARY_TOKEN")
        else:
            setattr(city, "economy_type", "BARTER_SYSTEM")

        setattr(city, "public_treasury", round(tax_pool, 2))
        setattr(city, "avg_net_worth", max(0.1, avg_wealth))
        setattr(city, "guild_craft_size", num_smiths)
        setattr(city, "guild_apprentice_size", num_apprentices)
        setattr(city, "guild_smuggler_size", num_smugglers)
