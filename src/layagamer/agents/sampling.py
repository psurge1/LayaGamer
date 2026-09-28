"""Sample offered actions without changing the model's recorded response."""
import math
import random


def select_action(answer: dict, offered: list[str], rng: random.Random,
                  temperature: float = 0.5) -> tuple[str, dict]:
    if not math.isfinite(temperature) or temperature < 0:
        raise ValueError("Sampling temperature must be finite and nonnegative")
    choice = answer["choice"]
    if choice not in offered:
        raise ValueError(f"Model returned an action outside offered choices: {choice!r}")
    if temperature == 0:
        return choice, {"method": "argmax", "temperature": 0, "model_choice": choice}
    probabilities = answer.get("probabilities", {})
    if set(probabilities) != set(offered):
        raise ValueError("Expected probabilities for every offered action")
    values = [float(probabilities[m]) for m in offered]
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in values) or not any(values):
        raise ValueError("Invalid action probabilities")
    # Subtract the largest log weight to avoid underflow at low temperatures.
    peak = math.log(max(values))
    weights = [math.exp((math.log(p) - peak) / temperature) if p else 0 for p in values]
    total = sum(weights)
    distribution = {m: w / total for m, w in zip(offered, weights)}
    move = rng.choices(offered, weights=weights, k=1)[0]
    return move, {"method": "sample", "temperature": temperature,
                  "model_choice": choice, "probabilities": distribution}
