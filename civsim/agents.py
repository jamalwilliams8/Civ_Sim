"""
civsim/agents.py
Combined Engine File: Holds system-wide thresholds, individual Agent entities, 
DemographicCohort buckets, and the AgentRegistry execution system.
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
    
    # Dual-mapping aliases to support backward compatibility with population math
    HIGH = 1
    LOW = 2

class Agent:
    def __init__(self, id, generation, x, y, sex=None):
        self.id = id
        self.generation = generation
        self.x = x
        self.y = y
        self.alive = True
        self.age = 0
        self.health = STARTING_HEALTH
        self.wealth = 0.0
        self.intelligence = round(random.uniform(5.0, 15.0), 2)
        self.settlement_id = None
        self.occupation = "FARMER"
        self.death_cause = None
        self.resolution = Resolution.INDIVIDUAL
        
        # Birth traits
        self.sex = sex if sex is not None else random.choice(["M", "F"])
        self.grit = round(random.uniform(0.3, 1.0), 2)
        self.hardened_veteran = False

    def is_fertile(self) -> bool:
        if not self.alive: return False
        if self.sex != "F": return False
        return MIN_BREEDING_AGE <= self.age <= MAX_BREEDING_AGE

class DemographicCohort:
    def __init__(self, count, x, y, generation=0):
        self.count = count
        self.x = x
        self.y = y
        self.generation = generation
        self.age = 25
        self.health = STARTING_HEALTH
        self.settlement_id = None
        self.occupation = "FARMER"
        self.resolution = Resolution.COMPRESSED

class AgentRegistry:
    def __init__(self):
        self.agents = {}
        self.cohorts = {}
        self.next_agent_id = 0

    def create_agent(self, generation, x, y, sex=None):
        agent_id = f"AGT-{generation}-{self.next_agent_id}"
        self.next_agent_id += 1
        new_agent = Agent(agent_id, generation, x, y, sex)
        self.agents[agent_id] = new_agent
        return new_agent

    def raw_living_agents(self):
        return [a for a in self.agents.values() if a.alive]

    def living_agents(self):
        return self.raw_living_agents()
