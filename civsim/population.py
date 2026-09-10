"""
Population dynamics: food consumption, health changes, deaths, and births.
Separate from Agent identity (agents.py) — this module decides *whether*
someone lives, dies, or is born; agents.py just defines what an agent *is*.
"""

from civsim.agents import (
    Agent, AgentRegistry, FOOD_NEED_PER_TICK, HEALTH_GAIN_IF_FED,
    HEALTH_LOSS_IF_UNFED, MAX_HEALTH, OLD_AGE_ONSET, OLD_AGE_MAX,
)
from civsim.world import World

BASE_BIRTH_CHANCE_PER_FERTILE_AGENT = 0.05  # per tick, before food-surplus modifier
SETTLEMENT_STARVATION_BUFFER = 0.5  # settlement members lose less health when unfed (food coordination)


def resolve_old_age(agents: AgentRegistry, rng, current_tick: int) -> None:
    """Without this, no agent ever dies of old age: everyone eventually
    ages past MAX_BREEDING_AGE and the population permanently loses its
    ability to reproduce even with unlimited food (confirmed by inspecting
    a 500-tick run: 33 living agents, 0 fertile, oldest age 500). Death
    probability rises linearly from 0 at OLD_AGE_ONSET to a certainty at
    OLD_AGE_MAX, so generations turn over instead of accumulating forever."""
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


def resolve_food_and_health(world: World, agents: AgentRegistry, current_tick: int) -> None:
    """Each living agent tries to eat from the tile it's standing on."""
    for agent in agents.living_agents():
        tile = world.get_tile(agent.x, agent.y)
        if tile.food_wild >= FOOD_NEED_PER_TICK:
            tile.food_wild -= FOOD_NEED_PER_TICK
            agent.health = min(MAX_HEALTH, agent.health + HEALTH_GAIN_IF_FED)
        else:
            loss = HEALTH_LOSS_IF_UNFED
            if agent.settlement_id is not None:
                loss *= SETTLEMENT_STARVATION_BUFFER
            agent.health -= loss

        if agent.health <= 0:
            agent.die(tick=current_tick, cause="starvation")


def resolve_births(agents: AgentRegistry, rng, current_tick: int) -> list[Agent]:
    """Each fertile living agent has an independent chance of producing a new agent."""
    new_agents = []
    fertile = [a for a in agents.living_agents() if a.is_fertile()]
    for parent in fertile:
        if rng.random() < BASE_BIRTH_CHANCE_PER_FERTILE_AGENT:
            child = agents.create_agent(
                generation=parent.generation + 1,
                x=parent.x,
                y=parent.y,
            )
            new_agents.append(child)
    return new_agents