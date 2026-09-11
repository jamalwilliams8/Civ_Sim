"""
civsim/settlements.py
Manages settlement registration boundaries, structural city growth vectors,
and regional biome coordinate initializations.
"""
import random
from civsim.agents import AgentRegistry, Resolution

class Settlement:
    def __init__(self, id, name, home_x, home_y, current_tick):
        self.id = id
        self.name = name
        self.home_x = home_x
        self.home_y = home_y
        self.founded_tick = current_tick
        self.active = True
        self.food_price_index = 1.0
        self.public_treasury = 0.0
        self.fortifications = 0.0
        self.crime_rate = 0.0
        self.civic_comfort_score = 0.0
        self.economy_type = "BARTER_SYSTEM"
        self.government_type = "TRIBAL_CHIEFDOM"
        self.central_bank_status = "NONE"
        self.last_bank_action = "NO_BANK_FOUNDED"
        self.defense_tier = "EARTHEN_DIKE"
        self.comfort_tier = "PRIMITIVE_CESSPOOLS"
        self.last_political_milestone = "NONE"
        
        # FIX: Natively initialize the missing leader tracking node properties
        self.leader_id = None

class SettlementRegistry:
    def __init__(self):
        self.settlements = {}
        self.next_city_id = 0
        self.city_names = ["Elderpeak", "Ironcomb", "Mosskeep", "Dawnhold", "Lowhurst", "Goldwood", "Clayreach", "Shadowreach"]

    def create_settlement(self, home_x, home_y, current_tick):
        city_id = f"STL-{self.next_city_id}"
        name = self.city_names[self.next_city_id % len(self.city_names)]
        if self.next_city_id >= len(self.city_names):
            name += f" III"
        self.next_city_id += 1
        
        new_city = Settlement(city_id, name, home_x, home_y, current_tick)
        self.settlements[city_id] = new_city
        return new_city

def resolve_settlements(agents, settlements, current_tick) -> None:
    """Spawns city grids if background cohort populations concentrate over threshold limits."""
    living = agents.raw_living_agents()
    coord_map = {}
    
    for agent in living:
        if not agent.settlement_id:
            pos = (agent.x, agent.y)
            coord_map[pos] = coord_map.get(pos, 0) + 1

    for pos, count in coord_map.items():
        if count >= 10:
            already_exists = any(s.home_x == pos[0] and s.home_y == pos[1] and s.active for s in settlements.settlements.values())
            if not already_exists:
                new_settlement = settlements.create_settlement(pos[0], pos[1], current_tick)
                for agent in living:
                    if agent.x == pos[0] and agent.y == pos[1]:
                        agent.settlement_id = new_settlement.id

# --- GEOGRAPHIC RADIAL UTILITIES ---
SETTLEMENT_RADIUS = 3

def _within_radius(x1, y1, x2, y2, radius=SETTLEMENT_RADIUS) -> bool:
    """Calculates if coordinates sit within a localized spatial territory boundary."""
    return abs(x1 - x2) <= radius and abs(y1 - y2) <= radius
