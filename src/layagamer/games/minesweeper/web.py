"""Minesweeper browser adapter."""
from .agent import MinesweeperLayaAgent
from .engine import MinesweeperState


class MinesweeperWeb:
    def __init__(self, agent: MinesweeperLayaAgent): self.agent = agent
    def describe(self) -> dict:
        return {"id": "minesweeper", "label": "Minesweeper", "agents": [{"id": "tactical", "label": "Tactical Laya"}]}
    def prepare(self, payload: dict) -> MinesweeperState:
        if payload.get("agent", "tactical") != "tactical": raise ValueError("Unknown agent")
        points = lambda name: frozenset(tuple(point) for point in payload.get(name, []))
        state = MinesweeperState(payload.get("width", 8), payload.get("height", 8), points("mines"),
                                 points("revealed"), points("flagged"))
        if state.finished: raise ValueError("Game is finished")
        return state
    def decide(self, state: MinesweeperState) -> dict:
        decision = self.agent.decide(state)
        return {**decision.metadata, "move": decision.action,
                "legal_moves": list(decision.metadata["questions"]["move"]["criteria"])}
