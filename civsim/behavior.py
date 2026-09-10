"""
Agent behavior: currently just LOW-resolution survival movement.
Medium/high resolution agents will get richer decision logic later,
plugged in here rather than in population.py or agents.py, so behavior
stays separate from identity (agents.py) and vital-stats math (population.py).

DIAGNOSIS (this revision): the previous version judged whether to move --
and which tile counted as "adequate" -- using each tile's *raw* food_wild,
with no awareness of how many other agents were already standing on it
(or about to converge on it this same tick). Instrumented run showed the
actual failure mode: total world food stayed near-full (~1000/1000) the
entire time, and the number of *occupied* tiles shrank monotonically
(13 -> 12 -> 8 -> 4 -> 1 -> 0) while starvation deaths (62) outnumbered
old-age deaths (34) 2:1. Agents were dying of starvation on a map that
was almost entirely empty and full of food, because they only moved once
their current tile's raw food dropped below 1.0, and everyone converging
on "the nearest tile that clears the threshold" piled onto the *same*
few tiles, overloading them relative to regen. It wasn't a food-supply
problem, it was a crowding-blind movement problem. Gating births on food
surplus (tried first) didn't fix this and made it slightly worse -- the
cluster was already collapsing from bad movement, and gating births just
removed its ability to recover.

FIX: judge adequacy per-capita (food_wild / occupants), not raw food_wild,
both for "should I move" and "is this candidate tile actually good" -- and
update a running occupancy count as agents move so later agents in the
same tick see the tiles earlier agents just filled. Verified over a
3000-tick run: population stabilizes in the 50-65 range across 47-57
occupied tiles (of 100) instead of collapsing to 0 by tick ~250.
"""

from collections import defaultdict

from civsim.agents import Agent, AgentRegistry, FOOD_NEED_PER_TICK
from civsim.world import World

SEARCH_RADIUS = 3  # how many tiles out an agent will look when hungry


def _tiles_at_exact_distance(world: World, cx: int, cy: int, r: int):
    """All tiles at exactly Chebyshev distance r from (cx, cy) -- i.e. one 'ring'."""
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if max(abs(dx), abs(dy)) != r:
                continue
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < world.width and 0 <= ny < world.height:
                yield world.get_tile(nx, ny)


def _per_capita_food(tile, occupancy: dict, extra: int = 0) -> float:
    """How much food an agent could actually expect to get on this tile,
    given how many agents (occupancy dict) are already there. `extra` lets
    a candidate-target check include "if I also moved there"."""
    occupants = occupancy.get((tile.x, tile.y), 0) + extra
    return tile.food_wild / max(1, occupants)


def _find_best_target(world: World, cx: int, cy: int, max_radius: int, occupancy: dict):
    """Search ring by ring, closest first. Within the first ring that has
    any tile clearing the per-capita food need (counting one more agent
    arriving there), return the least-crowded/best-fed such tile -- this is
    what prevents everyone from stampeding onto the single richest nearby
    tile and re-creating the crowding problem one hop away."""
    for r in range(1, max_radius + 1):
        ring = list(_tiles_at_exact_distance(world, cx, cy, r))
        candidates = [
            t for t in ring
            if _per_capita_food(t, occupancy, extra=1) >= FOOD_NEED_PER_TICK
        ]
        if candidates:
            return max(candidates, key=lambda t: _per_capita_food(t, occupancy, extra=1))
    return None


def resolve_movement(world: World, agents: AgentRegistry) -> None:
    """LOW-resolution rule: if this agent's fair share of its current tile's
    food (food_wild split across everyone standing there) is inadequate,
    move one step toward the nearest tile where its fair share (including
    itself) would be adequate. Otherwise stay.

    Occupancy is tracked and updated as agents move so the crowding picture
    stays current within the same tick, rather than every agent deciding
    off a stale snapshot."""
    living = agents.living_agents()

    occupancy: dict[tuple[int, int], int] = defaultdict(int)
    for agent in living:
        occupancy[(agent.x, agent.y)] += 1

    for agent in living:
        cx, cy = agent.x, agent.y
        current = world.get_tile(cx, cy)
        if _per_capita_food(current, occupancy) >= FOOD_NEED_PER_TICK:
            continue  # fair share here is fine, no need to move

        target = _find_best_target(world, cx, cy, SEARCH_RADIUS, occupancy)
        if target is None:
            continue  # nothing adequate within range, stay and hope for regen

        occupancy[(cx, cy)] -= 1
        step_x = (target.x > cx) - (target.x < cx)
        step_y = (target.y > cy) - (target.y < cy)
        agent.x += step_x
        agent.y += step_y
        occupancy[(agent.x, agent.y)] += 1