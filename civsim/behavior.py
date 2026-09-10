"""
Agent behavior: Integrated Adaptive Resolution Management.
Compresses excess individual agents into spatial math cohorts to prevent CPU lag.
"""

from collections import defaultdict
from civsim.agents import Agent, AgentRegistry, DemographicCohort, FOOD_NEED_PER_TICK
from civsim.world import World

SEARCH_RADIUS = 2  
COHORT_COMPRESSION_THRESHOLD = 30  # Max individual agent instances allowed per single tile


def _per_capita_food(tile, occupancy: dict, extra: int = 0) -> float:
    occupants = occupancy.get((tile.x, tile.y), 0) + extra
    return tile.food_wild / max(1, occupants)


def resolve_movement(world: World, agents: AgentRegistry) -> None:
    """Executes spatial checks and manages individual agent-to-cohort compression triggers."""
    living = agents.living_agents()
    
    # 1. Adaptive Resolution Check: Group individual agents by spatial grid locations
    grid_buckets = defaultdict(list)
    for agent in living:
        grid_buckets[(agent.x, agent.y)].append(agent)

    # 2. Compress heavy nodes into Demographic Cohort blocks
    for pos, agents_on_tile in grid_buckets.items():
        if len(agents_on_tile) >= COHORT_COMPRESSION_THRESHOLD:
            # Pull or initialize target spatial cohort block
            if pos not in agents.cohorts:
                first_agent = agents_on_tile[0]
                agents.cohorts[pos] = DemographicCohort(
                    x=pos[0], 
                    y=pos[1], 
                    generation=first_agent.generation,
                    settlement_id=first_agent.settlement_id
                )
            
            cohort = agents.cohorts[pos]
            for agent in agents_on_tile:
                cohort.count += 1
                cohort.total_age += agent.age
                # Safely transition individual object into tracking state math
                agent.die(0, "compressed")  

    # Refresh tracking reference maps
    living = agents.living_agents()

    occupancy = defaultdict(int)
    for pos, cohort in agents.cohorts.items():
        occupancy[pos] += cohort.count
    for agent in living:
        occupancy[(agent.x, agent.y)] += 1

    # 3. Individual Movement Loop execution
    for agent in living:
        cx, cy = agent.x, agent.y
        current = world.get_tile(cx, cy)
        
        if _per_capita_food(current, occupancy) >= FOOD_NEED_PER_TICK:
            continue  

        best_target = None
        best_food = -1.0
        
        min_x = max(0, cx - SEARCH_RADIUS)
        max_x = min(world.width - 1, cx + SEARCH_RADIUS)
        min_y = max(0, cy - SEARCH_RADIUS)
        max_y = min(world.height - 1, cy + SEARCH_RADIUS)
        
        for nx in range(min_x, max_x + 1):
            for ny in range(min_y, max_y + 1):
                if nx == cx and ny == cy:
                    continue
                tile = world.get_tile(nx, ny)
                food_share = _per_capita_food(tile, occupancy, extra=1)
                
                if food_share >= FOOD_NEED_PER_TICK and food_share > best_food:
                    best_food = food_share
                    best_target = tile

        if best_target is not None:
            occupancy[(cx, cy)] -= 1
            step_x = (best_target.x > cx) - (best_target.x < cx)
            step_y = (best_target.y > cy) - (best_target.y < cy)
            agent.x += step_x
            agent.y += step_y
            occupancy[(agent.x, agent.y)] += 1
