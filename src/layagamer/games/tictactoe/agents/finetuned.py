"""All-legal-actions agent; shares its encoding with training."""
from time import perf_counter
from typing import Protocol
import random
from layagamer.agents.sampling import select_action

from layagamer.agents import Decision
from ..engine import Board

ENCODING_VERSION = "tictactoe-board-v1"


class Backend(Protocol):
    def predict(self, state: dict, questions: dict) -> dict: ...


def build_request(board: Board) -> tuple[dict, dict]:
    if board.finished:
        raise ValueError("No decision on a finished board")
    state = {
        "game": "tic-tac-toe",
        "you": board.turn,
        "board": [list(board.cells[i:i + 3]) for i in (0, 3, 6)],
        "numbering": "1 to 9, left to right, top to bottom; '.' is empty.",
        "rules": "X starts. Alternate placing marks. Three in a row, column, or diagonal wins. Otherwise a full board draws.",
    }
    return state, {"move": {
        "type": "choice", "instructions": "Choose a move to win or draw tic-tac-toe.",
        "criteria": {m: f"Place {board.turn} in square {m}." for m in board.legal_moves},
    }}


class FinetunedAgent:
    def __init__(self, checkpoint: str, *, device: str | None = None,
                 backend: Backend | None = None, temperature: float = 0.5,
                 seed: int | None = None) -> None:
        self.checkpoint = checkpoint
        self.device = device
        self.backend = backend
        self.temperature = temperature
        self.rng = random.Random(seed)

    def decide(self, observation: Board) -> Decision:
        state, questions = build_request(observation)
        if self.backend is None:
            from laya import Agent
            self.backend = Agent(self.checkpoint, device=self.device)
        started = perf_counter()
        result = self.backend.predict(state, questions)
        elapsed = (perf_counter() - started) * 1000
        move, selection = select_action(result["answers"]["move"],
                                        list(observation.legal_moves), self.rng, self.temperature)
        return Decision(move, {
            "agent": "tictactoe-finetuned", "checkpoint": self.checkpoint,
            "encoding_version": ENCODING_VERSION, "latency_ms": elapsed,
            "selection": selection,
            "harness_aids": [], "state": state, "questions": questions, "result": result,
        })
