import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "python" / "picocalc_breakout.py"
sys.path.insert(0, str(ROOT / "python"))


class PicoCalcBreakoutTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_breakout", APP)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_render_game_draws_bricks_paddle_ball_and_status(self):
        module = self.load_module()
        from picofb import Canvas
        from picogames.breakout import BreakoutGame

        game = BreakoutGame()
        canvas = Canvas(320, 320, module.C_BG)

        module.render_game(canvas, game)

        brick = game.bricks[0]
        self.assertNotEqual(canvas.pixel(brick.x + 2, brick.y + 2), module.C_BG)
        self.assertEqual(canvas.pixel(int(game.paddle_x), game.paddle_y), module.C_PADDLE)
        self.assertNotEqual(canvas.pixel(5, 305), module.C_BG)

    def test_ctrl_f5_quits_breakout(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.F5, ctrl=True)), "quit")

    def test_space_and_enter_launch(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.CHAR, " ")), "launch")
        self.assertEqual(module.key_to_action(KeyPress(Key.ENTER)), "launch")


if __name__ == "__main__":
    unittest.main()
