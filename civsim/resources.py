"""
Resource production: Labor invested by agents working a tile raises that tile's 
productive capacity (max_food_wild). Integrating with the technology state to 
multiply production if 'Agriculture' or 'Toolmaking' is researched.

Fulfills Phase 2 requirement: "Labor must affect production -> production must affect resources".
"""

from civsim.agents import AgentRegistry
from civsim.world import World
from civsim.technology import TechRegistry

LABOR_CAPACITY_GAIN_PER_AGENT = 0.02  # Base max_food_wild increase per worker-tick
LAND_CAPACITY_CEILING_BASE = 40.0     # Hard cap for uncultivated wild gathering


def resolve_resource_production(world: World, agents: AgentRegistry, tech_registry: TechRegistry) -> None:
    """
    Every living agent works the tile they occupy. If their parent settlement 
    has researched advanced agricultural technologies, the production ceiling 
    multiplies, turning sparse wilderness fields into high-yield farm cities.
    """
    # 1. Map physical coordinates to active labor volumes (including high and low-res components)
    worker_counts = {}
    
    # Track high-res individual workers
    for agent in agents.living_agents():
        key = (agent.x, agent.y)
        worker_counts[key] = worker_counts.get(key, 0) + 1
        
    # Track optimized mathematical low-res cohort workers
    for pos, cohort in agents.cohorts.items():
        if cohort.count > 0:
            worker_counts[pos] = worker_counts.get(pos, 0) + cohort.count

    # 2. Apply labor and compute technological modifiers per occupied tile
    for (x, y), worker_count in worker_counts.items():
        tile = world.get_tile(x, y)
        
        # Determine settlement association to fetch technological scaling vectors
        settlement_id = None
        # Check if an individual here belongs to a city
        for agent in agents.living_agents():
            if agent.x == x and agent.y == y and agent.settlement_id:
                settlement_id = agent.settlement_id
                break
        # Fallback to local cohort city bindings
        if not settlement_id and (x, y) in agents.cohorts:
            settlement_id = agents.cohorts[(x, y)].settlement_id

        # 3. Apply Multipliers from the Technology Tree
        ceiling_multiplier = 1.0
        efficiency_multiplier = 1.0
        
        if settlement_id:
            tech_state = tech_registry.get_state(settlement_id)
            
            # Agriculture increases the total volume of food the land can handle
            if "Agriculture" in tech_state.unlocked_techs:
                ceiling_multiplier = 5.0  # Raises cap from 40 to 200 food!
                
            # Toolmaking increases the rate at which workers cultivate the land
            if "Toolmaking" in tech_state.unlocked_techs:
                efficiency_multiplier = 2.0  # Workers build up fields twice as fast

        # Calculate final scaled thresholds
        active_ceiling = LAND_CAPACITY_CEILING_BASE * ceiling_multiplier
        
        if tile.max_food_wild >= active_ceiling:
            continue
            
        gain = worker_count * LABOR_CAPACITY_GAIN_PER_AGENT * efficiency_multiplier
        tile.max_food_wild = min(active_ceiling, tile.max_food_wild + gain)
