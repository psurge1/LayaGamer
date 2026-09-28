"""Immutable Minesweeper rules and visible-board deductions."""
from dataclasses import dataclass
from collections import deque

Point = tuple[int, int]


@dataclass(frozen=True)
class MinesweeperState:
    width: int
    height: int
    mines: frozenset[Point]
    revealed: frozenset[Point] = frozenset()
    flagged: frozenset[Point] = frozenset()
    exploded: Point | None = None

    def __post_init__(self) -> None:
        cells = {(x, y) for y in range(self.height) for x in range(self.width)}
        if not (4 <= self.width <= 20 and 4 <= self.height <= 20):
            raise ValueError("Minesweeper dimensions must be between 4 and 20")
        if not self.mines or not self.mines < cells:
            raise ValueError("Mine placement must leave playable cells")
        if not self.revealed <= cells or not self.flagged <= cells or self.revealed & self.flagged:
            raise ValueError("Invalid revealed or flagged cells")
        if self.exploded is not None and self.exploded not in self.mines:
            raise ValueError("Exploded cell must contain a mine")

    def neighbors(self, point: Point) -> tuple[Point, ...]:
        x, y = point
        return tuple((nx, ny) for ny in range(max(0, y - 1), min(self.height, y + 2))
                     for nx in range(max(0, x - 1), min(self.width, x + 2)) if (nx, ny) != point)

    def number(self, point: Point) -> int:
        return sum(neighbor in self.mines for neighbor in self.neighbors(point))

    @property
    def finished(self) -> bool:
        return self.exploded is not None or len(self.revealed) == self.width * self.height - len(self.mines)

    @property
    def won(self) -> bool:
        return self.finished and self.exploded is None

    def apply(self, action: str) -> "MinesweeperState":
        if self.finished: raise ValueError("Game is finished")
        kind, raw = action.split(":", 1)
        point = tuple(map(int, raw.split(",")))
        if len(point) != 2 or not (0 <= point[0] < self.width and 0 <= point[1] < self.height):
            raise ValueError("Invalid cell")
        if kind == "flag":
            if point in self.revealed: raise ValueError("Cannot flag a revealed cell")
            flags = set(self.flagged)
            if point in flags: flags.remove(point)
            else: flags.add(point)
            return MinesweeperState(self.width, self.height, self.mines, self.revealed, frozenset(flags))
        if kind != "reveal" or point in self.flagged or point in self.revealed:
            raise ValueError("Invalid reveal")
        if point in self.mines:
            return MinesweeperState(self.width, self.height, self.mines, self.revealed, self.flagged, point)
        revealed, queue = set(self.revealed), deque([point])
        while queue:
            cell = queue.popleft()
            if cell in revealed or cell in self.flagged or cell in self.mines: continue
            revealed.add(cell)
            if self.number(cell) == 0: queue.extend(self.neighbors(cell))
        return MinesweeperState(self.width, self.height, self.mines, frozenset(revealed), self.flagged)

    def visible(self) -> list[list[str]]:
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                point = x, y
                row.append("F" if point in self.flagged else str(self.number(point)) if point in self.revealed else "#")
            rows.append(row)
        return rows

    def deductions(self) -> dict[Point, dict]:
        hidden = {(x, y) for y in range(self.height) for x in range(self.width)} - self.revealed - self.flagged
        global_risk = max(0, len(self.mines) - len(self.flagged)) / max(1, len(hidden))
        facts = {}
        for point in hidden:
            constraints, safe, mine = [], False, False
            for neighbor in self.neighbors(point):
                if neighbor not in self.revealed: continue
                adjacent = self.neighbors(neighbor)
                unknown = [cell for cell in adjacent if cell not in self.revealed and cell not in self.flagged]
                remaining = self.number(neighbor) - sum(cell in self.flagged for cell in adjacent)
                if point in unknown and unknown:
                    constraints.append(max(0, remaining) / len(unknown))
                    safe |= remaining == 0
                    mine |= remaining == len(unknown)
            risk = 0.0 if safe else 1.0 if mine else max(constraints) if constraints else global_risk
            facts[point] = {"provably_safe": safe, "certain_mine": mine, "estimated_risk": round(risk, 4),
                            "adjacent_revealed": sum(n in self.revealed for n in self.neighbors(point))}
        return facts
