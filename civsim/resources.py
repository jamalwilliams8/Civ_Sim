"""
Resource production: labor invested by agents working a tile gradually
raises that tile's productive capacity (max_food_wild). Previously
max_food_wild was fixed forever at world-gen, so there was no mechanism
for population to ever increase the food supply that supports it -- this
is the missing "population -> labor -> more production -> supports more
population" loop from the roadmap (section 7 / Priority 1 item 4).
"""

from civsim.agents import AgentRegistry
from civsim.world import World

LABOR_CAPACITY_GAIN_PER_AGENT = 0.02  # max_food_wild increase per worker-tick
LAND_CAPACITY_CEILING = 40.0          # hard cap: cultivation can't grow unbounded


def resolve_resource_production(world: World, agents: AgentRegistry) -> None:
    """Every living agent 'works' the tile it currently occupies. More
    workers on a tile raise its ceiling faster, but each tile is capped
    at LAND_CAPACITY_CEILING regardless of headcount, so this is pressure
    relief, not infinite growth."""
    worker_counts: dict[tuple[int, int], int] = {}
    for agent in agents.living_agents():
        key = (agent.x, agent.y)
        worker_counts[key] = worker_counts.get(key, 0) + 1

    for (x, y), worker_count in worker_counts.items():
        tile = world.get_tile(x, y)
        if tile.max_food_wild >= LAND_CAPACITY_CEILING:
            continue
        gain = worker_count * LABOR_CAPACITY_GAIN_PER_AGENT
        tile.max_food_wild = min(LAND_CAPACITY_CEILING, tile.max_food_wild + gain)