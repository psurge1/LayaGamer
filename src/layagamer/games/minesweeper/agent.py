"""Minesweeper harness based only on information visible to the player."""
import random
from time import perf_counter
from typing import Any

from layagamer.agents import Decision
from layagamer.agents.sampling import select_action
from .engine import MinesweeperState


class MinesweeperLayaAgent:
    def __init__(self, *, device: str | None = None, router: Any = None,
                 temperature: float = 0.5, seed: int | None = None):
        self.device, self.router, self.temperature = device, router, temperature
        self.rng = random.Random(seed)

    @staticmethod
    def request(game: MinesweeperState) -> tuple[dict, dict]:
        facts = game.deductions()
        safe = [point for point, fact in facts.items() if fact["provably_safe"]]
        mines = [point for point, fact in facts.items() if fact["certain_mine"]]
        if safe:
            actions, constraint = [("reveal", point) for point in safe], "provably_safe_reveals"
        elif mines:
            actions, constraint = [("flag", point) for point in mines], "certain_mine_flags"
        else:
            ranked = sorted(facts, key=lambda point: (facts[point]["estimated_risk"],
                                                       -facts[point]["adjacent_revealed"], point[1], point[0]))
            actions, constraint = [("reveal", point) for point in ranked[:16]], "lowest_risk_shortlist"
        criteria = {}
        for kind, point in actions:
            fact = facts[point]
            label = f"{kind}:{point[0]},{point[1]}"
            criteria[label] = (f"{kind.title()} column {point[0] + 1}, row {point[1] + 1}. "
                               f"Estimated mine risk {fact['estimated_risk']:.0%}; "
                               f"touches {fact['adjacent_revealed']} revealed cells.")
        state = {"game": "minesweeper", "rules": "Reveal every safe cell without revealing a mine. Flags mark suspected mines.",
                 "legend": {"#": "hidden", "F": "flag", "0-8": "adjacent mines"},
                 "board": game.visible(), "mines_total": len(game.mines), "flags_used": len(game.flagged),
                 "action_constraint": constraint,
                 "candidate_facts": {f"{x},{y}": fact for (x, y), fact in facts.items()}}
        return state, {"move": {"type": "choice",
            "instructions": "Choose the safest useful Minesweeper action from visible evidence. Reveal proven-safe cells and flag proven mines.",
            "criteria": criteria}}

    def decide(self, observation: MinesweeperState) -> Decision:
        state, questions = self.request(observation)
        if self.router is None:
            from laya import Router
            self.router = Router(**({"device": self.device} if self.device else {}))
        started = perf_counter(); result = self.router.predict(state, questions, model="english")
        elapsed = (perf_counter() - started) * 1000
        action, selection = select_action(result["answers"]["move"],
            list(questions["move"]["criteria"]), self.rng, self.temperature)
        return Decision(action, {"agent": "minesweeper-tactical", "latency_ms": elapsed,
            "harness_aids": [state["action_constraint"], "visible_constraint_deductions"],
            "selection": selection, "state": state, "questions": questions, "result": result})
