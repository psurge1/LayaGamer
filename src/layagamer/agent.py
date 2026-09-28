"""Observation and legal actions → Laya choice → validated action."""
from time import perf_counter
from typing import Any
import random
from layagamer.agents.sampling import select_action

from layagamer.tictactoe import Board
from layagamer.context import consequences, describe, winning_squares


class LayaPlayer:
    def __init__(self, *, device: str | None = None, router: Any = None,
                 temperature: float = 0.5, seed: int | None = None):
        self.router = router
        self.device = device
        self.temperature = temperature
        self.rng = random.Random(seed)

    @staticmethod
    def request(board: Board) -> tuple[dict, dict]:
        state = board.state()
        facts = consequences(board)
        state["action_consequences"] = facts
        winning_moves = [move for move, fact in facts.items() if fact["wins_now"]]
        opponent = state["opponent"]
        threats = winning_squares(board.cells, opponent)
        blocking_moves = [move for move, fact in facts.items()
                          if threats and not fact["opponent_can_win_next_at"]]
        # A block must remove every immediate threat. If no complete block
        # exists, offer threat squares as partial blocks and expose the danger.
        partial_blocks = [move for move in board.legal_moves if move in threats]
        candidates = winning_moves or blocking_moves or partial_blocks or list(board.legal_moves)
        state["action_constraint"] = (
            "immediate_win" if winning_moves else "block_opponent_win" if blocking_moves
            else "partial_block" if partial_blocks else "none"
        )
        state["opponent_winning_squares"] = threats
        state["available_choices"] = candidates
        state["decision_priority"] = (
            "An immediate win ends the game before the opponent can move. "
            "Priority: take an immediate win, otherwise block an opponent's immediate win, "
            "otherwise consider all legal moves. Multiple threats may make a complete block impossible."
        )
        criteria = {}
        for move in candidates:
            row, col = divmod(int(move) - 1, 3)
            criteria[move] = (f"Place {board.turn} in square {move}, row {row + 1}, column {col + 1}. "
                              + describe(facts[move]))
        return state, {"move": {
            "type": "choice",
            "instructions": "Choose the best legal tic-tac-toe move for your mark. "
                            "Win if possible; otherwise block an opponent's immediate win "
                            "and aim to win or draw. Use the supplied action consequences. "
                            "Prefer an immediate win, then avoid immediate loss, then create "
                            "your own fork or prevent an unanswered opponent fork. "
                            "A fork means two distinct winning squares; one block cannot cover both.",
            "criteria": criteria,
        }}

    def choose(self, board: Board) -> dict:
        state, questions = self.request(board)
        if self.router is None:
            from laya import Router
            self.router = Router(**({"device": self.device} if self.device else {}))
        started = perf_counter()
        result = self.router.predict(state, questions, model="english")
        latency_ms = (perf_counter() - started) * 1000
        move, selection = select_action(result["answers"]["move"],
                                        list(questions["move"]["criteria"]), self.rng, self.temperature)
        return dict(move=move, selection=selection, latency_ms=latency_ms,
                    state=state, questions=questions, result=result)
