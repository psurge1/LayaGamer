"""Chess browser adapter using python-chess for every state transition."""
import chess
from .agent import ChessLayaAgent
from .engine import ChessState


class ChessWeb:
    def __init__(self, agent: ChessLayaAgent): self.agent = agent
    def describe(self) -> dict:
        return {"id": "chess", "label": "Chess", "agents": [{"id": "tactical", "label": "Tactical Laya"}]}
    def prepare(self, payload: dict) -> ChessState:
        if payload.get("agent", "tactical") != "tactical": raise ValueError("Unknown agent")
        state = ChessState(payload.get("fen", chess.STARTING_FEN))
        if state.finished: raise ValueError("Game is finished")
        return state
    def decide(self, state: ChessState) -> dict:
        decision = self.agent.decide(state); next_state = state.apply(decision.action)
        return {**decision.metadata, "move": decision.action,
                "legal_moves": list(state.legal_actions), "position": next_state.serialize()}
    def state(self, payload: dict) -> dict:
        state = ChessState(payload.get("fen", chess.STARTING_FEN))
        if payload.get("move") is not None: state = state.apply(payload["move"])
        return state.serialize()
