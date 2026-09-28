"""Deterministic minimax labels and symmetry-grouped splits."""
import argparse
from functools import cache
import hashlib
import json
from pathlib import Path

from .engine import Board
from layagamer.games.tictactoe.agents.finetuned import build_request, ENCODING_VERSION


@cache
def value(board: Board) -> int:
    if board.finished:
        return -1 if board.winner else 0
    return max(-value(board.play(move)) for move in board.legal_moves)


def canonical(board: Board) -> str:
    grids = []
    cells = board.cells
    for _ in range(4):
        grids.extend(("".join(cells), "".join(cells[r * 3 + 2 - c] for r in range(3) for c in range(3))))
        cells = tuple(cells[(2 - c) * 3 + r] for r in range(3) for c in range(3))
    return board.turn + min(grids)


def examples() -> list[dict]:
    seen = set()
    rows = []

    def visit(board: Board) -> None:
        if board in seen or board.finished:
            return
        seen.add(board)
        scores = {move: -value(board.play(move)) for move in board.legal_moves}
        best = [m for m, score in scores.items() if score == max(scores.values())]
        group = canonical(board)
        bucket = int(hashlib.sha256(group.encode()).hexdigest(), 16) % 10
        state, questions = build_request(board)
        rows.append({"encoding_version": ENCODING_VERSION, "group": group,
                     "split": "test" if bucket == 0 else "validation" if bucket == 1 else "train",
                     "cells": board.cells, "turn": board.turn, "state": state, "questions": questions,
                     "optimal_moves": best, "values": scores,
                     "target": {m: 1 / len(best) if m in best else 0 for m in scores}})
        for move in board.legal_moves:
            visit(board.play(move))

    visit(Board())
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = examples()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")
    print({split: sum(row["split"] == split for row in rows) for split in ("train", "validation", "test")})


if __name__ == "__main__":
    main()
