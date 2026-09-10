"""
civsim/agents.py
Persistent individual agents and compressed demographic cohorts.
Provides the data architecture for dynamic resolution scaling.
"""

import random
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
OLD_AGE_ONSET = 50    
OLD_AGE_MAX = 80       


class Resolution(Enum):
    COMPRESSED = "compressed" 
    LOW = "low"               
    MEDIUM = "medium" 
    HIGH = "high"     


@dataclass(slots=True)
class Agent:
    id: str
    generation: int
    x: int
    y: int
    sex: str                  
    age: int = 0
    alive: bool = True
    health: float = STARTING_HEALTH
    resolution: Resolution = Resolution.LOW
    death_tick: int | None = None
    death_cause: str | None = None
    settlement_id: str | None = None
    
    # Phase 2 Social-Environmental Extensions
    hazard_experience: float = 0.0   # Adaptive memory scalar from surviving wilderness exposure
    housing_quality: float = 1.0     # Mitigates environment/crowding degradation factors

    def is_fertile(self) -> bool:
        return (
            self.alive 
            and self.sex == "F"
            and self.resolution != Resolution.COMPRESSED 
            and isinstance(self.age, (int, float))
            and MIN_BREEDING_AGE <= self.age <= MAX_BREEDING_AGE
        )

    def die(self, tick: int, cause: str) -> None:
        self.alive = False
        self.death_tick = tick
        self.death_cause = cause


@dataclass
class DemographicCohort:
    x: int
    y: int
    count: int = 0
    total_age: float = 0.0
    avg_health: float = STARTING_HEALTH
    settlement_id: str | None = None
    generation: int = 0


class AgentRegistry:
    def __init__(self):
        self._counter = count(1)
        self.agents: dict[str, Agent] = {}
        self.cohorts: dict[tuple[int, int], DemographicCohort] = {}

    def create_agent(self, generation: int, x: int, y: int) -> Agent:
        agent_id = f"AGT-{generation}-{next(self._counter)}"
        chosen_sex = random.choice(["M", "F"])
        agent = Agent(id=agent_id, generation=generation, x=x, y=y, sex=chosen_sex)
        self.agents[agent_id] = agent
        return agent

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.id] = agent

    def get(self, agent_id: str) -> Agent:
        return self.agents[agent_id]

    def living_agents(self) -> list[Agent]:
        return [a for a in self.agents.values() if a.alive and a.resolution != Resolution.COMPRESSED]

    def raw_living_agents(self) -> list[Agent]:
        return [a for a in self.agents.values() if a.alive]

    def tick(self) -> None:
        for agent in self.agents.values():
            if agent.alive:
                if isinstance(agent.age, (int, float)):
                    agent.age += 1
