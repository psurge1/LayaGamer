import unittest

from layagamer.context import consequences, winning_squares
from layagamer.agent import LayaPlayer
from layagamer.tictactoe import Board


def position(*moves):
    board = Board()
    for move in moves:
        board = board.play(move)
    return board


class ContextTests(unittest.TestCase):
    def test_win_and_block(self):
        board = position("1", "4", "2", "5")
        facts = consequences(board)
        self.assertTrue(facts["3"]["wins_now"])
        self.assertEqual(facts["3"]["opponent_can_win_next_at"], [])
        self.assertEqual(facts["6"]["blocks_threat_at"], "6")
        self.assertEqual(facts["6"]["opponent_can_win_next_at"], [])
        self.assertEqual(facts["9"]["opponent_can_win_next_at"], ["6"])

    def test_fork(self):
        facts = consequences(position("1", "5", "9", "2"))
        self.assertTrue(facts["7"]["creates_fork"])
        self.assertEqual(facts["7"]["your_next_winning_squares"], ["4", "8"])

    def test_opponent_fork(self):
        facts = consequences(position("1", "5", "9"))
        self.assertTrue(facts["3"]["opponent_fork_replies"])
        self.assertEqual(facts["2"]["opponent_fork_replies"], [])

    def test_draw(self):
        board = position("1", "2", "3", "5", "4", "6", "8", "7")
        self.assertTrue(consequences(board)["9"]["draws_now"])

    def test_options_include_consequences(self):
        state, questions = LayaPlayer.request(position("1", "4", "2", "5"))
        self.assertIn("action_consequences", state)
        self.assertIn("Wins the game immediately", questions["move"]["criteria"]["3"])
        self.assertEqual(list(questions["move"]["criteria"]), ["3"])
        self.assertEqual(state["available_choices"], ["3"])
        self.assertEqual(state["action_consequences"]["9"]["opponent_can_win_next_at"], ["6"])

    def test_block_opponent_win(self):
        board = position("1", "4", "9", "5")
        _, questions = LayaPlayer.request(board)
        self.assertEqual(set(questions["move"]["criteria"]), {"6"})

    def test_reported_game_diagonal_block(self):
        board = position("2", "1", "5", "8", "3")
        state, questions = LayaPlayer.request(board)
        self.assertEqual(set(questions["move"]["criteria"]), {"7"})
        self.assertEqual(state["action_constraint"], "block_opponent_win")
        self.assertEqual(state["action_consequences"]["6"]["opponent_can_win_next_at"], ["7"])

    def test_without_threat_all_legal_choices_remain(self):
        board = position("2", "1")
        state, questions = LayaPlayer.request(board)
        self.assertEqual(set(questions["move"]["criteria"]), set(board.legal_moves))
        self.assertEqual(state["action_constraint"], "none")

    def test_unavoidable_double_threat_is_not_called_safe(self):
        board = position("1", "2", "3", "4", "5")
        state, questions = LayaPlayer.request(board)
        self.assertEqual(state["action_constraint"], "partial_block")
        self.assertEqual(set(questions["move"]["criteria"]), {"7", "9"})
        for move in questions["move"]["criteria"]:
            self.assertTrue(state["action_consequences"][move]["opponent_can_win_next_at"])

    def test_multiple_wins_remain_choices(self):
        board = position("1", "2", "5", "4", "3", "8")
        _, questions = LayaPlayer.request(board)
        self.assertEqual(set(questions["move"]["criteria"]), {"7", "9"})

    def test_winning_squares_match_actual_moves(self):
        seen = set()

        def visit(board):
            if board in seen or board.finished:
                return
            seen.add(board)
            actual = [m for m in board.legal_moves if board.play(m).winner == board.turn]
            self.assertEqual(winning_squares(board.cells, board.turn), actual)
            for m in board.legal_moves:
                visit(board.play(m))

        visit(Board())
