"""
civsim/culture.py
Implements Phase 3 Cultural Drift and Ideological Trait Mutation.
Gives newly founded colonies unique social identities that alter their behavior.
"""

import random

CULTURE_TYPES = ["COOPERATIVE", "ISOLATIONIST", "MILITARISTIC"]


class CultureRegistry:
    def __init__(self):
        self.settlement_cultures: dict[str, str] = {}

    def get_culture(self, settlement_id: str) -> str:
        """Returns the active ideology type of a town, defaulting to standard cooperative values."""
        if settlement_id not in self.settlement_cultures:
            self.settlement_cultures[settlement_id] = "COOPERATIVE"
        return self.settlement_cultures[settlement_id]

    def mutate_culture_for_split(self, parent_id: str, child_id: str) -> str:
        """Derives a new colony's social values from its parent with a chance for structural drift."""
        parent_culture = self.get_culture(parent_id)
        
        # 30% chance for the splinter colony to drift into a completely different social ideology
        if random.random() < 0.30:
            mutated_culture = random.choice([c for c in CULTURE_TYPES if c != parent_culture])
        else:
            mutated_culture = parent_culture
            
        self.settlement_cultures[child_id] = mutated_culture
        return mutated_culture
