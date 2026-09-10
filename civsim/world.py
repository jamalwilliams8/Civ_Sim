"""
civsim/world.py
Persistent environment map: tracks tile-by-tile wild resources, soil health degradation vectors, 
and unique regional climate zones (Harsh Northern Tundra vs Fertile Valleys).
"""

import random


class Tile:
    def __init__(self, x: int, y: int, max_food: float, food_wild: float, soil_health: float, regen_rate: float, zone_type: str):
        self.x = x
        self.y = y
        self.max_food_wild = max_food
        self.food_wild = food_wild
        self.soil_health = soil_health
        self.regen_rate = regen_rate
        self.zone_type = zone_type # "TUNDRA" or "VALLEY"


class World:
    def __init__(self, width: int, height: int, rng=None):
        self.width = width
        self.height = height
        self.tiles = {}
        self.current_weather = "NORMAL"
        self.northern_weather = "NORMAL" # Separate climate cycle for the harsh north
        
        for x in range(width):
            for y in range(height):
                # Regional Separation: Northern 25% of the map matrix is designated as Harsh Tundra
                if y < 25:
                    zone = "TUNDRA"
                    max_f = 15.0
                    r_rate = 0.3
                else:
                    zone = "VALLEY"
                    max_f = 25.0
                    r_rate = 0.6

                self.tiles[(x, y)] = Tile(
                    x=x, y=y, max_food=max_f, food_wild=max_f,
                    soil_health=1.0, regen_rate=r_rate, zone_type=zone
                )

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[(x, y)]

    def tick_ecosystem(self, agents_registry) -> None:
        """Processes environment changes, regional climate shifts, and soil loads."""
        # 1. Update Core Valley Weather Cycle (8% chance to shift)
        if random.random() < 0.08:
            roll = random.random()
            if roll < 0.45: self.current_weather = "NORMAL"
            elif roll < 0.80: self.current_weather = "WET"
            elif roll < 0.90: self.current_weather = "ARID"
            elif roll < 0.95: self.current_weather = "DROUGHT"
            else: self.current_weather = "FREEZE"

        # 2. Update Harsh Northern Tundra Weather Cycle (Significantly higher FREEZE probability)
        if random.random() < 0.12:
            roll = random.random()
            if roll < 0.20: self.northern_weather = "NORMAL"
            elif roll < 0.40: self.northern_weather = "WET"
            elif roll < 0.50: self.northern_weather = "ARID"
            elif roll < 0.60: self.northern_weather = "DROUGHT"
            else: self.northern_weather = "FREEZE" # 40% chance for a winter crisis in the Tundra

        occupancy = {}
        for agent in agents_registry.raw_living_agents():
            pos = (agent.x, agent.y)
            occupancy[pos] = occupancy.get(pos, 0) + 1
        for c_pos, cohort in agents_registry.cohorts.items():
            occupancy[c_pos] = occupancy.get(c_pos, 0) + cohort.count

        for pos, tile in self.tiles.items():
            load = occupancy.get(pos, 0)
            
            # Soil degradation vectors
            if load > 40:
                tile.soil_health = max(0.05, tile.soil_health - (load * 0.001))
            else:
                tile.soil_health = min(1.0, tile.soil_health + 0.005)

            # Apply separate regional weather modifiers
            active_weather = self.northern_weather if tile.zone_type == "TUNDRA" else self.current_weather
            weather_modifier = 1.0
            if active_weather == "DROUGHT": weather_modifier = 0.25
            elif active_weather == "FREEZE": weather_modifier = 0.10

            # Regeneration cycle
            if tile.food_wild < tile.max_food_wild:
                regen = tile.regen_rate * tile.soil_health * weather_modifier
                tile.food_wild = min(tile.max_food_wild, tile.food_wild + regen)

            # Population extraction depletion
            if load > 0:
                tile.food_wild = max(0.0, tile.food_wild - (load * 0.08))
