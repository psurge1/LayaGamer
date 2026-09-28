import unittest
from layagamer.games.minesweeper.agent import MinesweeperLayaAgent
from layagamer.games.minesweeper.engine import MinesweeperState


class MinesweeperTests(unittest.TestCase):
    def test_reveal_flood_win_and_mine(self):
        state = MinesweeperState(4, 4, frozenset({(3, 3)}))
        cleared = state.apply("reveal:0,0")
        self.assertTrue(cleared.won)
        exploded = state.apply("reveal:3,3")
        self.assertEqual(exploded.exploded, (3, 3))

    def test_visible_deductions_and_harness(self):
        visible = frozenset({(0, 0), (0, 1), (1, 1)})
        state = MinesweeperState(4, 4, frozenset({(1, 0)}), visible)
        facts = state.deductions()
        self.assertTrue(facts[(1, 0)]["certain_mine"])
        observation, questions = MinesweeperLayaAgent.request(state)
        self.assertEqual(observation["action_constraint"], "certain_mine_flags")
        self.assertIn("flag:1,0", questions["move"]["criteria"])

        flagged = MinesweeperState(4, 4, frozenset({(1, 0)}), visible, frozenset({(1, 0)}))
        observation, questions = MinesweeperLayaAgent.request(flagged)
        self.assertEqual(observation["action_constraint"], "provably_safe_reveals")
        self.assertTrue(all(action.startswith("reveal:") for action in questions["move"]["criteria"]))

    def test_agent_never_receives_mine_locations(self):
        state = MinesweeperState(4, 4, frozenset({(3, 3)}))
        observation, _ = MinesweeperLayaAgent.request(state)
        self.assertNotIn("mines", observation)
        self.assertNotIn([3, 3], observation["board"])
