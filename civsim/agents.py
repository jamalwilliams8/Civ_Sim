"""
civsim/agents.py
Combined Engine File: Holds system-wide thresholds, individual Agent entities, 
DemographicCohort buckets, and the AgentRegistry execution system.
Natively fixed to ensure explicit None checks do not wipe out agent gender states.
"""
import random

# System configuration constants
FOOD_NEED_PER_TICK = 1.0
STARTING_HEALTH = 100.0
MAX_HEALTH = 100.0
HEALTH_GAIN_IF_FED = 5.0
HEALTH_LOSS_IF_UNFED = 10.0
MIN_BREEDING_AGE = 18
MAX_BREEDING_AGE = 50

class Resolution:
    INDIVIDUAL = 1
    COMPRESSED = 2
    HIGH = 1
    LOW = 1

class Agent:
    def __init__(self, id, generation, x, y, **kwargs):
        self.id = id
        self.generation = generation
        self.x = x
        self.y = y
        
        self.alive = kwargs.get("alive", True)
        self.age = kwargs.get("age", 0)
        self.health = kwargs.get("health", STARTING_HEALTH)
        self.wealth = kwargs.get("wealth", 0.0)
        self.intelligence = kwargs.get("intelligence", round(random.uniform(5.0, 15.0), 2))
        self.settlement_id = kwargs.get("settlement_id", None)
        self.occupation = kwargs.get("occupation", "FARMER")
        self.death_cause = kwargs.get("death_cause", None)
        
        incoming_res = kwargs.get("resolution", Resolution.INDIVIDUAL)
        self.resolution = Resolution.INDIVIDUAL if incoming_res in [Resolution.INDIVIDUAL, Resolution.LOW] else Resolution.COMPRESSED
            
        # FIX: Explicitly evaluate None values to prevent gender erasure bugs
        incoming_sex = kwargs.get("sex")
        self.sex = incoming_sex if incoming_sex is not None else random.choice(["M", "F"])
        
        self.grit = kwargs.get("grit", round(random.uniform(0.3, 1.0), 2))
        self.hardened_veteran = kwargs.get("hardened_veteran", False)

    def is_fertile(self) -> bool:
        if not self.alive: return False
        if self.sex != "F": return False
        return MIN_BREEDING_AGE <= self.age <= MAX_BREEDING_AGE

    def die(self, tick: int, cause: str) -> None:
        self.alive = False
        self.health = 0.0
        self.death_cause = cause
        self.death_tick = tick

class DemographicCohort:
    def __init__(self, count, x, y, generation=0, **kwargs):
        self.count = count
        self.x = x
        self.y = y
        self.generation = generation
        self.age = kwargs.get("age", 25)
        self.health = kwargs.get("health", STARTING_HEALTH)
        self.settlement_id = kwargs.get("settlement_id", None)
        self.occupation = kwargs.get("occupation", "FARMER")
        self.resolution = Resolution.COMPRESSED
        self.grit = kwargs.get("grit", 0.60)
        self.hardened_veteran = kwargs.get("hardened_veteran", False)

class AgentRegistry:
    def __init__(self):
        self.agents = {}
        self.cohorts = {}
        self.next_agent_id = 0

    def create_agent(self, generation, x, y, sex=None):
        agent_id = f"AGT-{generation}-{self.next_agent_id}"
        self.next_agent_id += 1
        start_age = random.randint(18, 30) if generation == 0 else 0
        new_agent = Agent(agent_id, generation, x, y, sex=sex, age=start_age, alive=True)
        self.agents[agent_id] = new_agent
        return new_agent

    def add_agent(self, agent) -> None:
        if agent and hasattr(agent, "id"):
            self.agents[agent.id] = agent

    def raw_living_agents(self):
        return [a for a in self.agents.values() if a.alive]

    def living_agents(self):
        return self.raw_living_agents()
