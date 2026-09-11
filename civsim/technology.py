"""
civsim/technology.py
Technology and Infrastructure: Tracks accumulation of Knowledge from production, 
unlocking advancements that boost worker productivity and environmental resilience.
"""
from dataclasses import dataclass, field
from civsim.settlements import SettlementRegistry

KNOWLEDGE_PER_SURPLUS_FOOD = 0.05
TECH_THRESHOLDS = {
    "Agriculture": 100.0,            # Greatly boosts food cultivation ceilings
    "Warm Clothing": 180.0,          # Insulates citizens completely from cold tundra exposure damage
    "Arctic Hunting": 220.0,         # FIX: Lets northern tribes extract double food from tundra tiles during freezes
    "Toolmaking": 250.0,             # Boosts worker resource extraction speed
    "Irrigation": 500.0,             # Allows settlements to pull food from nearby tiles
}


@dataclass
class TechState:
    knowledge: float = 0.0
    unlocked_techs: set[str] = field(default_factory=set)
    infrastructure_level: float = 0.0


class TechRegistry:
    def __init__(self):
        self.settlement_techs: dict[str, TechState] = {}

    def get_state(self, settlement_id: str) -> TechState:
        if settlement_id not in self.settlement_techs:
            self.settlement_techs[settlement_id] = TechState()
        return self.settlement_techs[settlement_id]

    def resolve_innovation(self, settlements: SettlementRegistry, current_tick: int) -> None:
        """Accumulates knowledge across active settlements based on their density."""
        for s_id, settlement in settlements.settlements.items():
            if not settlement.active:
                continue
                
            state = self.get_state(s_id)
            base_pop = len(settlement.member_ids)
            
            gained = max(1, base_pop) * KNOWLEDGE_PER_SURPLUS_FOOD
            state.knowledge += gained
            
            # Check for breakthroughs
            for tech, cost in TECH_THRESHOLDS.items():
                if tech not in state.unlocked_techs and state.knowledge >= cost:
                    state.unlocked_techs.add(tech)
                    
            state.infrastructure_level = len(state.unlocked_techs) * 2.0
