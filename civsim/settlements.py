"""
Settlements: persistent group affiliations that emerge from sustained
population density, with hysteresis so ordinary wandering doesn't
instantly strip membership (spec section 9, bug fix section 61).

Two responsibilities, run in order each tick:

1. EXISTING SETTLEMENTS: any current member who has drifted outside the
   settlement's radius gets an absence counter instead of being dropped
   immediately. Only sustained absence (> ABANDONMENT_GRACE_TICKS) costs
   membership. Any unaffiliated agent who wanders into range joins
   automatically -- settling in is passive, like the rest of movement.

2. NEW FORMATION: among agents with no settlement, track how many
   ticks in a row each candidate tile has sustained at least
   FOUNDING_MIN_POPULATION unaffiliated agents within SETTLEMENT_RADIUS.
   Once a tile holds that streak for FOUNDING_MIN_DURATION ticks, a
   settlement is founded there and everyone currently in range joins.
   This is a density/duration threshold, not a scripted "settlement
   appears in Year X" -- it only happens where behavior actually
   produced a sustained cluster.
"""

from dataclasses import dataclass, field
from itertools import count

from civsim.agents import AgentRegistry

SETTLEMENT_RADIUS = 2          # Chebyshev distance counted as "in" the settlement
FOUNDING_MIN_POPULATION = 6    # unaffiliated agents required in radius to start a streak
FOUNDING_MIN_DURATION = 10     # consecutive ticks the density must hold before founding
ABANDONMENT_GRACE_TICKS = 5    # ticks a member may be absent before losing membership


def _within_radius(x: int, y: int, cx: int, cy: int, r: int) -> bool:
    return max(abs(x - cx), abs(y - cy)) <= r


@dataclass
class Settlement:
    id: str
    home_x: int
    home_y: int
    founded_tick: int
    member_ids: set[str] = field(default_factory=set)
    absence: dict[str, int] = field(default_factory=dict)  # agent_id -> consecutive absent ticks


class SettlementRegistry:
    """Owns every settlement that has ever formed. This is the only place settlements are created."""

    def __init__(self):
        self._counter = count(1)
        self.settlements: dict[str, Settlement] = {}
        self.formation_streaks: dict[tuple[int, int], int] = {}

    def found_settlement(self, x: int, y: int, current_tick: int) -> Settlement:
        settlement_id = f"STL-{next(self._counter)}"
        settlement = Settlement(id=settlement_id, home_x=x, home_y=y, founded_tick=current_tick)
        self.settlements[settlement_id] = settlement
        return settlement


def resolve_settlements(agents: AgentRegistry, registry: SettlementRegistry, current_tick: int) -> None:
    living = agents.living_agents()

    # --- 1. existing settlements: presence, hysteresis, passive joining ---
    for settlement in list(registry.settlements.values()):
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
                    del settlement.absence[agent.id]

        for agent in living:
            if agent.settlement_id is not None:
                continue
            if _within_radius(agent.x, agent.y, settlement.home_x, settlement.home_y, SETTLEMENT_RADIUS):
                agent.settlement_id = settlement.id
                settlement.member_ids.add(agent.id)
                settlement.absence[agent.id] = 0

    # --- 2. new formation among whoever is still unaffiliated ---
    unaffiliated = [a for a in living if a.settlement_id is None]
    if not unaffiliated:
        registry.formation_streaks.clear()
        return

    seed_tiles = {(a.x, a.y) for a in unaffiliated}
    density = {
        (sx, sy): sum(1 for a in unaffiliated if _within_radius(a.x, a.y, sx, sy, SETTLEMENT_RADIUS))
        for (sx, sy) in seed_tiles
    }

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
        del registry.formation_streaks[(sx, sy)]