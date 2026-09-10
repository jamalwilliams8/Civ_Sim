"""
civsim/simulation.py
Central execution engine managing sequential tick loops across environmental, 
social, economic, and technological layers.
"""

import random
import time
from civsim.world import World
from civsim.agents import AgentRegistry
from civsim.settlements import SettlementRegistry, resolve_settlements
from civsim.movement import resolve_movement
from civsim.population import resolve_food_and_health, resolve_birth_and_death
from civsim.technology import TechRegistry
from civsim.resources import resolve_resource_production
from civsim.hazards import resolve_wilderness_hazards
from civsim.infrastructure import resolve_housing_infrastructure
from civsim.governance import resolve_governance_decisions
from civsim.economy import resolve_economic_barter_trade
from civsim.history import CausalityEngine  


class Simulation:
    def __init__(self, config=None, seed: int = 42, width: int = 50, height: int = 50):
        starting_pop = 50
        if config is not None:
            if isinstance(config, dict):
                self.seed = config.get("seed", seed)
                width = config.get("world_width", width)
                height = config.get("world_height", height)
                starting_pop = config.get("starting_population", starting_pop)
            else:
                self.seed = getattr(config, "seed", seed)
                width = getattr(config, "world_width", width)
                height = getattr(config, "world_height", height)
                starting_pop = getattr(config, "starting_population", starting_pop)
        else:
            self.seed = seed

        self.current_tick = 0
        
        random.seed(self.seed)
        world_rng = random.Random(self.seed)
        
        self.world = World(width=width, height=height, rng=world_rng)
        self.agents = AgentRegistry()
        self.settlements = SettlementRegistry()
        self.tech_registry = TechRegistry()  
        self.history = CausalityEngine()  

        center_x = width // 2
        center_y = height // 2
        for _ in range(starting_pop):
            rx = random.randint(max(0, center_x - 7), min(width - 1, center_x + 7))
            ry = random.randint(max(0, center_y - 7), min(height - 1, center_y + 7))
            self.agents.create_agent(generation=0, x=rx, y=ry)

        self.history.record_event(0, "WORLD_GEN", center_x, center_y, f"World generation spawned from master seed {self.seed}.")

    def step(self) -> None:
        self.current_tick += 1
        pre_step_active = {s_id: s.active for s_id, s in self.settlements.settlements.items()}

        # 1. Spatial Movement Processing
        resolve_movement(self.world, self.agents)
        
        # 2. Settlement Affiliations
        resolve_settlements(self.agents, self.settlements, self.current_tick)
        
        # 3. Governance Migration Split Decisions
        resolve_governance_decisions(self.world, self.agents, self.settlements, self.current_tick)
        
        # 4. Phase 3 Economy: Execute localized barter market caravan trades
        resolve_economic_barter_trade(self.world, self.settlements)
        
        # 5. Wilderness Hazards
        resolve_wilderness_hazards(self.agents, self.settlements, self.current_tick)
        
        # 6. Infrastructure Housing Builds
        resolve_housing_infrastructure(self.agents, self.settlements)
        
        # 7. Labor Resource Extraction
        resolve_resource_production(self.world, self.agents, self.tech_registry)
        
        # 8. Technology Innovation
        cohort_cache = {}
        for cohort in self.agents.cohorts.values():
            if cohort.settlement_id:
                cohort_cache[cohort.settlement_id] = cohort_cache.get(cohort.settlement_id, 0) + cohort.count

        for s_id, settlement in self.settlements.settlements.items():
            if not settlement.active:
                continue
            state = self.tech_registry.get_state(s_id)
            state.knowledge += cohort_cache.get(s_id, 0) * 0.05
            
        self.tech_registry.resolve_innovation(self.settlements, self.current_tick)
        
        # 9. Resource Consumption & Allocation Processing
        resolve_food_and_health(self.world, self.agents)
        
        # 10. Ecosystem Regeneration
        self.world.tick_ecosystem(self.agents)
        
        # 11. Demographics
        resolve_birth_and_death(self.agents, self.current_tick)

        # 12. Graph Auditing
        for s_id, s in self.settlements.settlements.items():
            if s_id not in pre_step_active:
                self.history.record_event(self.current_tick, "FOUNDING", s.home_x, s.home_y, f"The settlement of {s.name} was established.")
            elif pre_step_active[s_id] and not s.active:
                self.history.record_event(self.current_tick, "ABANDONMENT", s.home_x, s.home_y, f"The settlement of {s.name} faded into historical ruins.")

    def run(self, ticks: int) -> None:
        print(f"--- Advancing timeline by {ticks} ticks ---")
        start_time = time.time()
        for _ in range(ticks):
            self.step()
            if self.current_tick % 100 == 0:
                summary = self.get_summary()
                print(f"[Tick {summary['tick']:04d}] Pop: {summary['combined_population']} | Settlements: {summary['active_settlements']}")
        elapsed = time.time() - start_time
        print(f"✓ Completed {ticks} ticks in {elapsed:.2f}s.")

    def get_summary(self) -> dict:
        living_count = len(self.agents.living_agents())
        cohort_population = sum(c.count for c in self.agents.cohorts.values())
        active_settlements_count = sum(1 for s in self.settlements.settlements.values() if s.active)
        return {
            "tick": self.current_tick,
            "active_settlements": active_settlements_count,
            "combined_population": living_count + cohort_population
        }
