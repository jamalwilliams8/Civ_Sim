"""
civsim/occupations.py
Implements Phase 3 Specialized Occupations. Allocates labor roles 
(Farmer, Blacksmith, Soldier) based on density and technological requirements.
"""

from collections import defaultdict
from civsim.agents import AgentRegistry, Resolution

def resolve_occupations(agents: AgentRegistry, settlements) -> None:
    """Dynamically slices settlement populations into specialized socio-economic labor roles."""
    living = agents.raw_living_agents()
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    # Map total urban counts by settlement ID
    city_pops = defaultdict(int)
    for agent in living:
        if agent.settlement_id:
            city_pops[agent.settlement_id] += 1

    for s in active_cities:
        pop = city_pops.get(s.id, 0)
        if pop <= 0:
            continue

        # Fetch city agents across uncompressed bands to assign labor roles cleanly
        city_agents = [a for a in living if a.settlement_id == s.id]
        
        # Sort by age so younger agents farm, middle-aged craft, and robust units serve as soldiers
        city_agents.sort(key=lambda a: a.age)
        
        # Proportional Division: 50% Farmers, 30% Blacksmiths, 20% Soldiers/Guards
        num_farmers = int(pop * 0.50)
        num_smiths = int(pop * 0.30)
        
        for idx, agent in enumerate(city_agents):
            if idx < num_farmers:
                setattr(agent, "occupation", "FARMER")
            elif idx < (num_farmers + num_smiths):
                setattr(agent, "occupation", "BLACKSMITH")
            else:
                setattr(agent, "occupation", "SOLDIER")
