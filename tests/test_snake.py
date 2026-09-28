import unittest
from layagamer.agents import Decision
from layagamer.games.snake.agent import SnakeLayaAgent
from layagamer.games.snake.engine import SnakeState
from layagamer.games.snake.web import SnakeWeb


class SnakeTests(unittest.TestCase):
    def test_step_growth_collision_and_context(self):
        state = SnakeState(food=(5, 5))
        grown = state.step("straight", next_food=(8, 8))
        self.assertEqual((grown.score, len(grown.snake), grown.snake[0]), (1, 4, (5, 5)))
        wall = SnakeState(width=5, height=5, snake=((4, 2), (3, 2)), direction="right", food=(0, 0))
        self.assertFalse(wall.step("straight").alive)
        facts = wall.consequences()
        self.assertFalse(facts["straight"]["safe"])
        self.assertGreater(facts["left"]["reachable_space"], 0)

    def test_context_describes_heading_and_shortest_food_route(self):
        state = SnakeState()
        facts = state.consequences()
        self.assertEqual(state.food_bearing(), "directly_ahead")
        self.assertEqual(facts["straight"]["shortest_food_path"], 2)
        self.assertTrue(facts["straight"]["on_shortest_food_route"])
        self.assertFalse(facts["left"]["on_shortest_food_route"])

    def test_harness_filters_fatal_actions(self):
        state = SnakeState(width=5, height=5, snake=((4, 2), (3, 2)), direction="right", food=(0, 0))
        observation, questions = SnakeLayaAgent.request(state)
        self.assertEqual(set(questions["move"]["criteria"]), {"option_a", "option_b"})
        self.assertEqual(observation["action_constraint"], "avoid_immediate_death")
        self.assertIn("food_bearing", observation)
        self.assertIn("Shortest visible route", questions["move"]["criteria"]["option_a"])

    def test_harness_decodes_neutral_option_labels(self):
        class Router:
            def predict(self, state, questions, **kwargs):
                options = list(questions["move"]["criteria"])
                return {"answers": {"move": {"choice": options[1],
                    "probabilities": dict.fromkeys(options, 1 / len(options))}}}

        decision = SnakeLayaAgent(router=Router(), temperature=0).decide(SnakeState())
        self.assertEqual(decision.action, "straight")
        self.assertEqual(decision.metadata["selection"]["model_choice"], "straight")
        self.assertEqual(set(decision.metadata["action_criteria"]), {"left", "straight", "right"})

    def test_web_adapter(self):
        class Agent:
            def decide(self, state): return Decision("straight", {"questions":{"move":{"criteria":{"straight":"go"}}}})
        game = SnakeWeb(Agent())
        state = game.prepare({"snake":[[4,5],[3,5]],"direction":"right","food":[7,5]})
        self.assertEqual(game.decide(state)["move"], "straight")
