"""
civsim/diagnostics.py
Diagnostics & Historical Chronicler: Compiles active system metrics.
Exposes environmental trends, market metrics, progressive taxes, and labor tracks.
"""

from civsim.agents import AgentRegistry, Resolution
from civsim.world import World
from civsim.settlements import SettlementRegistry


def report(world: World, agents: AgentRegistry, settlements: SettlementRegistry, ticks_run: int) -> dict:
    all_agents = list(agents.agents.values())
    living_high_res = [a for a in all_agents if a.alive and a.resolution != Resolution.COMPRESSED]
    dead = [a.id for a in all_agents if not a.alive]
    low_res_population = sum(c.count for c in agents.cohorts.values())
    total_living_population = len(living_high_res) + low_res_population

    death_causes = {}
    for a in all_agents:
        if not a.alive and a.death_cause != "compressed":
            death_causes[a.death_cause] = death_causes.get(a.death_cause, 0) + 1

    avg_health = sum(a.health for a in living_high_res) / len(living_high_res) if living_high_res else 0.0
    tiles = list(world.tiles.values())
    avg_food = sum(t.food_wild for t in tiles) / len(tiles)

    active_cities = []

    for s_id, s in settlements.settlements.items():
        city_name = getattr(s, "name", s.id)
        
        # FIX: Directly target the actual structural attributes bound to individual settlement nodes
        has_lib = getattr(s, "has_archive_library", False)
        lib_count = getattr(s, "library_volume_count", 0)
        
        info = {
            "name": city_name,
            "coordinates": (s.home_x, s.home_y),
            "founded_year": s.founded_tick,
            "crime_rate": getattr(s, "crime_rate", 0.0),
            "guard_force": getattr(s, "guard_force", 0.0),
            "miracle_status": getattr(s, "last_miracle_result", "NO_RECENT_PHENOMENA"),
            "has_library": has_lib,
            "library_books": lib_count,
            "economy": getattr(s, "economy_type", "BARTER_SYSTEM"),
            "price_index": getattr(s, "food_price_index", 1.0),
            "inflation": getattr(s, "inflation_rate", 0.0),
            "avg_nw": getattr(s, "avg_net_worth", 0.0),
            "guild_craft": getattr(s, "guild_craft_size", 0),
            "treasury": getattr(s, "public_treasury", 0.0),
            "fortifications": getattr(s, "fortifications", 0.0),
            "apprentices": getattr(s, "guild_apprentice_size", 0),
            "smugglers": getattr(s, "guild_smuggler_size", 0)
        }
        
        if getattr(s, "active", True):
            local_cohort_pop = sum(c.count for pos, c in agents.cohorts.items() if getattr(c, "settlement_id", None) == s.id)
            local_indiv_pop = sum(1 for a in all_agents if a.alive and a.settlement_id == s.id and a.resolution != Resolution.COMPRESSED)
            info["current_population"] = local_indiv_pop + local_cohort_pop
            active_cities.append(info)

    return {
        "ticks_run": ticks_run,
        "living_population": total_living_population,
        "tracked_high_res": len(living_high_res),
        "historical_dead_count": len(dead),
        "death_causes": death_causes,
        "avg_health_living": round(avg_health, 2),
        "avg_tile_food": round(avg_food, 2),
        "current_climate": getattr(world, "current_weather", "NORMAL"),
        "settlements": {
            "active_count": len(active_cities),
            "active_details": active_cities
        }
    }


def print_history_book(report_data: dict) -> None:
    print("====================================================")
    print(f"        WORLD HISTORY CHRONICLE - YEAR {report_data['ticks_run']}")
    print("====================================================")
    print(f"Global Climate State  : {report_data['current_climate']}")
    print(f"Total Combined Population: {report_data['living_population']}")
    print(f"Global Cemetery Count  : {report_data['historical_dead_count']}")
    print(f"Mortality Records: {report_data['death_causes']}\n")
    
    print(f"--- ACTIVE CIVILIZATIONS ({report_data['settlements']['active_count']}) ---")
    for city in report_data['settlements']['active_details']:
        # Fix text string representation formatting
        lib_text = f"YES ({city['library_books']} texts)" if city['has_library'] else "NONE"
        print(f" * The Domain of {city['name']} at {city['coordinates']} | Citizens: {city['current_population']}")
        print(f"   [Society Status] Crime Index: {city['crime_rate']*100:.1f}% | Watch Force: {city['guard_force']*100:.1f}% | Walls: {city['fortifications']} defense")
        print(f"   [Public Treasury] Accumulated Fund: {city['treasury']} coins | System Mode: PROGRESSIVE_TAX_POOL")
        print(f"   [Market Economy] System: {city['economy']} | Food Price Index: {city['price_index']}x | Token Inflation: {city['inflation']}%")
        print(f"   [Labor Registry] Avg Net Worth: {city['avg_nw']} coins | Master Smiths: {city['guild_craft']} | Apprentices: {city['apprentices']} | Smugglers: {city['smugglers']}")
        print(f"   [Knowledge Hub ] Institutional Archive Library: {lib_text} | Miracle: {city['miracle_status']}")
        print("")
        
    print("====================================================")
