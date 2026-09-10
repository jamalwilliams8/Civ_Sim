"""
The single source of randomness for the entire simulation.

Rule: nothing outside this module ever calls `random` or `numpy.random`
directly. Every subsystem gets its own named child RNG derived from the
master seed, so adding a new subsystem later never shifts the random
sequence that existing subsystems depend on.
"""

import hashlib
import random


class SimRNG:
    def __init__(self, master_seed: int):
        self.master_seed = master_seed
        self._streams: dict[str, random.Random] = {}

    def stream(self, name: str) -> random.Random:
        """
        Return a dedicated random.Random for a named subsystem
        (e.g. 'population', 'hazard', 'weather'). Each stream is
        seeded deterministically from (master_seed, name), so:
          - the same master seed always reproduces the same run
          - subsystems never interfere with each other's draws
        """
        if name not in self._streams:
            key = f"{self.master_seed}:{name}".encode("utf-8")
            derived_seed = int(hashlib.sha256(key).hexdigest(), 16) & 0xFFFFFFFF
            self._streams[name] = random.Random(derived_seed)
        return self._streams[name]