"""
civsim/settlements.py
Settlements: persistent group affiliations that emerge from sustained
population density, with immersive random naming and tribal leadership seats.
"""

import random
from dataclasses import dataclass, field
from itertools import count
from collections import defaultdict
from civsim.agents import AgentRegistry, Resolution

SETTLEMENT_RADIUS = 2          
FOUNDING_MIN_POPULATION = 6    
FOUNDING_MIN_DURATION = 10     
ABANDONMENT_GRACE_TICKS = 5    
MAX_SETTLEMENT_VACANCY_TICKS = 20 

# EXPANDED LIBRARY: A vast collection of thematic prefixes and suffixes to fuel thousands of unique combinations
PREFIXES = [
    "Oak", "Ember", "River", "Dawn", "Shadow", "Stone", "Iron", "Storm", "Silver", "Winter", 
    "Clay", "Moss", "Ash", "Black", "Gold", "Frost", "Thorn", "Wild", "Mist", "Flint", 
    "Raven", "Wolf", "Deer", "Bear", "Hawk", "Pine", "Elder", "Cedar", "Gale", "Brook", 
    "Amber", "Copper", "Dusk", "Bright", "Cold", "Grim", "High", "Low", "North", "South", 
    "East", "West", "Red", "Blue", "Green", "White", "Heath", "Fen", "Moor", "Crag"
]

SUFFIXES = [
    "haven", "fall", "bend", "reach", "crest", "hold", "wood", "crag", "vale", "shore", 
    "ridge", "brook", "glen", "ford", "mill", "rock", "peak", "wood", "field", "dale", 
    "marsh", "moor", "spring", "well", "port", "gate", "keep", "tower", "fort", "burgh", 
    "ton", "ham", "stead", "shire", "holt", "thwaite", "hurst", "den", "comb", "cote"
]


def _within_radius(x: int, y: int, cx: int, cy: int, r: int) -> bool:
    return max(abs(x - cx), abs(y - cy)) <= r


@dataclass
class Settlement:
    id: str
    name: str                                              
    home_x: int
    home_y: int
    founded_tick: int
    leader_id: str | None = None                           
    member_ids: set[str] = field(default_factory=set)
    absence: dict[str, int] = field(default_factory=dict)  
    vacancy_ticks: int = 0                                 
    active: bool = True                                    


class SettlementRegistry:
    def __init__(self):
        self._counter = count(1)
        self.settlements: dict[str, Settlement] = {}
        self.formation_streaks: dict[tuple[int, int], int] = {}

    def found_settlement(self, x: int, y: int, current_tick: int) -> Settlement:
        settlement_id = f"STL-{next(self._counter)}"
        
        # Generate an immersive, non-repetitive historical name from the expanded library
        name_attempt = f"{random.choice(PREFIXES)}{random.choice(SUFFIXES)}"
        existing_names = {s.name for s in self.settlements.values()}
        while name_attempt in existing_names:
            name_attempt = f"{random.choice(PREFIXES)}{random.choice(SUFFIXES)}"
            
        settlement = Settlement(id=settlement_id, name=name_attempt, home_x=x, home_y=y, founded_tick=current_tick)
        self.settlements[settlement_id] = settlement
        return settlement


def resolve_settlements(agents: AgentRegistry, registry: SettlementRegistry, current_tick: int) -> None:
    living = agents.raw_living_agents()
    active_settlements = [s for s in registry.settlements.values() if s.active]

    # --- 1. EXISTING SETTLEMENTS: HYSTERESIS & PASSIVE JOINING ---
    for settlement in active_settlements:
        for agent in living:
            if agent.settlement_id != settlement.id:
                continue
            if _within_radius(agent.x, agent.y, settlement.home_x, settlement.home_y, SETTLEMENT_RADIUS):
                settlement.absence[agent.id] = 0
            else:
                settlement.absence[agent.id] = settlement.absence.get(agent.id, 0) + 1
                if settlement.absence[agent.id] > ABANDONMENT_GRACE_TICKS:
                    agent.settlement_id = None
                    settlement.member_ids.discard(agent.id)
                    if agent.id in settlement.absence:
                        del settlement.absence[agent.id]

        for agent in living:
            if agent.settlement_id is not None:
                continue
            if _within_radius(agent.x, agent.y, settlement.home_x, settlement.home_y, SETTLEMENT_RADIUS):
                agent.settlement_id = settlement.id
                settlement.member_ids.add(agent.id)
                settlement.absence[agent.id] = 0

    # --- 2. GHOST TOWN DETECTION & TRIBAL LEADERSHIP PROMOTION CONTROLS ---
    for settlement in active_settlements:
        living_ids = {a.id for a in living}
        settlement.member_ids &= living_ids
        
        local_cohort_pop = sum(c.count for pos, c in agents.cohorts.items() if getattr(c, 'settlement_id', None) == settlement.id)
        combined_town_size = len(settlement.member_ids) + local_cohort_pop
        
        if combined_town_size == 0:
            settlement.vacancy_ticks += 1
            if settlement.vacancy_ticks >= MAX_SETTLEMENT_VACANCY_TICKS:
                settlement.active = False 
        else:
            settlement.vacancy_ticks = 0
            
            # LEADERSHIP EVALUATION: Ensure the city has a living political anchor
            current_leader = agents.agents.get(settlement.leader_id) if settlement.leader_id else None
            if not current_leader or not current_leader.alive or current_leader.settlement_id != settlement.id:
                candidates = [a for a in living if a.settlement_id == settlement.id and a.resolution != Resolution.COMPRESSED]
                if candidates:
                    oldest_candidate = max(candidates, key=lambda a: a.age)
                    settlement.leader_id = oldest_candidate.id
                    # Promote leader to HIGH resolution tracking mode
                    oldest_candidate.resolution = Resolution.HIGH

    # --- 3. OPTIMIZED NEW FORMATION ---
    unaffiliated = [a for a in living if a.settlement_id is None]
    
    agent_counts = defaultdict(int)
    for a in unaffiliated:
        agent_counts[(a.x, a.y)] += 1
    for pos, cohort in agents.cohorts.items():
        if cohort.settlement_id is None:
            agent_counts[pos] += cohort.count

    if not agent_counts:
        registry.formation_streaks.clear()
        return

    density = {}
    seed_tiles = set(agent_counts.keys())
    
    for sx, sy in seed_tiles:
        total_in_radius = 0
        for (ax, ay), count_on_tile in agent_counts.items():
            if max(abs(ax - sx), abs(ay - sy)) <= SETTLEMENT_RADIUS:
                total_in_radius += count_on_tile
        density[(sx, sy)] = total_in_radius

    qualifying = {pos for pos, n in density.items() if n >= FOUNDING_MIN_POPULATION}
    for pos in list(registry.formation_streaks.keys()):
        if pos not in qualifying:
            del registry.formation_streaks[pos]
    for pos in qualifying:
        registry.formation_streaks[pos] = registry.formation_streaks.get(pos, 0) + 1

    ready = [pos for pos, streak in registry.formation_streaks.items() if streak >= FOUNDING_MIN_DURATION]
    for (sx, sy) in sorted(ready, key=lambda p: (-density[p], p)):
        founding_members = [
            a for a in unaffiliated
            if a.settlement_id is None and _within_radius(a.x, a.y, sx, sy, SETTLEMENT_RADIUS)
        ]
        if len(founding_members) < FOUNDING_MIN_POPULATION:
            continue
            
        settlement = registry.found_settlement(sx, sy, current_tick)
        for a in founding_members:
            a.settlement_id = settlement.id
            settlement.member_ids.add(a.id)
            settlement.absence[a.id] = 0
            
        if (sx, sy) in agents.cohorts:
            agents.cohorts[(sx, sy)].settlement_id = settlement.id
            
        if (sx, sy) in registry.formation_streaks:
            del registry.formation_streaks[(sx, sy)]
