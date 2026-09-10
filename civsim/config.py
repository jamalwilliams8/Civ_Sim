"""
Central configuration for the simulation.
Nothing else in the codebase should hardcode a tunable number —
it should import it from here, so behavior is data-driven and
a config change doesn't require touching simulation logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimConfig:
    # --- Master Engine Seeds ---
    seed: int = 18472931          # Master RNG seed — determinism depends on this
    ticks_per_year: int = 1       # 1 tick = 1 year baseline scale
    
    # --- Map Matrix Dimensions ---
    world_width: int = 100        # Expanded map grid dimension width
    world_height: int = 100       # Expanded map grid dimension height
    starting_population: int = 50 # Larger founding group to settle a wider map

    def as_dict(self) -> dict:
        return self.__dict__.copy()
