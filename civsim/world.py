"""
civsim/world.py
Persistent environment map: tracks tile-by-tile wild resources, soil health degradation vectors, 
and unique regional climate zones, dynamically balanced to allow sustainable civilizational expansion.
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
        self.northern_weather = "NORMAL"
        
        for x in range(width):
            for y in range(height):
                if y < 25:
                    zone = "TUNDRA"
                    max_f = 30.0        # Raised tundra base pool
                    r_rate = 0.6        # Safer baseline northern recovery
                else:
                    zone = "VALLEY"
                    max_f = 65.0        # Expanded valley resource buffers
                    r_rate = 1.5        # Robust baseline valley replenishment

                self.tiles[(x, y)] = Tile(
                    x=x, y=y, max_food=max_f, food_wild=max_f,
                    soil_health=1.0, regen_rate=r_rate, zone_type=zone
                )

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[(x, y)]

    def tick_ecosystem(self, agents_registry, tech_registry=None) -> None:
        """Processes regional climate trends and resource production yields with balanced difficulty weights."""
        # 1. Update Core Valley Weather Cycle (80% Normal/Wet growth baselines)
        if random.random() < 0.08:
            roll = random.random()
            if roll < 0.50: self.current_weather = "NORMAL"
            elif roll < 0.85: self.current_weather = "WET"
            elif roll < 0.92: self.current_weather = "ARID"
            elif roll < 0.96: self.current_weather = "DROUGHT"
            else: self.current_weather = "FREEZE"

        # 2. Update Tundra Weather Cycle
        if random.random() < 0.12:
            roll = random.random()
            if roll < 0.30: self.northern_weather = "NORMAL"
            elif roll < 0.55: self.northern_weather = "WET"
            elif roll < 0.70: self.northern_weather = "ARID"
            elif roll < 0.82: self.northern_weather = "DROUGHT"
            else: self.northern_weather = "FREEZE"

        # 3. Index total population loads
        occupancy = {}
        for agent in agents_registry.raw_living_agents():
            pos = (agent.x, agent.y)
            occupancy[pos] = occupancy.get(pos, 0) + 1
        for c_pos, cohort in agents_registry.cohorts.items():
            occupancy[c_pos] = occupancy.get(c_pos, 0) + cohort.count

        # 4. Process Tile Infrastructure Multipliers
        for pos, tile in self.tiles.items():
            load = occupancy.get(pos, 0)
            
            has_agriculture = False
            has_arctic_hunting = False
            
            for cohort in agents_registry.cohorts.values():
                if (cohort.x, cohort.y) == pos and cohort.settlement_id and tech_registry is not None:
                    tech_state = tech_registry.get_state(cohort.settlement_id)
                    if "Agriculture" in tech_state.unlocked_techs:
                        has_agriculture = True
                    if "Arctic Hunting" in tech_state.unlocked_techs:
                        has_arctic_hunting = True

            # Dynamic Soil Maintenance: Prevent sudden dust-bowl starvation crashes
            if load > 40:
                degradation_rate = 0.00005 if has_agriculture else 0.0003
                tile.soil_health = max(0.25, tile.soil_health - (load * degradation_rate))
            else:
                tile.soil_health = min(1.0, tile.soil_health + 0.03)

            # Apply separate regional weather modifiers
            active_weather = self.northern_weather if tile.zone_type == "TUNDRA" else self.current_weather
            
            # FIX: Lowered weather penalties slightly so winter doesn't cause instant tribal erasure loops
            weather_modifier = 1.0
            if active_weather == "DROUGHT": 
                weather_modifier = 0.55 if has_agriculture else 0.40
            elif active_weather == "FREEZE": 
                weather_modifier = 0.50 if has_arctic_hunting else 0.25

            current_max = tile.max_food_wild * (2.5 if has_agriculture else 1.0)

            # Regeneration execution cycle
            if tile.food_wild < current_max:
                regen = tile.regen_rate * tile.soil_health * weather_modifier
                if has_agriculture:
                    regen *= 2.0 
                tile.food_wild = min(current_max, tile.food_wild + regen)

            # Population extraction depletion
            if load > 0:
                extraction_efficiency = 0.03 if has_agriculture else 0.06
                tile.food_wild = max(0.0, tile.food_wild - (load * extraction_efficiency))
