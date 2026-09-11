"""
civsim/agent_registry.py
Manages the active collections, lookups, and generation metrics of individual agents.
"""
import random
from civsim.agents import Agent
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
