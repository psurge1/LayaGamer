"""Specialized Snake harness with route, safety, and space context."""
import random
from time import perf_counter
from typing import Any

from layagamer.agents import Decision
from layagamer.agents.sampling import select_action
from .engine import SnakeState


class SnakeLayaAgent:
    def __init__(self, *, device: str | None = None, router: Any = None,
                 temperature: float = 1.0, seed: int | None = None):
        self.device, self.router, self.temperature = device, router, temperature
        self.rng = random.Random(seed)

    @staticmethod
    def constrained_actions(facts: dict[str, dict]) -> tuple[list[str], str]:
        """Shortlist tactically equivalent actions without choosing among them."""
        safe = [action for action, fact in facts.items() if fact["safe"]]
        if not safe:
            return list(facts), "no_safe_action"

        eating = [action for action in safe if facts[action]["eats_food"]]
        if eating:
            return eating, "eat_food"

        non_trapping = [action for action in safe if not facts[action]["trap_risk"]]
        candidates = non_trapping or safe
        routed = [action for action in candidates
                  if facts[action]["shortest_food_path"] is not None]
        if routed:
            best_distance = min(facts[action]["shortest_food_path"] for action in routed)
            shortest = [action for action in routed
                        if facts[action]["shortest_food_path"] == best_distance]
            return shortest, "shortest_safe_food_route"
        if non_trapping and len(non_trapping) < len(safe):
            return non_trapping, "avoid_trap"
        return safe, "avoid_immediate_death"

    @staticmethod
    def request(state: SnakeState) -> tuple[dict, dict]:
        facts = state.consequences()
        offered, constraint = SnakeLayaAgent.constrained_actions(facts)
        observation = {"game": "snake",
                       "rules": "Choose a relative turn, then move one cell. Eat food to grow. A wall or body collision ends the game.",
                       **state.observation(), "action_consequences": facts,
                       "action_constraint": constraint}
        criteria = {}
        for index, action in enumerate(offered):
            fact = facts[action]
            text = (f"{action.capitalize()}: face {fact['resulting_direction']} and move to {fact['next_head']}. "
                    f"Leaves {fact['reachable_space']} reachable cells ({fact['space_ratio']:.0%} of free space).")
            if fact["eats_food"]:
                text += " Eats the food immediately."
            elif fact["shortest_food_path"] is None:
                text += " No route to the food is currently visible."
            else:
                text += f" Shortest visible route to food: {fact['shortest_food_path']} more steps."
                if constraint == "shortest_safe_food_route":
                    text += " This is a shortest non-trapping food route."
            if fact["trap_risk"]:
                text += " Warning: little escape space; likely trap."
            # Neutral wire labels prevent the language meaning of "right" from
            # being confused with "correct". They are decoded below.
            criteria[f"option_{chr(ord('a') + index)}"] = text
        questions = {"move": {"type": "choice",
            "instructions": ("Choose among the tactically equivalent Snake moves offered by the harness. Prefer "
                             "escape space when routes are tied. Left/right are relative to the current heading."),
            "criteria": criteria}}
        return observation, questions

    def decide(self, observation: SnakeState) -> Decision:
        state, questions = self.request(observation)
        if self.router is None:
            from laya import Router
            self.router = Router(**({"device": self.device} if self.device else {}))
        started = perf_counter()
        result = self.router.predict(state, questions, model="english")
        elapsed = (perf_counter() - started) * 1000
        selected_option, selection = select_action(result["answers"]["move"],
            list(questions["move"]["criteria"]), self.rng, self.temperature)
        facts = state["action_consequences"]
        offered_actions, _ = self.constrained_actions(facts)
        option_to_action = dict(zip(questions["move"]["criteria"], offered_actions))
        action = option_to_action[selected_option]
        selection["model_choice"] = option_to_action[selection["model_choice"]]
        if "probabilities" in selection:
            selection["probabilities"] = {
                option_to_action[option]: probability
                for option, probability in selection["probabilities"].items()
            }
        action_criteria = {
            option_to_action[option]: text
            for option, text in questions["move"]["criteria"].items()
        }
        return Decision(action, {"agent": "snake-tactical", "latency_ms": elapsed,
            "harness_aids": [state["action_constraint"], "route_context", "space_context"], "selection": selection,
            "state": state, "questions": questions, "action_criteria": action_criteria,
            "option_to_action": option_to_action, "result": result})
