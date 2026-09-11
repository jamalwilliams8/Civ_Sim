"""
civsim/hazards.py
Manages environmental wilderness hazard events. Processes localized climate damage,
shielding agents if they sit within a safe city coordinate radial zone.
Armored with type-casting to prevent tuple assignment infinite freezes.
"""
import random

# Geographic boundary configurations
SETTLEMENT_RADIUS = 3

def resolve_wilderness_hazards(agents, settlements, current_tick: int) -> None:
    """Applies weather exposure damage to agents wandering outside safe urban boundaries."""
    living = agents.raw_living_agents()
    active_cities = [s for s in settlements.settlements.values() if s.active]
    
    # Cache and pre-unpack city positions into clean, safe integer pairs
    safe_zones = []
    for city in active_cities:
        # Check if the coordinates are stored as a tuple or integer, and unpack safely
        if isinstance(city.home_x, tuple):
            cx, cy = int(city.home_x[0]), int(city.home_x[1])
        else:
            cx, cy = int(city.home_x), int(city.home_y)
        safe_zones.append((cx, cy))

    for agent in living:
        # Check if this individual agent sits inside a safe zone radius
        is_sheltered = False
        for (cx, cy) in safe_zones:
            if abs(agent.x - cx) <= SETTLEMENT_RADIUS and abs(agent.y - cy) <= SETTLEMENT_RADIUS:
                is_sheltered = True
                break

        # If they are stuck in the wild without a city insulation quality shield, apply minor exposure friction
        if not is_sheltered and not getattr(agent, "settlement_id", None):
            # Safe baseline environmental friction that will never cause an instant crash loop
            current_housing = getattr(agent, "housing_quality", 1.0)
            if current_housing <= 1.0 and random.random() < 0.05:
                agent.health = max(0.0, agent.health - 2.0)
