"""Snake browser adapter."""
from .agent import SnakeLayaAgent
from .engine import SnakeState


class SnakeWeb:
    def __init__(self, agent: SnakeLayaAgent): self.agent = agent
    def describe(self) -> dict:
        return {"id": "snake", "label": "Snake", "agents": [{"id": "tactical", "label": "Tactical Laya"}]}
    def prepare(self, payload: dict) -> SnakeState:
        if payload.get("agent", "tactical") != "tactical": raise ValueError("Unknown agent")
        return SnakeState(width=payload.get("width", 10), height=payload.get("height", 10),
            snake=tuple(tuple(point) for point in payload["snake"]), direction=payload["direction"],
            food=tuple(payload["food"]), score=payload.get("score", 0), alive=True)
    def decide(self, state: SnakeState) -> dict:
        decision = self.agent.decide(state)
        return {**decision.metadata, "move": decision.action, "legal_moves": ["left", "straight", "right"]}
