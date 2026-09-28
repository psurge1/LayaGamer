import unittest
from layagamer.games.tictactoe.web import TicTacToeWeb
from layagamer.agents import Decision


class WebGameTests(unittest.TestCase):
    def test_agents_and_original_response(self):
        class Tactical:
            def choose(self, board):
                return {"move": "5", "result": {"source": "tactical"}}
        class Trained:
            def decide(self, board):
                return Decision("2", {"agent": "tictactoe-finetuned", "result": {"source": "trained"}})
        game = TicTacToeWeb(Tactical(), Trained())
        for agent, expected in (("tactical", "5"), ("finetuned", "2")):
            request = game.prepare({"cells": ["."] * 9, "turn": "X", "agent": agent})
            response = game.decide(request)
            self.assertEqual(response["move"], expected)
            self.assertEqual(len(response["legal_moves"]), 9)
        self.assertEqual([a["id"] for a in game.describe()["agents"]], ["finetuned", "tactical"])

    def test_unavailable_agent_and_invalid_board(self):
        game = TicTacToeWeb(None)
        self.assertEqual([a["id"] for a in game.describe()["agents"]], ["tactical"])
        for payload in ({"cells": ["."] * 9, "agent": "finetuned"}, {"cells": []},
                        {"cells": ["X"] * 9}, {"cells": ["."] * 9, "agent": "snake"}):
            with self.assertRaises(ValueError):
                game.prepare(payload)
