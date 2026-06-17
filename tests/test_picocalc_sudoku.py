import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "python" / "picocalc_sudoku.py"
sys.path.insert(0, str(ROOT / "python"))


class PicoCalcSudokuAppTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_sudoku", DEMO)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_rendered_board_draws_to_framebuffer_canvas(self):
        module = self.load_module()
        from picofb import Canvas

        game = module.demo_game()
        canvas = Canvas(320, 320)

        module.render_sudoku_frame(canvas, game)

        self.assertEqual(canvas.pixel(0, 0), module.HEADER)
        self.assertEqual(canvas.pixel(module.GRID_X, module.GRID_Y), module.GRID_THICK)
        self.assertEqual(
            canvas.pixel(module.GRID_X + game.cursor_col * module.CELL, module.GRID_Y),
            module.SELECT,
        )
        self.assertNotEqual(canvas.pixel(8, 6), module.HEADER)

    def test_applies_key_actions_to_game(self):
        module = self.load_module()
        game = module.demo_game()
        game.cursor_row = 0
        game.cursor_col = 2

        self.assertTrue(module.apply_key_action(game, "digit", 4))
        self.assertEqual(game.grid[0][2], 4)

        self.assertTrue(module.apply_key_action(game, "clear", None))
        self.assertEqual(game.grid[0][2], 0)


if __name__ == "__main__":
    unittest.main()
