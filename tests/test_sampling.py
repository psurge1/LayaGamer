import random
import unittest

from layagamer.agents.sampling import select_action
from layagamer.agent import LayaPlayer
from layagamer.games.tictactoe.agents.finetuned import FinetunedAgent
from layagamer.tictactoe import Board


class SamplingTests(unittest.TestCase):
    def test_variety_and_seed(self):
        answer = {"choice": "1", "probabilities": {"1": 0.6, "2": 0.4}}
        def sequence():
            rng = random.Random(42)
            return [select_action(answer, ["1", "2"], rng)[0] for _ in range(100)]
        self.assertEqual(sequence(), sequence())
        self.assertEqual(set(sequence()), {"1", "2"})
        _, metadata = select_action(answer, ["1", "2"], random.Random(1))
        self.assertAlmostEqual(metadata["probabilities"]["1"], 0.36 / 0.52)
        self.assertEqual(answer["choice"], "1")

    def test_agents_sample_only_offered_actions(self):
        class Fake:
            def predict(self, state, questions, **kwargs):
                moves = list(questions["move"]["criteria"])
                return {"answers": {"move": {"choice": moves[0],
                    "probabilities": {m: 1 / len(moves) for m in moves}}}}
        board = Board()
        for move in ("2", "1", "5", "8", "3"):
            board = board.play(move)
        tactical = LayaPlayer(router=Fake(), seed=42)
        trained = FinetunedAgent("fake", backend=Fake(), seed=42)
        self.assertEqual({tactical.choose(board)["move"] for _ in range(50)}, {"7"})
        self.assertEqual({trained.decide(board).action for _ in range(100)}, set(board.legal_moves))

    def test_invalid_distribution_rejected(self):
        for probabilities in ({}, {"1": 0}, {"1": float("nan")}, {"1": -1}):
            with self.assertRaises(ValueError):
                select_action({"choice": "1", "probabilities": probabilities}, ["1"], random.Random())
