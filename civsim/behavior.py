"""
Agent behavior: Optimized LOW-resolution survival movement.
Uses an accelerated lookup grid to ensure high-population throughput.
"""

from collections import defaultdict
from civsim.agents import Agent, AgentRegistry, FOOD_NEED_PER_TICK
from civsim.world import World

SEARCH_RADIUS = 2  # Scaled down slightly to drastically reduce calculation matrices


def _per_capita_food(tile, occupancy: dict, extra: int = 0) -> float:
    occupants = occupancy.get((tile.x, tile.y), 0) + extra
    return tile.food_wild / max(1, occupants)


def resolve_movement(world: World, agents: AgentRegistry) -> None:
    """
    Optimized movement phase. Fast-tracks contented agents to bypass 
    expensive ring-search lookups, keeping computational cost minimal.
    """
    living = agents.living_agents()
    if not living:
        return

    # 1. Pre-calculate spatial occupancy in a single fast pass
    occupancy = defaultdict(int)
    for agent in living:
        occupancy[(agent.x, agent.y)] += 1

    # 2. Process movement decisions
    for agent in living:
        cx, cy = agent.x, agent.y
        current = world.get_tile(cx, cy)
        
        # --- SPEED OPTIMIZATION PROFILING ---
        # If the agent's current fair share is perfectly fine, bypass all search logic entirely!
        if _per_capita_food(current, occupancy) >= FOOD_NEED_PER_TICK:
            continue  

        # 3. Only look outwards if local resources are actively missing
        best_target = None
        best_food = -1.0
        
        # Fast local bounding box check instead of nested coordinate lookups
        min_x = max(0, cx - SEARCH_RADIUS)
        max_x = min(world.width - 1, cx + SEARCH_RADIUS)
        min_y = max(0, cy - SEARCH_RADIUS)
        max_y = min(world.height - 1, cy + SEARCH_RADIUS)
        
        for nx in range(min_x, max_x + 1):
            for ny in range(min_y, max_y + 1):
                if nx == cx and ny == cy:
                    continue
                tile = world.get_tile(nx, ny)
                # Count if we were to arrive there
                food_share = _per_capita_food(tile, occupancy, extra=1)
                
                if food_share >= FOOD_NEED_PER_TICK and food_share > best_food:
                    best_food = food_share
                    best_target = tile

        # 4. Execute physical step toward target coordinate
        if best_target is not None:
            occupancy[(cx, cy)] -= 1
            step_x = (best_target.x > cx) - (best_target.x < cx)
            step_y = (best_target.y > cy) - (best_target.y < cy)
            agent.x += step_x
            agent.y += step_y
            occupancy[(agent.x, agent.y)] += 1
