"""
civsim/movement.py
Agent behavior: Integrated Adaptive Resolution Management.
Optimized to integrate individual risk-awareness and environmental danger perception.
"""

from collections import defaultdict
from civsim.agents import Agent, AgentRegistry, DemographicCohort, FOOD_NEED_PER_TICK, Resolution
from civsim.world import World

SEARCH_RADIUS = 2  
MAX_ALLOWED_HIGH_RES_INDIVIDUALS = 100  


def resolve_movement(world: World, agents: AgentRegistry) -> None:
    """Executes pathfinding steps utilizing individual hazard awareness constraints."""
    all_raw_living = agents.raw_living_agents()
    
    # Enforce performance throttle ceiling
    current_high_res = [a for a in all_raw_living if a.resolution != Resolution.COMPRESSED]
    if len(current_high_res) > MAX_ALLOWED_HIGH_RES_INDIVIDUALS:
        current_high_res.sort(key=lambda a: a.age)
        excess_count = len(current_high_res) - MAX_ALLOWED_HIGH_RES_INDIVIDUALS
        for i in range(excess_count):
            agent_to_throttle = current_high_res[i]
            agent_to_throttle.resolution = Resolution.COMPRESSED

    living = agents.living_agents()
    if not living:
        return
    
    grid_buckets = defaultdict(list)
    for agent in living:
        grid_buckets[(agent.x, agent.y)].append(agent)

    # Cohort compression
    for pos, agents_on_tile in grid_buckets.items():
        if len(agents_on_tile) >= 3:  
            if pos not in agents.cohorts:
                lead_agent = agents_on_tile
                s_id = getattr(lead_agent, "settlement_id", None)
                gen = getattr(lead_agent, "generation", 0)
                
                agents.cohorts[pos] = DemographicCohort(
                    x=pos[0], 
                    y=pos[1], 
                    generation=gen,
                    settlement_id=s_id
                )
            
            cohort = agents.cohorts[pos]
            new_count = 0
            new_age = 0
            for agent in agents_on_tile:
                new_count += 1
                new_age += agent.age
                agent.resolution = Resolution.COMPRESSED  
            
            cohort.count += new_count
            cohort.total_age += new_age

    living = agents.living_agents()

    # Unified occupancy map
    occupancy = defaultdict(int)
    for c_pos, cohort in agents.cohorts.items():
        occupancy[c_pos] += cohort.count
    for agent in living:
        occupancy[(agent.x, agent.y)] += 1

    # Dynamic Navigation Loop
    for agent in living:
        cx, cy = agent.x, agent.y
        origin_pos = (cx, cy)
        current_tile = world.get_tile(cx, cy)
        
        # REALISM CHECK: Risk-awareness behavior loop
        # High hazard memory suppresses curiosity wandering, forcing agents to stay sheltered
        danger_memory = getattr(agent, "hazard_experience", 0.0)
        local_occupants = occupancy.get(origin_pos, 1)
        
        # If danger memory is high, the agent prioritizes localized urban safety over wandering
        if danger_memory > 2.0 and agent.settlement_id is not None:
            continue  # Lock position to stay huddled inside the settlement infrastructure boundary

        if (current_tile.food_wild / max(1, local_occupants)) >= FOOD_NEED_PER_TICK:
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
                target_pos = (nx, ny)
                tile = world.get_tile(nx, ny)
                
                food_share = tile.food_wild / (occupancy.get(target_pos, 0) + 1)
                if food_share >= FOOD_NEED_PER_TICK and food_share > best_food:
                    best_food = food_share
                    best_target = target_pos

        if best_target is None:
            h = agent.id.__hash__()
            dx = (h % 3) - 1
            dy = ((h // 3) % 3) - 1
            tx = min(max(cx + dx, 0), world.width - 1)
            ty = min(max(cy + dy, 0), world.height - 1)
            best_target = (tx, ty)

        if best_target != origin_pos:
            tx, ty = best_target
            step_x = (tx > cx) - (tx < cx)
            step_y = (ty > cy) - (ty < cy)
            
            new_x = cx + step_x
            new_y = cy + step_y
            
            occupancy[origin_pos] -= 1
            agent.x = new_x
            agent.y = new_y
            occupancy[(new_x, new_y)] += 1
