"""
civsim/economy.py
Implements Phase 3 Barter Markets. Allows neighboring settlements to 
establish trade agreements, passing surplus resources between coordinates.
"""

from civsim.settlements import SettlementRegistry, _within_radius

TRADE_RADIUS = 8  # Maximum tile distance across which barter caravans can travel
TRADE_EFFICIENCY_GAIN = 0.5


def resolve_economic_barter_trade(world, settlements: SettlementRegistry) -> None:
    """Active settlements share localized resource surpluses with struggling neighbors."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if len(active_cities) < 2:
        return

    # Pairwise comparison to find trade opportunities between active nodes
    for i, city_a in enumerate(active_cities):
        tile_a = world.get_tile(city_a.home_x, city_a.home_y)
        
        for city_b in active_cities[i+1:]:
            # Verify if settlements are within economic caravan travel radius
            if _within_radius(city_a.home_x, city_a.home_y, city_b.home_x, city_b.home_y, TRADE_RADIUS):
                tile_b = world.get_tile(city_b.home_x, city_b.home_y)
                
                # Check for food imbalances to execute a trade exchange
                if tile_a.food_wild > 30.0 and tile_b.food_wild < 10.0:
                    # Trade food from A to B
                    transfer = (tile_a.food_wild - tile_b.food_wild) * 0.2
                    tile_a.food_wild -= transfer
                    tile_b.food_wild += transfer * (1.0 + TRADE_EFFICIENCY_GAIN)
                elif tile_b.food_wild > 30.0 and tile_a.food_wild < 10.0:
                    # Trade food from B to A
                    transfer = (tile_b.food_wild - tile_a.food_wild) * 0.2
                    tile_b.food_wild -= transfer
                    tile_a.food_wild += transfer * (1.0 + TRADE_EFFICIENCY_GAIN)
