"""
civsim/infrastructure.py
Manages housing construction loops. Labor invested builds housing quality,
counterbalancing settlement overcrowding and providing a structural insulation shield against cold damage.
"""

from collections import defaultdict
from civsim.agents import AgentRegistry, Resolution
from civsim.settlements import SettlementRegistry

CONSTRUCTION_RATE_PER_WORKER = 0.05
MAX_HOUSING_QUALITY = 5.0


def resolve_housing_infrastructure(agents: AgentRegistry, settlements: SettlementRegistry) -> None:
    """Accumulates labor volumes to build and maintain housing insulation levels across tiles."""
    living = agents.raw_living_agents()
    
    # 1. Map total labor capacity per coordinate spot in a single pass
    labor_map = defaultdict(float)
    for agent in agents.living_agents():
        labor_map[(agent.x, agent.y)] += 1.0
    for pos, cohort in agents.cohorts.items():
        labor_map[pos] += float(cohort.count)

    # 2. Distribute housing quality improvements to agents sitting on built-up tiles
    for agent in living:
        pos = (agent.x, agent.y)
        labor_present = labor_map.get(pos, 0.0)
        
        has_settlement = False
        if agent.settlement_id:
            has_settlement = True

        current_housing = getattr(agent, "housing_quality", 1.0)
        if has_settlement and labor_present > 2.0:
            # Labor builds up home insulation quality over time
            new_housing = min(MAX_HOUSING_QUALITY, current_housing + (labor_present * CONSTRUCTION_RATE_PER_WORKER))
        else:
            # Passive weather decay outside active construction zones
            new_housing = max(1.0, current_housing - 0.02)

        try:
            agent.housing_quality = new_housing
        except AttributeError:
            pass
