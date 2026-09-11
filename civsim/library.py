"""
civsim/library.py
Implements Phase 2/4 Archive Libraries. Preserves written technological strings 
against catastrophic historical regression waves.
"""

from collections import defaultdict

def resolve_libraries_and_preservation(agents, settlements, tech_registry) -> None:
    """Processes infrastructure building maintenance loops for library book archives."""
    active_cities = [s for s in settlements.settlements.values() if s.active]
    if not active_cities:
        return

    # Track city populations across cohorts
    city_pops = defaultdict(int)
    for cohort in agents.cohorts.values():
        if getattr(cohort, "settlement_id", None):
            city_pops[cohort.settlement_id] += cohort.count

    for city in active_cities:
        pop = city_pops.get(city.id, 0)
        has_library = getattr(city, "has_archive_library", False)

        # Settlements construct libraries when their specialized population hits a stable footprint
        if not has_library and pop >= 30:
            setattr(city, "has_archive_library", True)
            setattr(city, "library_volume_count", 3)
        elif has_library:
            tech_state = tech_registry.get_state(city.id)
            setattr(city, "library_volume_count", max(1, len(tech_state.unlocked_techs)))
        else:
            setattr(city, "has_archive_library", False)
            setattr(city, "library_volume_count", 0)
