"""
civsim/diagnostics.py
Diagnostics & Historical Chronicler: Compiles active system metrics.
Exposes internal social friction indices, crime rates, and miraculous belief anomalies.
"""

from civsim.agents import AgentRegistry, Resolution
from civsim.world import World
from civsim.settlements import SettlementRegistry


def report(world: World, agents: AgentRegistry, settlements: SettlementRegistry, ticks_run: int) -> dict:
    all_agents = list(agents.agents.values())
    living_high_res = [a for a in all_agents if a.alive and a.resolution != Resolution.COMPRESSED]
    dead = [a for a in all_agents if not a.alive]

    low_res_population = sum(c.count for c in agents.cohorts.values())
    total_living_population = len(living_high_res) + low_res_population

    death_causes = {}
    for d in dead:
        if d.death_cause != "compressed":  
            death_causes[d.death_cause] = death_causes.get(d.death_cause, 0) + 1

    avg_health = sum(a.health for a in living_high_res) / len(living_high_res) if living_high_res else 0.0
    tiles = list(world.tiles.values())
    avg_food = sum(t.food_wild for t in tiles) / len(tiles)

    active_cities = []
    significant_ruins = []

    for s_id, s in settlements.settlements.items():
        city_name = getattr(s, "name", s.id)
        
        info = {
            "name": city_name,
            "coordinates": (s.home_x, s.home_y),
            "founded_year": s.founded_tick,
            "peak_pop": getattr(s, "peak_population", 0),
            "lifespan": getattr(s, "last_active_tick", s.founded_tick) - s.founded_tick,
            "crime_rate": getattr(s, "crime_rate", 0.0),
            "guard_force": getattr(s, "guard_force", 0.0),
            # FIX: Pull cached miracle variable strings safely using fallback defaults
            "miracle_status": getattr(s, "last_miracle_result", "NO_RECENT_PHENOMENA")
        }
        
        if getattr(s, "active", True):
            local_cohort_pop = sum(c.count for pos, c in agents.cohorts.items() if getattr(c, "settlement_id", None) == s.id)
            local_indiv_pop = sum(1 for a in all_agents if a.alive and a.settlement_id == s.id and a.resolution != Resolution.COMPRESSED)
            info["current_population"] = local_indiv_pop + local_cohort_pop
            active_cities.append(info)
        else:
            if info["lifespan"] >= 150 and info["peak_pop"] >= 150:
                significant_ruins.append(info)
            elif info["lifespan"] >= 60 and info["peak_pop"] >= 40:
                significant_ruins.append(info)

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
            "ruins_count": len(significant_ruins),
            "ruins_details": significant_ruins
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
        print(f" * The Domain of {city['name']} at {city['coordinates']} | Citizens: {city['current_population']}")
        print(f"   [Society Status] Crime Index: {city['crime_rate']*100:.1f}% | Watch Force: {city['guard_force']*100:.1f}%")
        # FIX: Print the emergent miracle resolution ledger string
        print(f"   [Belief Matrix ] Last Miracle Record: {city['miracle_status']}")
        
    print("====================================================")
