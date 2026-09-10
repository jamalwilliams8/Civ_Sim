"""
Diagnostics & Historical Chronicler: Compiles system metrics. 
Defends against OneDrive cloud caching inconsistencies by using safe parameter lookups.
"""

from civsim.agents import AgentRegistry
from civsim.world import World
from civsim.settlements import SettlementRegistry


def report(world: World, agents: AgentRegistry, settlements: SettlementRegistry, ticks_run: int) -> dict:
    all_agents = list(agents.agents.values())
    living_high_res = [a for a in all_agents if a.alive]
    dead = [a for a in all_agents if not a.alive]

    # Sum up all hidden mathematical background populations
    low_res_population = sum(c.count for c in agents.cohorts.values())
    total_living_population = len(living_high_res) + low_res_population

    death_causes = {}
    for d in dead:
        if d.death_cause != "compressed":  # Avoid tracking resolution shifts as actual mortality
            death_causes[d.death_cause] = death_causes.get(d.death_cause, 0) + 1

    avg_health = sum(a.health for a in living_high_res) / len(living_high_res) if living_high_res else 0.0
    tiles = list(world.tiles.values())
    avg_food = sum(t.food_wild for t in tiles) / len(tiles)

    active_cities = []
    discovered_ruins = []

    for s_id, s in settlements.settlements.items():
        # OneDrive Cache Protection: Use safe getattr defaults to prevent crashes
        peak_pop_val = getattr(s, "peak_population", 0)
        is_active_val = getattr(s, "active", True)
        is_ruin_val = getattr(s, "is_historical_ruin", False)
        is_discovered_val = getattr(s, "discovered", False)

        info = {
            "id": s.id,
            "coordinates": (s.home_x, s.home_y),
            "founded_year": s.founded_tick,
            "peak_pop": peak_pop_val,
            "discovered": is_discovered_val
        }
        
        if is_active_val:
            # Include local coordinates cohort tracking inside city counts
            local_cohort_pop = sum(c.count for pos, c in agents.cohorts.items() if getattr(c, "settlement_id", None) == s.id)
            local_indiv_pop = sum(1 for a in living_high_res if a.settlement_id == s.id)
            info["current_population"] = local_indiv_pop + local_cohort_pop
            active_cities.append(info)
        elif is_ruin_val and is_discovered_val:
            discovered_ruins.append(info)

    return {
        "ticks_run": ticks_run,
        "living_population": total_living_population,
        "tracked_high_res": len(living_high_res),
        "historical_dead_count": len(dead),
        "death_causes": death_causes,
        "avg_health_living": round(avg_health, 2),
        "avg_tile_food": round(avg_food, 2),
        "settlements": {
            "active_count": len(active_cities),
            "active_details": active_cities,
            "ruins_count": len(discovered_ruins),
            "ruins_details": discovered_ruins
        }
    }


def print_history_book(report_data: dict) -> None:
    print("====================================================")
    print(f"        WORLD HISTORY CHRONICLE - YEAR {report_data['ticks_run']}")
    print("====================================================")
    print(f"Total Combined Civilization Population: {report_data['living_population']}")
    print(f"Active High-Res Characters Looked At: {report_data['tracked_high_res']}")
    print(f"Global Cemetery Count: {report_data['historical_dead_count']}")
    print(f"Mortality Records: {report_data['death_causes']}\n")
    
    print(f"--- ACTIVE CIVILIZATIONS ({report_data['settlements']['active_count']}) ---")
    for city in report_data['settlements']['active_details']:
        print(f" * {city['id']} at {city['coordinates']} | Founded: Yr {city['founded_year']} | Citizens: {city['current_population']}")
        
    ruins_count = report_data['settlements']['ruins_count']
    if ruins_count > 0:
        print(f"\n--- ARCHEOLOGICAL DISCOVERIES ({ruins_count}) ---")
        for ruin in report_data['settlements']['ruins_details']:
            print(f" * Agents discovered the ancient farming fields of {ruin['id']} at {ruin['coordinates']}")
            print(f"   Significance: Reached a peak historical size of {ruin['peak_pop']} citizens before abandonment.")
            
    print("====================================================")
