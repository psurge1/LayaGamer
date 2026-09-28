import unittest

from layagamer.games.tictactoe.agents.finetuned import FinetunedAgent, build_request
from layagamer.games.tictactoe.dataset import examples, value
from layagamer.tictactoe import Board


class FinetunedTests(unittest.TestCase):
    def test_no_tactical_filtering(self):
        board = Board()
        for move in ("1", "4", "2", "5"):
            board = board.play(move)
        state, questions = build_request(board)
        self.assertEqual(set(questions["move"]["criteria"]), set(board.legal_moves))
        self.assertNotIn("action_consequences", state)

    def test_decision_contract(self):
        class Fake:
            def predict(self, state, questions):
                return {"answers": {"move": {"choice": "5"}}}
        decision = FinetunedAgent("test-checkpoint", backend=Fake(), temperature=0).decide(Board())
        self.assertEqual(decision.action, "5")
        self.assertEqual(decision.metadata["harness_aids"], [])

    def test_labels_and_splits(self):
        rows = examples()
        self.assertEqual(len(rows), 4520)
        self.assertEqual(value(Board()), 0)
        groups = {}
        for row in rows:
            self.assertAlmostEqual(sum(row["target"].values()), 1)
            self.assertEqual(groups.setdefault(row["group"], row["split"]), row["split"])
            self.assertEqual((row["state"], row["questions"]), build_request(Board(tuple(row["cells"]), row["turn"])))
        board = Board()
        for move in ("2", "1", "5", "8", "3"):
            board = board.play(move)
        row = next(r for r in rows if tuple(r["cells"]) == board.cells)
        self.assertEqual(row["optimal_moves"], ["7"])
