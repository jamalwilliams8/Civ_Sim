"""
civsim/hazards.py
Implements solo wilderness exposure risks and adaptive hazard learning vectors.
Agents outside safe settlement zones face health penalties and learn to avoid the wild.
"""

import random
from civsim.agents import AgentRegistry, Resolution, HEALTH_LOSS_IF_UNFED
from civsim.settlements import SettlementRegistry, _within_radius, SETTLEMENT_RADIUS

WILDERNESS_HAZARD_CHANCE = 0.15
BASE_HAZARD_DAMAGE = 2.0


def resolve_wilderness_hazards(agents: AgentRegistry, settlements: SettlementRegistry, current_tick: int) -> None:
    """Evaluates agents exposed in the wilderness, applying damage and updating hazard memory."""
    living = agents.raw_living_agents()
    active_cities = [s for s in settlements.settlements.values() if s.active]

    for agent in living:
        # Determine if the agent is physically inside any safe city radius
        sheltered = False
        for city in active_cities:
            if _within_radius(agent.x, agent.y, city.home_x, city.home_y, SETTLEMENT_RADIUS):
                sheltered = True
                break

        if sheltered:
            continue  # Safe inside city infrastructure boundaries

        # Agent is exposed in the wild. Evaluate hazard trigger
        if random.random() < WILDERNESS_HAZARD_CHANCE:
            # Pull custom experience parameters using safe attribute lookups
            experience = getattr(agent, "hazard_experience", 0.0)
            
            # Learning effect: Higher experience reduces damage taken (acclimatization)
            damage_mitigation = min(0.75, experience * 0.05)
            final_damage = max(0.5, BASE_HAZARD_DAMAGE * (1.0 - damage_mitigation))
            
            agent.health -= final_damage
            
            # Increment memory weight — the agent learns from surviving danger
            new_exp = experience + 1.0
            try:
                agent.hazard_experience = new_exp
            except AttributeError:
                pass  # Fallback shield for safety
