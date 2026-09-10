"""
Population dynamics: Processes individual agents and high-scale cohorts.
Optimized with pure cohort-to-cohort spatial expansion to enable 1000+ tick runs.
"""

from collections import defaultdict
from civsim.agents import (
    Agent, AgentRegistry, DemographicCohort, FOOD_NEED_PER_TICK, 
    HEALTH_GAIN_IF_FED, HEALTH_LOSS_IF_UNFED, MAX_HEALTH, 
    OLD_AGE_ONSET, OLD_AGE_MAX
)
from civsim.world import World

BASE_BIRTH_CHANCE_PER_FERTILE_AGENT = 0.04  
SETTLEMENT_STARVATION_BUFFER = 0.5  
MAX_TILE_COHORT_POPULATION = 150  # Cap on background math mass per tile


def resolve_old_age(agents: AgentRegistry, rng, current_tick: int) -> None:
    """Processes mortality curves across individuals and spatial cohorts."""
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

    for pos, cohort in list(agents.cohorts.items()):
        if cohort.count <= 0:
            continue
        avg_age = cohort.total_age / cohort.count
        if avg_age >= OLD_AGE_ONSET:
            clamped_age = min(avg_age, OLD_AGE_MAX)
            death_ratio = (clamped_age - OLD_AGE_ONSET) / max(1, span)
            deaths = int(cohort.count * death_ratio * 0.25)
            cohort.count = max(0, cohort.count - deaths)


def resolve_food_and_health(world: World, agents: AgentRegistry, current_tick: int) -> None:
    """Divides local tile food resources between individuals and cohorts equitably."""
    living = agents.living_agents()
    
    tile_individuals = defaultdict(list)
    for agent in living:
        tile_individuals[(agent.x, agent.y)].append(agent)

    all_occupied_tiles = set(tile_individuals.keys()) | set(agents.cohorts.keys())

    for (x, y) in all_occupied_tiles:
        tile = world.get_tile(x, y)
        individuals_here = tile_individuals[(x, y)]
        cohort = agents.cohorts.get((x, y))
        
        cohort_count = cohort.count if cohort else 0
        total_consumers = len(individuals_here) + cohort_count
        if total_consumers == 0:
            continue
            
        total_food_needed = total_consumers * FOOD_NEED_PER_TICK
        
        if tile.food_wild >= total_food_needed:
            tile.food_wild -= total_food_needed
            for agent in individuals_here:
                agent.health = min(MAX_HEALTH, agent.health + HEALTH_GAIN_IF_FED)
            if cohort:
                cohort.avg_health = min(MAX_HEALTH, cohort.avg_health + HEALTH_GAIN_IF_FED)
        else:
            available_share = tile.food_wild / total_consumers
            tile.food_wild = 0.0
            fraction_met = available_share / FOOD_NEED_PER_TICK
            
            for agent in individuals_here:
                loss = HEALTH_LOSS_IF_UNFED
                if agent.settlement_id or (cohort and cohort.settlement_id):
                    loss *= SETTLEMENT_STARVATION_BUFFER
                net_impact = (fraction_met * HEALTH_GAIN_IF_FED) - ((1.0 - fraction_met) * loss)
                agent.health = min(MAX_HEALTH, max(0.0, agent.health + net_impact))
                
            if cohort:
                loss = HEALTH_LOSS_IF_UNFED
                if cohort.settlement_id:
                    loss *= SETTLEMENT_STARVATION_BUFFER
                net_impact = (fraction_met * HEALTH_GAIN_IF_FED) - ((1.0 - fraction_met) * loss)
                cohort.avg_health = min(MAX_HEALTH, max(0.0, cohort.avg_health + net_impact))

    for agent in living:
        if agent.health <= 0:
            agent.die(tick=current_tick, cause="starvation")
            
    for pos, cohort in list(agents.cohorts.items()):
        if cohort.avg_health <= 2.0:
            cohort.count = int(cohort.count * 0.5)
        if cohort.count <= 0:
            del agents.cohorts[pos]


def resolve_births(agents: AgentRegistry, rng, current_tick: int) -> list[Agent]:
    """Handles individual reproduction and fast low-res cohort block spillover."""
    new_agents = []
    
    fertile = [a for a in agents.living_agents() if a.is_fertile()]
    for parent in fertile:
        if rng.random() < BASE_BIRTH_CHANCE_PER_FERTILE_AGENT:
            child = agents.create_agent(generation=parent.generation + 1, x=parent.x, y=parent.y)
            new_agents.append(child)

    for pos, cohort in list(agents.cohorts.items()):
        if cohort.count <= 0:
            continue
        estimated_fertile_pop = cohort.count * 0.4
        births = int(estimated_fertile_pop * BASE_BIRTH_CHANCE_PER_FERTILE_AGENT)
        
        if births > 0:
            cohort.count += births
            
            # --- HIGH SCALE COHORT-TO-COHORT OVERFLOW ---
            # If background masses overflow, spawn a matching fast low-res cohort nearby!
            if cohort.count > MAX_TILE_COHORT_POPULATION:
                overflow = cohort.count - MAX_TILE_COHORT_POPULATION
                cohort.count = MAX_TILE_COHORT_POPULATION
                
                # Pick a random neighboring tile coordinate
                sx = min(max(pos[0] + rng.randint(-1, 1), 0), 99)
                sy = min(max(pos[1] + rng.randint(-1, 1), 0), 99)
                target_pos = (sx, sy)
                
                if target_pos not in agents.cohorts:
                    agents.cohorts[target_pos] = DemographicCohort(
                        x=sx, y=sy, 
                        generation=cohort.generation + 1,
                        settlement_id=cohort.settlement_id
                    )
                agents.cohorts[target_pos].count += overflow
                agents.cohorts[target_pos].total_age += overflow * 18  # Starts at average young-adult age

    return new_agents
