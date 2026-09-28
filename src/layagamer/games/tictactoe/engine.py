"""Immutable tic-tac-toe state, independent of the inference backend."""
from dataclasses import dataclass

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8),
         (0, 4, 8), (2, 4, 6))


@dataclass(frozen=True)
class Board:
    cells: tuple[str, ...] = (".",) * 9
    turn: str = "X"

    def __post_init__(self):
        if len(self.cells) != 9 or any(c not in (".", "X", "O") for c in self.cells):
            raise ValueError("Expected nine cells containing '.', 'X', or 'O'")
        x, o = self.cells.count("X"), self.cells.count("O")
        if x - o not in (0, 1) or self.turn != ("X" if x == o else "O"):
            raise ValueError("Invalid mark counts or turn")
        winners = {self.cells[a] for a, b, c in LINES
                   if self.cells[a] != "." and self.cells[a] == self.cells[b] == self.cells[c]}
        if len(winners) > 1 or ("X" in winners and x != o + 1) or ("O" in winners and x != o):
            raise ValueError("Invalid winning board")

    @property
    def winner(self) -> str | None:
        for a, b, c in LINES:
            if self.cells[a] != "." and self.cells[a] == self.cells[b] == self.cells[c]:
                return self.cells[a]
        return None

    @property
    def finished(self) -> bool:
        return self.winner is not None or "." not in self.cells

    @property
    def legal_moves(self) -> tuple[str, ...]:
        return () if self.finished else tuple(str(i + 1) for i, c in enumerate(self.cells) if c == ".")

    def play(self, move: str) -> "Board":
        if move not in self.legal_moves:
            raise ValueError(f"Illegal move: {move!r}")
        cells = list(self.cells)
        cells[int(move) - 1] = self.turn
        return Board(tuple(cells), "O" if self.turn == "X" else "X")

    def render(self) -> str:
        labels = [str(i + 1) if c == "." else c for i, c in enumerate(self.cells)]
        return "\n---------\n".join(" | ".join(labels[i:i + 3]) for i in (0, 3, 6))

    def state(self) -> dict:
        if self.finished:
            raise ValueError("No decision on a finished board")
        return {
            "game": "tic-tac-toe",
            "rules": "X moves first. Alternate placing one mark in an empty square. "
                     "Three matching marks in a row, column, or diagonal wins. "
                     "A full board without a winner is a draw. Occupied squares are illegal.",
            "you": self.turn,
            "opponent": "O" if self.turn == "X" else "X",
            "turn": "It is your turn. Choose one legal move to win or avoid losing.",
            "numbering": "1–9 run left to right, top to bottom. '.' means empty.",
            "board": [list(self.cells[i:i + 3]) for i in (0, 3, 6)],
            "squares": {str(i + 1): c for i, c in enumerate(self.cells)},
            "legal_moves": list(self.legal_moves),
        }
