"""
Central configuration for the simulation.
Nothing else in the codebase should hardcode a tunable number —
it should import it from here, so behavior is data-driven and
a config change doesn't require touching simulation logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimConfig:
    seed: int = 18472931          # master RNG seed — determinism depends on this
    ticks_per_year: int = 1       # 1 tick = 1 year to start; we can change resolution later
    starting_population: int = 20 # size of the founding group

    def as_dict(self) -> dict:
        return self.__dict__.copy()