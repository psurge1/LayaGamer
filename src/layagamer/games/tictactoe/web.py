"""Translate this game's browser requests to its existing agents."""
from .agents.tactical import LayaPlayer
from layagamer.games.tictactoe.agents.finetuned import FinetunedAgent
from .engine import Board


class TicTacToeWeb:
    def __init__(self, tactical: LayaPlayer, finetuned: FinetunedAgent | None = None):
        self.tactical = tactical
        self.finetuned = finetuned

    def describe(self) -> dict:
        agents = [{"id": "tactical", "label": "Tactical Laya"}]
        if self.finetuned is not None:
            agents.insert(0, {"id": "finetuned", "label": "Fine-tuned Laya"})
        return {"id": "tictactoe", "label": "Tic-tac-toe", "agents": agents}

    def prepare(self, payload: dict) -> tuple[Board, str]:
        if not isinstance(payload.get("cells"), list):
            raise ValueError("Expected board cells")
        board = Board(tuple(payload["cells"]), payload.get("turn", "X"))
        if board.finished:
            raise ValueError("Game is already finished")
        agent = payload.get("agent", "tactical")
        if agent not in [entry["id"] for entry in self.describe()["agents"]]:
            raise ValueError("Unknown or unavailable agent")
        return board, agent

    def decide(self, prepared: tuple[Board, str]) -> dict:
        board, agent = prepared
        if agent == "finetuned":
            result = self.finetuned.decide(board)
            decision = {**result.metadata, "move": result.action}
        else:
            decision = {**self.tactical.choose(board), "agent": "tactical"}
        return {**decision, "legal_moves": list(board.legal_moves)}
