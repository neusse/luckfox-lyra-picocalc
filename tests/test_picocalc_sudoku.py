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

    def test_rendered_board_fits_picocalc_console(self):
        module = self.load_module()
        game = module.demo_game()

        screen = module.render_game_screen(game, width=45, show_help=True)

        lines = screen.splitlines()
        self.assertGreaterEqual(len(lines), 18)
        self.assertTrue(all(len(module.strip_ansi(line)) <= 45 for line in lines))
        self.assertIn("PicoCalc Sudoku", screen)
        self.assertIn("1-9 set", screen)

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
