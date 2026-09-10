"""
Persistent individual agents: identity, aging, food/health, death, and
simulation resolution. Every agent is a real, inspectable object regardless
of resolution — resolution controls how much decision logic runs on them,
not whether they exist as individuals.
"""

from dataclasses import dataclass
from enum import Enum
from itertools import count


FOOD_NEED_PER_TICK = 1.0
STARTING_HEALTH = 10.0
MAX_HEALTH = 10.0
HEALTH_GAIN_IF_FED = 1.0
HEALTH_LOSS_IF_UNFED = 3.0
MIN_BREEDING_AGE = 15
MAX_BREEDING_AGE = 45
OLD_AGE_ONSET = 50    # age at which old-age mortality risk begins
OLD_AGE_MAX = 80       # age at which death from old age becomes certain


class Resolution(Enum):
    LOW = "low"       # ordinary population: identity + basic stats only
    MEDIUM = "medium" # locally relevant: gets goals/relationships later
    HIGH = "high"     # historically significant: full decision detail later


@dataclass(slots=True)
class Agent:
    id: str
    generation: int
    x: int
    y: int
    age: int = 0
    alive: bool = True
    health: float = STARTING_HEALTH
    resolution: Resolution = Resolution.LOW
    death_tick: int | None = None
    death_cause: str | None = None
    settlement_id: str | None = None

    def is_fertile(self) -> bool:
        return self.alive and MIN_BREEDING_AGE <= self.age <= MAX_BREEDING_AGE

    def die(self, tick: int, cause: str) -> None:
        self.alive = False
        self.death_tick = tick
        self.death_cause = cause


class AgentRegistry:
    """Owns every agent that has ever existed. This is the only place agents are created."""

    def __init__(self):
        self._counter = count(1)
        self.agents: dict[str, Agent] = {}

    def create_agent(self, generation: int, x: int, y: int) -> Agent:
        agent_id = f"AGT-{generation}-{next(self._counter)}"
        agent = Agent(id=agent_id, generation=generation, x=x, y=y)
        self.agents[agent_id] = agent
        return agent

    def get(self, agent_id: str) -> Agent:
        """Look up any agent by ID, regardless of resolution — this is what
        makes 'click any of the 100k and see a real individual' possible."""
        return self.agents[agent_id]

    def living_agents(self) -> list[Agent]:
        return [a for a in self.agents.values() if a.alive]

    def by_resolution(self, resolution: Resolution) -> list[Agent]:
        return [a for a in self.agents.values() if a.alive and a.resolution == resolution]

    def tick(self) -> None:
        for agent in self.agents.values():
            if agent.alive:
                agent.age += 1