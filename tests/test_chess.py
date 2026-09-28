import unittest
import chess
from layagamer.games.chess.agent import ChessLayaAgent
from layagamer.games.chess.engine import ChessState
from layagamer.games.chess.web import ChessWeb
from layagamer.agents import Decision


class ChessTests(unittest.TestCase):
    def test_python_chess_transitions_and_serialization(self):
        state = ChessState()
        self.assertEqual(len(state.legal_actions), 20)
        after = state.apply("e2e4")
        self.assertEqual(after.serialize()["turn"], "black")
        self.assertIn("e7e5", after.legal_actions)
        with self.assertRaises(ValueError): state.apply("e2e5")

    def test_checkmate_priority(self):
        candidates = [
            "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
            "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1",
        ]
        game = next(ChessState(fen) for fen in candidates if any(f["checkmate"] for f in ChessState(fen).consequences().values()))
        facts = game.consequences()
        mates = {move for move, fact in facts.items() if fact["checkmate"]}
        state, questions = ChessLayaAgent.request(game)
        self.assertEqual(set(questions["move"]["criteria"]), mates)
        self.assertEqual(state["action_constraint"], "immediate_checkmate")

    def test_web_state_uses_rules_engine(self):
        class Agent:
            def decide(self, state): return Decision("e7e5", {})
        web = ChessWeb(Agent())
        position = web.state({"move":"e2e4"})
        self.assertEqual(position["turn"], "black")
        response = web.decide(ChessState(position["fen"]))
        self.assertEqual(response["move"], "e7e5")
        self.assertEqual(response["position"]["turn"], "white")

