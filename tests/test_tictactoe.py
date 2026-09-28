import unittest
from layagamer.agent import LayaPlayer
from layagamer.tictactoe import Board, LINES


class GameTests(unittest.TestCase):
    def test_all_reachable_games(self):
        seen = set()

        def visit(board):
            if board in seen:
                return
            seen.add(board)
            if board.finished:
                self.assertEqual(board.legal_moves, ())
                with self.assertRaises(ValueError):
                    board.play("1")
                return
            state, questions = LayaPlayer.request(board)
            self.assertEqual(state["you"], board.turn)
            winning = {m for m in board.legal_moves if board.play(m).winner == board.turn}
            opponent = "O" if board.turn == "X" else "X"
            threats = set()
            for move in board.legal_moves:
                hypothetical = list(board.cells)
                hypothetical[int(move) - 1] = opponent
                if any(all(hypothetical[i] == opponent for i in line) for line in LINES):
                    threats.add(move)
            safe = {m for m in board.legal_moves if all(
                board.play(m).play(reply).winner != opponent
                for reply in board.play(m).legal_moves)}
            expected = winning or (safe or threats if threats else set(board.legal_moves))
            self.assertEqual(set(questions["move"]["criteria"]), expected)
            for move in board.legal_moves:
                child = board.play(move)
                self.assertEqual(child.cells[int(move) - 1], board.turn)
                visit(child)

        visit(Board())
        self.assertEqual(len(seen), 5478)

    def test_router_contract(self):
        class FakeRouter:
            def predict(self, state, questions, **kwargs):
                return {"answers": {"move": {"choice": "5"}}}
        self.assertEqual(LayaPlayer(router=FakeRouter(), temperature=0).choose(Board())["move"], "5")

    def test_reject_occupied_choice(self):
        class FakeRouter:
            def predict(self, *args, **kwargs):
                return {"answers": {"move": {"choice": "1"}}}
        with self.assertRaises(ValueError):
            LayaPlayer(router=FakeRouter()).choose(Board().play("1"))
