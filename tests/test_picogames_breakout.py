import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))


class BreakoutModelTests(unittest.TestCase):
    def test_launch_starts_ball_upward(self):
        from picogames.breakout import BreakoutGame

        game = BreakoutGame(rng=random.Random(1))

        game.launch()

        self.assertTrue(game.active)
        self.assertNotEqual(game.ball_dx, 0)
        self.assertLess(game.ball_dy, 0)

    def test_paddle_movement_clamps_to_screen(self):
        from picogames.breakout import BreakoutGame

        game = BreakoutGame()

        game.move_paddle("left", amount=999)
        self.assertEqual(game.paddle_x, 0)

        game.move_paddle("right", amount=999)
        self.assertEqual(game.paddle_x, game.width - game.paddle_width)

    def test_brick_collision_scores_and_removes_brick(self):
        from picogames.breakout import BreakoutGame

        game = BreakoutGame(rng=random.Random(2))
        brick = next(brick for brick in game.bricks if brick.alive)
        game.active = True
        game.ball_x = brick.x + brick.width / 2
        game.ball_y = brick.y + brick.height + game.ball_radius - 1
        game.ball_dx = 0
        game.ball_dy = -2

        events = game.step(1 / 60)

        self.assertIn("brick", events)
        self.assertFalse(brick.alive)
        self.assertEqual(game.score, 10)

    def test_life_loss_resets_ball_and_stops_play(self):
        from picogames.breakout import BreakoutGame

        game = BreakoutGame()
        game.active = True
        game.ball_y = game.height - game.status_height + 10

        events = game.step(1 / 60)

        self.assertIn("life_lost", events)
        self.assertEqual(game.lives, 2)
        self.assertFalse(game.active)
        self.assertFalse(game.game_over)

    def test_restart_after_game_over_restores_initial_state(self):
        from picogames.breakout import BreakoutGame

        game = BreakoutGame()
        game.score = 120
        game.lives = 0
        game.game_over = True
        for brick in game.bricks[:3]:
            brick.alive = False

        game.restart()

        self.assertEqual(game.score, 0)
        self.assertEqual(game.lives, 3)
        self.assertFalse(game.game_over)
        self.assertEqual(game.bricks_remaining, game.brick_rows * game.brick_cols)


if __name__ == "__main__":
    unittest.main()
