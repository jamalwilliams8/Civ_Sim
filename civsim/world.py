"""
The physical world: a grid of tiles, each with terrain and resources.
No agents live here yet — this step is just the space they'll occupy.
"""

from dataclasses import dataclass, field


@dataclass
class Tile:
    x: int
    y: int
    terrain: str = "plains"       # e.g. "plains", "forest", "water"
    food_wild: float = 10.0       # current wild food available on this tile
    max_food_wild: float = 10.0   # ceiling this tile regenerates back toward
    regen_rate: float = 0.5       # food regrown per tick, up to max_food_wild


class World:
    def __init__(self, width: int, height: int, rng):
        self.width = width
        self.height = height
        self.rng = rng  # a random.Random stream, e.g. sim_rng.stream("world")
        self.tiles: dict[tuple[int, int], Tile] = {}
        self._generate()

    def _generate(self) -> None:
        """Create every tile in the grid with a randomly chosen terrain type."""
        terrain_choices = ["plains", "forest", "water"]
        for x in range(self.width):
            for y in range(self.height):
                terrain = self.rng.choice(terrain_choices)
                self.tiles[(x, y)] = Tile(x=x, y=y, terrain=terrain)

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[(x, y)]

    def tick(self) -> None:
        """Advance every tile by one tick: regenerate wild food toward its max."""
        for tile in self.tiles.values():
            if tile.food_wild < tile.max_food_wild:
                tile.food_wild = min(
                    tile.max_food_wild,
                    tile.food_wild + tile.regen_rate,
                )