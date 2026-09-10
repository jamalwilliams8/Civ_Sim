"""
civsim/world.py
Persistent environment map: tracks tile-by-tile wild resources, soil health degradation vectors, 
and global cyclical Weather/Climate patterns. Raw and unscripted from Year 0.
"""

import random

WEATHER_TYPES = ["NORMAL", "WET", "ARID", "DROUGHT", "FREEZE"]


class Tile:
    def __init__(self, x: int, y: int, max_food: float, food_wild: float, soil_health: float, regen_rate: float):
        self.x = x
        self.y = y
        self.max_food_wild = max_food
        self.food_wild = food_wild
        self.soil_health = soil_health
        self.regen_rate = regen_rate


class World:
    def __init__(self, width: int, height: int, rng=None):
        self.width = width
        self.height = height
        self.tiles = {}
        self.current_weather = "NORMAL"
        
        for x in range(width):
            for y in range(height):
                self.tiles[(x, y)] = Tile(
                    x=x, y=y,
                    max_food=25.0,        # Expanded base resource baseline pool
                    food_wild=25.0,
                    soil_health=1.0,
                    regen_rate=0.6        # Standardized regeneration speed
                )

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[(x, y)]

    def tick_ecosystem(self, agents_registry) -> None:
        """Processes environment changes, climate trends, and soil load carrying capacities."""
        # REALISM CHECK: Unscripted, dynamic weather shifts can execute from Tick 1
        if random.random() < 0.08:
            self.current_weather = random.choice(WEATHER_TYPES)

        occupancy = {}
        for agent in agents_registry.raw_living_agents():
            pos = (agent.x, agent.y)
            occupancy[pos] = occupancy.get(pos, 0) + 1

        for c_pos, cohort in agents_registry.cohorts.items():
            occupancy[c_pos] = occupancy.get(c_pos, 0) + cohort.count

        # Compute climate modifiers
        weather_modifier = 1.0
        if self.current_weather == "DROUGHT":
            weather_modifier = 0.25  
        elif self.current_weather == "FREEZE":
            weather_modifier = 0.10  

        for pos, tile in self.tiles.items():
            load = occupancy.get(pos, 0)
            
            # Soil degradation vectors
            if load > 40:
                tile.soil_health = max(0.05, tile.soil_health - (load * 0.001))
            else:
                tile.soil_health = min(1.0, tile.soil_health + 0.005)

            # Regeneration cycle
            if tile.food_wild < tile.max_food_wild:
                regen = tile.regen_rate * tile.soil_health * weather_modifier
                tile.food_wild = min(tile.max_food_wild, tile.food_wild + regen)

            # Population extraction depletion
            if load > 0:
                tile.food_wild = max(0.0, tile.food_wild - (load * 0.08))
