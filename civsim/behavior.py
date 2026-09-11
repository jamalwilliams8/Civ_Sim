"""
Agent behavior: Integrated Adaptive Resolution Management.
Optimized via single-pass coordinate bucket maps with an aggressive compression threshold
to guarantee 1,000+ tick execution without individual agent loop choking.
"""

from collections import defaultdict
from civsim.agents import Agent, AgentRegistry, DemographicCohort, FOOD_NEED_PER_TICK
from civsim.world import World

SEARCH_RADIUS = 2  
COHORT_COMPRESSION_THRESHOLD = 5  # Lowered to force aggressive background math scaling


def _per_capita_food(tile, occupancy: dict, extra: int = 0) -> float:
    occupants = occupancy.get((tile.x, tile.y), 0) + extra
    return tile.food_wild / max(1, occupants)


def resolve_movement(world: World, agents: AgentRegistry) -> None:
    """Executes pathfinding steps utilizing a high-speed pre-computed spatial map."""
    living = agents.living_agents()
    if not living:
        return
    
    # 1. SPATIAL INDEXING: Group individual agents by coordinate buckets in one pass
    grid_buckets = defaultdict(list)
    for agent in living:
        grid_buckets[(agent.x, agent.y)].append(agent)

    # 2. REALISTIC COHORT COMPRESSION
    for pos, agents_on_tile in grid_buckets.items():
        if len(agents_on_tile) >= COHORT_COMPRESSION_THRESHOLD:
            if pos not in agents.cohorts:
                # Safe array extraction: fetch the first individual agent inside the list
                lead_agent = agents_on_tile[0]
                
                s_id = getattr(lead_agent, "settlement_id", None)
                gen = getattr(lead_agent, "generation", 0)
                
                # Unpack the tuple positions cleanly into structural x and y integers
                agents.cohorts[pos] = DemographicCohort(
                    x=pos[0], 
                    y=pos[1], 
                    generation=gen,
                    settlement_id=s_id
                )
            
            cohort = agents.cohorts[pos]
            for agent in agents_on_tile:
                cohort.count += 1
                cohort.total_age += agent.age
                agent.die(0, "compressed")  

    # Refresh array tracking references
    living = agents.living_agents()

    # 3. UNIFIED OCCUPANCY REFERENCE MAP
    occupancy = defaultdict(int)
    for pos, cohort in agents.cohorts.items():
        occupancy[pos] += cohort.count
    for agent in living:
        occupancy[(agent.x, agent.y)] += 1

    # 4. PRE-COMPUTE REGIONAL MOVE TARGETS
    tile_vector_cache = {}

    # 5. HIGH-SPEED NAVIGATION LOOP
    for agent in living:
        cx, cy = agent.x, agent.y
        origin_pos = (cx, cy)
        current_tile = world.get_tile(cx, cy)
        
        local_occupants = occupancy.get(origin_pos, 1)
        if (current_tile.food_wild / max(1, local_occupants)) >= FOOD_NEED_PER_TICK:
            continue  

        if origin_pos not in tile_vector_cache:
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
                    target_pos = (nx, ny)
                    tile = world.get_tile(nx, ny)
                    
                    food_share = tile.food_wild / (occupancy.get(target_pos, 0) + 1)
                    if food_share >= FOOD_NEED_PER_TICK and food_share > best_food:
                        best_food = food_share
                        best_target = target_pos
            
            tile_vector_cache[origin_pos] = best_target

        chosen_vector = tile_vector_cache[origin_pos]

        # 6. DEADLOCK SAFETY ESCAPE PHASE
        if chosen_vector is None:
            h = agent.id.__hash__()
            dx = (h % 3) - 1
            dy = ((h // 3) % 3) - 1
            tx = min(max(agent.x + dx, 0), world.width - 1)
            ty = min(max(agent.y + dy, 0), world.height - 1)
            chosen_vector = (tx, ty)

        if chosen_vector is not None:
            tx, ty = chosen_vector
            occupancy[(cx, cy)] -= 1
            step_x = (tx > cx) - (tx < cx)
            step_y = (ty > cy) - (ty < cy)
            agent.x += step_x
            agent.y += step_y
            occupancy[(agent.x, agent.y)] += 1
