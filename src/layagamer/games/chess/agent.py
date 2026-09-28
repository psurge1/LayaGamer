"""Chess harness using legal moves and shallow tactical consequences."""
import random
from time import perf_counter
from typing import Any

from layagamer.agents import Decision
from layagamer.agents.sampling import select_action
from .engine import ChessState


class ChessLayaAgent:
    def __init__(self, *, device: str | None = None, router: Any = None,
                 temperature: float = 0.35, seed: int | None = None):
        self.device, self.router, self.temperature = device, router, temperature
        self.rng = random.Random(seed)

    @staticmethod
    def request(game: ChessState) -> tuple[dict, dict]:
        board, facts = game.board(), game.consequences()
        mates = [move for move, fact in facts.items() if fact["checkmate"]]
        offered = mates or list(facts)
        criteria = {}
        for move in offered:
            fact = facts[move]
            details = [f"Play {fact['san']} with the {fact['piece']}."]
            if fact["checkmate"]: details.append("Checkmates immediately.")
            elif fact["check"]: details.append("Gives check.")
            if fact["capture"]: details.append(f"Captures {fact['capture']} worth {fact['capture_value']}.")
            if fact["promotion"]: details.append(f"Promotes to {fact['promotion']}.")
            details.append(f"Opponent has {fact['opponent_legal_replies']} legal replies.")
            if fact["destination_attacked"]:
                details.append("Destination is attacked" + (" and defended." if fact["destination_defended"] else " and undefended."))
            criteria[move] = " ".join(details)
        state = {"game": "chess", "rules": "Standard chess. Checkmate wins; stalemate and standard draw rules apply.",
                 "you": "white" if board.turn else "black", "fen": game.fen,
                 "board": str(board).splitlines(), "in_check": board.is_check(),
                 "action_consequences": facts,
                 "action_constraint": "immediate_checkmate" if mates else "legal_moves"}
        return state, {"move": {"type": "choice",
            "instructions": "Choose the strongest legal chess move. Take checkmate immediately; otherwise consider king safety, material, checks, and whether moved pieces are attacked.",
            "criteria": criteria}}

    def decide(self, observation: ChessState) -> Decision:
        state, questions = self.request(observation)
        if self.router is None:
            from laya import Router
            self.router = Router(**({"device": self.device} if self.device else {}))
        started = perf_counter(); result = self.router.predict(state, questions, model="english")
        elapsed = (perf_counter() - started) * 1000
        action, selection = select_action(result["answers"]["move"],
            list(questions["move"]["criteria"]), self.rng, self.temperature)
        return Decision(action, {"agent": "chess-tactical", "latency_ms": elapsed,
            "harness_aids": [state["action_constraint"], "shallow_tactical_context"],
            "selection": selection, "state": state, "questions": questions, "result": result})
