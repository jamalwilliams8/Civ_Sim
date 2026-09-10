"""
The tick engine: owns the world and agents, advances simulated time.
"""

from civsim.config import SimConfig
from civsim.rng import SimRNG
from civsim.world import World
from civsim.agents import AgentRegistry
from civsim.behavior import resolve_movement
from civsim.population import resolve_food_and_health, resolve_births, resolve_old_age
from civsim.resources import resolve_resource_production
from civsim.settlements import SettlementRegistry, resolve_settlements


class Simulation:
    def __init__(self, config: SimConfig, width: int = 10, height: int = 10):
        self.config = config
        self.rng = SimRNG(config.seed)
        self.world = World(width, height, self.rng.stream("world"))
        self.agents = AgentRegistry()
        self.settlements = SettlementRegistry()
        self.current_tick = 0

        self._spawn_founding_population()

    def _spawn_founding_population(self) -> None:
        spawn_rng = self.rng.stream("spawn")
        cx, cy = self.world.width // 2, self.world.height // 2
        for _ in range(self.config.starting_population):
            x = min(max(cx + spawn_rng.randint(-2, 2), 0), self.world.width - 1)
            y = min(max(cy + spawn_rng.randint(-2, 2), 0), self.world.height - 1)
            self.agents.create_agent(generation=0, x=x, y=y)

    def step(self) -> None:
        """Advance the simulation by exactly one tick, in a fixed, explainable order."""
        self.world.tick()
        self.agents.tick()
        resolve_movement(self.world, self.agents)
        resolve_settlements(self.agents, self.settlements, self.current_tick)
        resolve_resource_production(self.world, self.agents)
        resolve_food_and_health(self.world, self.agents, self.current_tick)
        resolve_old_age(self.agents, self.rng.stream("aging"), self.current_tick)
        resolve_births(self.agents, self.rng.stream("population"), self.current_tick)
        self.current_tick += 1

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.step()