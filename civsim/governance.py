"""
civsim/governance.py
Implements tribal leadership actions: commands overpopulated urban centers 
to execute pioneer splits with O(1) index caching to eliminate CPU hang.
"""

import random
from civsim.agents import AgentRegistry, Resolution
from civsim.settlements import SettlementRegistry

CRISIS_POPULATION_THRESHOLD = 150  
SPLIT_RATIO = 0.40                


def resolve_governance_decisions(world, agents: AgentRegistry, settlements: SettlementRegistry, current_tick: int) -> None:
    """Leaders audit local tile loads and execute political migration orders using optimized dictionaries."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    # 1. OPTIMIZATION: Map cohort loads by settlement ID in a single pass instead of nested loops
    cohort_settlement_totals = {}
    for cohort in agents.cohorts.values():
        if cohort.settlement_id:
            cohort_settlement_totals[cohort.settlement_id] = cohort_settlement_totals.get(cohort.settlement_id, 0) + cohort.count

    # 2. Map individual uncompressed agents by settlement ID in a single pass
    indiv_settlement_totals = {}
    for agent in agents.living_agents():
        if agent.settlement_id:
            indiv_settlement_totals[agent.settlement_id] = indiv_settlement_totals.get(agent.settlement_id, 0) + 1

    colonies_founded_this_tick = 0

    for city in active_cities:
        if colonies_founded_this_tick >= 3:
            break

        total_load = indiv_settlement_totals.get(city.id, 0) + cohort_settlement_totals.get(city.id, 0)

        if total_load >= CRISIS_POPULATION_THRESHOLD:
            search_dist = random.randint(4, 8)
            target_x = min(world.width - 1, max(0, city.home_x + random.choice([-search_dist, search_dist])))
            target_y = min(world.height - 1, max(0, city.home_y + random.choice([-search_dist, search_dist])))
            
            new_colony = settlements.found_settlement(target_x, target_y, current_tick)
            colonies_founded_this_tick += 1
            
            target_migrants = int(total_load * SPLIT_RATIO)
            migrants_moved = 0
            
            # Migrate active uncompressed individuals first
            for agent in agents.living_agents():
                if agent.settlement_id == city.id and migrants_moved < target_migrants:
                    agent.settlement_id = new_colony.id
                    agent.x = target_x
                    agent.y = target_y
                    agent.resolution = Resolution.COMPRESSED
                    migrants_moved += 1

            old_pos = (city.home_x, city.home_y)
            new_pos = (target_x, target_y)
            
            if old_pos in agents.cohorts and agents.cohorts[old_pos].count > (target_migrants - migrants_moved):
                half_share = int((target_migrants - migrants_moved) * 0.5)
                if half_share > 0:
                    agents.cohorts[old_pos].count -= half_share
                    if new_pos not in agents.cohorts:
                        agents.cohorts[new_pos] = DemographicCohort(x=target_x, y=target_y, generation=agents.cohorts[old_pos].generation, settlement_id=new_colony.id)
                        agents.cohorts[new_pos].count = half_share
                    else:
                        agents.cohorts[new_pos].count += half_share
