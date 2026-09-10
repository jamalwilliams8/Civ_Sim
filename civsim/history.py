"""
civsim/history.py
Implements the Phase 4 Causality Engine. Builds an efficient directed graph
of significant historical events so users can trace "Why did this happen?".
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SimEvent:
    id: str                         # Unique format e.g. EVT-1042
    tick: int                       # Timestamp of occurrence
    event_type: str                 # "FOUNDING", "MIGRATION_SPLIT", "INNOVATION", "ABANDONMENT"
    location: tuple[int, int]
    description: str
    parent_ids: list[str] = field(default_factory=list)  # Direct links to causing factor IDs
    metadata: dict[str, Any] = field(default_factory=dict)


class CausalityEngine:
    def __init__(self):
        self.events: dict[str, SimEvent] = {}
        self._counter = 0

    def record_event(self, tick: int, event_type: str, x: int, y: int, description: str, parent_ids: Optional[list[str]] = None, metadata: Optional[dict] = None) -> str:
        """Logs a significant historical event node and returns its unique ID string."""
        self._counter += 1
        event_id = f"EVT-{self._counter:05d}"
        
        parents = parent_ids if parent_ids is not None else []
        meta = metadata if metadata is not None else {}
        
        event_node = SimEvent(
            id=event_id,
            tick=tick,
            event_type=event_type,
            location=(x, y),
            description=description,
            parent_ids=parents,
            metadata=meta
        )
        self.events[event_id] = event_node
        return event_id

    def trace_chain_backward(self, event_id: str, depth: int = 0, visited: Optional[set] = None) -> list[str]:
        """Recursively traces parent causes backward through history to compile an explanation string list."""
        if visited is None:
            visited = set()
            
        if event_id not in self.events or event_id in visited:
            return []
            
        visited.add(event_id)
        event = self.events[event_id]
        indent = "  " * depth
        
        lines = [f"{indent}[Yr {event.tick}] {event.description} ({event.id})"]
        
        for parent_id in event.parent_ids:
            lines.extend(self.trace_chain_backward(parent_id, depth + 1, visited))
            
        return lines
