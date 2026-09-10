"""
Diagnostics: aggregate metrics about a completed run, so bottlenecks are
identified rather than guessed at. Kept separate from population.py — that
module decides who lives/dies each tick; this module summarizes what happened.
"""

from civsim.agents import AgentRegistry
from civsim.world import World


def report(world: World, agents: AgentRegistry, ticks_run: int) -> dict:
    all_agents = list(agents.agents.values())
    living = [a for a in all_agents if a.alive]
    dead = [a for a in all_agents if not a.alive]

    death_causes: dict[str, int] = {}
    for d in dead:
        death_causes[d.death_cause] = death_causes.get(d.death_cause, 0) + 1

    avg_health = sum(a.health for a in living) / len(living) if living else 0.0

    tiles = list(world.tiles.values())
    avg_food = sum(t.food_wild for t in tiles) / len(tiles)
    starved_tiles = sum(1 for t in tiles if t.food_wild < 1.0)

    return {
        "ticks_run": ticks_run,
        "living": len(living),
        "dead": len(dead),
        "death_causes": death_causes,
        "avg_health_living": round(avg_health, 2),
        "avg_tile_food": round(avg_food, 2),
        "tiles_below_1_food": starved_tiles,
        "total_tiles": len(tiles),
    }