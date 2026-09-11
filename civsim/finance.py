"""
civsim/finance.py
Part 2 of the split Guilds system. Processes progressive taxation, hospitality,
civic comfort upgrades, palace decrees, and object mapping variables.
Armored with a safe floor block to prevent negative population starvation crashes.
"""
import random
from collections import defaultdict

def resolve_city_finance(world, agents, settlements, hunting_yields, city_pops) -> None:
    active_cities = [s for s in settlements.settlements.values() if s.active]
    living = agents.raw_living_agents()
    
    for city in active_cities:
        total_pop = city_pops.get(city.id, 0)
        if total_pop <= 0: continue
        
        tax_pool = getattr(city, "public_treasury", 0.0)
        food_price = getattr(city, "food_price_index", 1.0)
        crime_rate = getattr(city, "crime_rate", 0.0)
        
        num_smiths = sum(1 for a in living if a.settlement_id == city.id and a.occupation == 'BLACKSMITH')
        num_smugglers = max(0, int(total_pop * 0.04) if crime_rate > 0.05 else 0)
        num_archivists = sum(1 for a in living if a.settlement_id == city.id and a.occupation == 'ARCHIVIST')
        num_municipal = sum(1 for a in living if a.settlement_id == city.id and a.occupation == 'MUNICIPAL_STAFF')
        num_brewers = sum(1 for a in living if a.settlement_id == city.id and a.occupation == 'BREWER')
        num_cooks = sum(1 for a in living if a.settlement_id == city.id and a.occupation == 'COOK')
        num_apprentices = sum(1 for a in living if a.settlement_id == city.id and a.occupation == 'APPRENTICE')

        # Master Specialty and Service Revenue Distributions
        master_dividend = round(num_smiths * 3.5 * food_price, 2)
        if tax_pool > master_dividend and num_smiths > 0:
            tax_pool = round(tax_pool - master_dividend, 2)
            for a in living:
                if a.settlement_id == city.id and a.occupation == 'BLACKSMITH':
                    a.wealth = round(getattr(a, 'wealth', 0.0) + (master_dividend / num_smiths), 2)

        hospitality_yield = round((num_cooks * 2.2 + num_brewers * 2.5) * food_price, 2)
        for a in living:
            if a.settlement_id == city.id and a.occupation in ['COOK', 'BREWER']:
                a.wealth = round(getattr(a, 'wealth', 0.0) + (hospitality_yield / (max(1, num_cooks + num_brewers))), 2)

        govt_payroll = (num_municipal * 0.25) + (num_archivists * 0.50)
        if tax_pool >= govt_payroll:
            tax_pool = round(tax_pool - govt_payroll, 2)
            for a in living:
                if a.settlement_id == city.id and a.occupation in ['MUNICIPAL_STAFF', 'ARCHIVIST']:
                    a.wealth = round(getattr(a, 'wealth', 0.0) + 0.35, 2)

        # FIX: Force an absolute max() floor limit so unassigned or wilderness metrics 
        # can never drop your economy or food supply into game-breaking negative values.
        total_hunting = hunting_yields.get(city.id, 0.0)
        unassigned_workers = max(0, total_pop - num_smiths - num_apprentices - num_cooks - num_brewers)
        base_foraging = round(unassigned_workers * 1.65, 2)
        
        earned_wealth = max(1.0, round(base_foraging + total_hunting + master_dividend + hospitality_yield, 2))
        
        tax_rate = 0.10 if earned_wealth > 20.0 else 0.03
        deduction = round(earned_wealth * tax_rate, 2)
        tax_pool += deduction
        avg_wealth = round((earned_wealth - deduction) / total_pop, 2)
        
        # Sinks, Donations and Upgrades
        if avg_wealth > 8.0 and tax_pool < 20.0:
            donation = round(total_pop * random.uniform(0.3, 1.2), 2)
            avg_wealth = max(0.1, round(avg_wealth - (donation / total_pop), 2))
            tax_pool += donation
            
        if avg_wealth > 2.0:
            tavern_spend = round(total_pop * 0.08, 2)
            tax_pool += round(tavern_spend * 0.10, 2)
            avg_wealth = max(0.2, round(avg_wealth - (tavern_spend * 0.10) / total_pop, 2))
            crime_rate = max(0.01, crime_rate - 0.04)

        if num_smugglers > 0:
            steal = min(tax_pool, round(num_smugglers * random.uniform(0.2, 0.8), 2))
            tax_pool = max(0.0, tax_pool - steal)
            crime_rate = min(0.95, crime_rate + 0.01)

        # Infrastructure Decrees
        current_walls = getattr(city, 'fortifications', 0.0)
        castle_progress = getattr(city, 'royal_castle_tier', 0.0)
        comfort_level = getattr(city, 'civic_comfort_score', 0.0)
        gov_mode = getattr(city, 'government_type', 'TRIBAL_CHIEFDOM')
        
        if tax_pool > 150.0 and gov_mode in ['HEREDITARY_MONARCHY', 'COUNCIL_REPUBLIC']:
            castle_payroll = 50.0; tax_pool -= castle_payroll
            avg_wealth = round(avg_wealth + (castle_payroll / total_pop), 2)
            castle_progress = round(castle_progress + 1.0, 1)
            current_walls = round(current_walls + 40.0, 2)

        if tax_pool > 10.0 and castle_progress == 0.0:
            if current_walls < 150.0 and num_smiths > 0:
                inv = min(tax_pool * 0.4, 5.0); tax_pool = round(tax_pool - inv, 2)
                current_walls = round(current_walls + (inv * 0.35), 2)
            if tax_pool > 5.0:
                c_inv = min(tax_pool * 0.3, 3.0); tax_pool = round(tax_pool - c_inv, 2)
                comfort_level = round(comfort_level + (c_inv * 0.20), 2)

        # Set Object Configurations Safely
        if castle_progress >= 3.0: setattr(city, 'comfort_tier', 'CITADEL_FORTRESS_AND_PALACE')
        elif castle_progress >= 1.0: setattr(city, 'comfort_tier', 'STONE_KEEP_AND_PALACE_GROUNDS')
        elif comfort_level >= 15.0: setattr(city, 'comfort_tier', 'GRAND_INFIRMARY_AND_AQUEDUCTS')
        elif comfort_level >= 5.0: setattr(city, 'comfort_tier', 'PAVED_STONE_WELLS_AND_TAVERNS')
        else: setattr(city, 'comfort_tier', 'PRIMITIVE_CESSPOOLS')

        setattr(city, 'economy_type', 'MONETARY_TOKEN' if total_pop >= 10 else 'BARTER_SYSTEM')
        setattr(city, 'staff_archivists_count', num_archivists)
        setattr(city, 'staff_service_count', num_tavern_staff + num_municipal + num_brewers + num_cooks)
        setattr(city, 'crime_rate', crime_rate)
        setattr(city, 'fortifications', current_walls)
        setattr(city, 'royal_castle_tier', castle_progress)
        setattr(city, 'civic_comfort_score', comfort_level)
        setattr(city, 'public_treasury', round(tax_pool, 2))
        setattr(city, 'avg_net_worth', max(0.1, avg_wealth))
        setattr(city, 'guild_craft_size', num_smiths)
        setattr(city, 'guild_apprentice_size', num_apprentices)
        setattr(city, 'guild_smuggler_size', num_smugglers)
