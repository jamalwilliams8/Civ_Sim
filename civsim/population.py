"""
civsim/population.py
Manages demographic equations, lifecycle increments, and macro-demographic cohort birth rates.
"""

import random
from collections import defaultdict
from civsim.agents import (
    Agent, 
    FOOD_NEED_PER_TICK, 
    STARTING_HEALTH, 
    MAX_HEALTH, 
    HEALTH_GAIN_IF_FED, 
    HEALTH_LOSS_IF_UNFED,
    MIN_BREEDING_AGE,
    MAX_BREEDING_AGE,
    Resolution
)

BASE_BIRTH_CHANCE_PER_FERTILE_AGENT = 0.12  # Optimal statistical lineage growth factor
SETTLEMENT_STARVATION_BUFFER = 0.5


def resolve_food_and_health(world, agents) -> None:
    """Calculates food split metrics across individual active tiles."""
    living = agents.raw_living_agents()
    if not living:
        return

    occupancy = defaultdict(int)
    for c_pos, cohort in agents.cohorts.items():
        occupancy[c_pos] += cohort.count
    for agent in agents.living_agents():
        occupancy[(agent.x, agent.y)] += 1

    for agent in living:
        pos = (agent.x, agent.y)
        tile = world.get_tile(agent.x, agent.y)
        
        local_density = max(1, occupancy[pos])
        food_share = tile.food_wild / local_density

        if food_share >= FOOD_NEED_PER_TICK:
            agent.health = min(MAX_HEALTH, agent.health + HEALTH_GAIN_IF_FED)
        else:
            loss = HEALTH_LOSS_IF_UNFED
            if getattr(agent, "settlement_id", None) is not None:
                loss *= SETTLEMENT_STARVATION_BUFFER
            agent.health -= loss

        agent.age += 1


def resolve_birth_and_death(agents, current_tick: int) -> None:
    """Applies age risk limits and calculates macro-demographic cohort birth rates."""
    living = agents.raw_living_agents()
    if not living:
        return

    # 1. Mortality Process Loop
    for agent in living:
        if agent.health <= 0:
            agent.die(current_tick, "starvation")
            pos = (agent.x, agent.y)
            if agent.resolution == Resolution.COMPRESSED and pos in agents.cohorts:
                agents.cohorts[pos].count -= 1
            continue
        
        if agent.age > 50:
            age_risk = (agent.age - 50) * 0.03
            if random.random() < age_risk:
                agent.die(current_tick, "old_age")
                pos = (agent.x, agent.y)
                if agent.resolution == Resolution.COMPRESSED and pos in agents.cohorts:
                    agents.cohorts[pos].count -= 1

    # Clean out empty cohort registry positions
    for pos in list(agents.cohorts.keys()):
        if agents.cohorts[pos].count <= 0:
            del agents.cohorts[pos]

    # 2. Adaptive Resolution Un-compression Layer
    for pos, cohort in list(agents.cohorts.items()):
        if cohort.count < 3:
            for agent in agents.agents.values():
                if agent.alive and agent.resolution == Resolution.COMPRESSED and (agent.x, agent.y) == pos:
                    agent.resolution = Resolution.LOW
            del agents.cohorts[pos]

    # 3. Individual Birth Evaluation Loop (For Uncompressed Agents)
    active_fertile = [a for a in agents.raw_living_agents() if a.is_fertile()]
    for mother in active_fertile:
        if random.random() < BASE_BIRTH_CHANCE_PER_FERTILE_AGENT:
            child_generation = mother.generation + 1
            child_id = f"AGT-{child_generation}-{random.randint(100000, 999999)}"
            
            newborn = Agent(
                id=child_id,
                generation=child_generation,
                x=int(mother.x),
                y=int(mother.y),
                sex=random.choice(["M", "F"]),
                age=0,
                alive=True,
                health=STARTING_HEALTH,
                resolution=Resolution.LOW,
                settlement_id=mother.settlement_id
            )
            agents.add_agent(newborn)

    # 4. Macro Cohort Birth Evaluation Loop (For Compressed Agents)
    for pos, cohort in agents.cohorts.items():
        estimated_fertile_females = max(1, int(cohort.count * 0.25))
        for _ in range(estimated_fertile_females):
            if random.random() < BASE_BIRTH_CHANCE_PER_FERTILE_AGENT:
                cohort.count += 1
                child_generation = cohort.generation + 1
                child_id = f"AGT-{child_generation}-{random.randint(100000, 999999)}"
                
                # FIX: Unpack the tuple coordinate key explicitly into distinct integers
                passive_baby = Agent(
                    id=child_id,
                    generation=child_generation,
                    x=int(pos[0]),
                    y=int(pos[1]),
                    sex=random.choice(["M", "F"]),
                    age=0,
                    alive=True,
                    health=STARTING_HEALTH,
                    resolution=Resolution.COMPRESSED,
                    settlement_id=cohort.settlement_id
                )
                agents.add_agent(passive_baby)
