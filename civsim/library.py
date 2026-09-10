"""
civsim/library.py
Implements Phase 2/4 Archive Libraries. Preserves written technological strings 
against catastrophic historical regression waves.
"""

from collections import defaultdict
from civsim.agents import AgentRegistry

LIBRARY_LABOR_REQUIREMENT = 10.0


def resolve_libraries_and_preservation(agents: AgentRegistry, settlements, tech_registry) -> None:
    """Processes infrastructure building maintenance loops for library book archives."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    # Track blacksmith craft volumes per city node via direct pass
    smith_counts = defaultdict(int)
    for agent in agents.raw_living_agents():
        if agent.settlement_id and getattr(agent, "occupation", "FARMER") == "BLACKSMITH":
            smith_counts[agent.settlement_id] += 1

    for city in active_cities:
        num_smiths = smith_counts.get(city.id, 0)
        has_library = getattr(city, "has_archive_library", False)

        if not has_library and num_smiths >= 5:
            # Blacksmiths forge preservation tools: Build a Library
            setattr(city, "has_archive_library", True)
            
            # Log archive creation inside our history tracking registry channels
            tech_state = tech_registry.get_state(city.id)
            setattr(city, "library_volume_count", len(tech_state.unlocked_techs))
        elif has_library:
            tech_state = tech_registry.get_state(city.id)
            # Sync the library archives capacity to hold newly discovered techs
            setattr(city, "library_volume_count", len(tech_state.unlocked_techs))
