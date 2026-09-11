"""
civsim/agents.py
Core entity blueprint definition for individual simulation actors and cohort buckets.
Contains system-wide survival thresholds and parameters.
"""
import random

# System configuration constants
FOOD_NEED_PER_TICK = 1.0
STARTING_HEALTH = 100.0

class Resolution:
    INDIVIDUAL = 1
    COMPRESSED = 2

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
        
        # Birth metrics
        self.sex = sex if sex is not None else random.choice(["M", "F"])
        self.grit = round(random.uniform(0.3, 1.0), 2)
        self.hardened_veteran = False

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
