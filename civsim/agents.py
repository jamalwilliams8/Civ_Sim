"""
Persistent individual agents and compressed demographic cohorts.
Provides the data architecture for dynamic resolution scaling:
LOW resolution agents are optimized into Cohort blocks to protect scale.
"""

from dataclasses import dataclass, field
from enum import Enum
from itertools import count


FOOD_NEED_PER_TICK = 1.0
STARTING_HEALTH = 10.0
MAX_HEALTH = 10.0
HEALTH_GAIN_IF_FED = 1.0
HEALTH_LOSS_IF_UNFED = 3.0
MIN_BREEDING_AGE = 15
MAX_BREEDING_AGE = 45
OLD_AGE_ONSET = 50    
OLD_AGE_MAX = 80       


class Resolution(Enum):
    LOW = "low"       # Aggregated into fast demographic math cohorts
    MEDIUM = "medium" # Locally tracked agent objects
    HIGH = "high"     # Historically significant figures (Leaders/Inventors)


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


@dataclass
class DemographicCohort:
    """
    Compresses hundreds of LOW-resolution agents on a single tile into 
    one fast mathematical cohort block, preventing individual CPU loop chokes.
    """
    x: int
    y: int
    count: int = 0
    total_age: float = 0.0
    avg_health: float = STARTING_HEALTH
    settlement_id: str | None = None
    generation: int = 0


class AgentRegistry:
    """Owns every individual agent and compressed cohort inside the world."""

    def __init__(self):
        self._counter = count(1)
        self.agents: dict[str, Agent] = {}
        # Spatial tracker for optimized low-resolution blocks
        self.cohorts: dict[tuple[int, int], DemographicCohort] = {}

    def create_agent(self, generation: int, x: int, y: int) -> Agent:
        agent_id = f"AGT-{generation}-{next(self._counter)}"
        agent = Agent(id=agent_id, generation=generation, x=x, y=y)
        self.agents[agent_id] = agent
        return agent

    def get(self, agent_id: str) -> Agent:
        return self.agents[agent_id]

    def living_agents(self) -> list[Agent]:
        return [a for a in self.agents.values() if a.alive]

    def tick(self) -> None:
        """Ages tracked individual agents."""
        for agent in self.agents.values():
            if agent.alive:
                agent.age += 1
