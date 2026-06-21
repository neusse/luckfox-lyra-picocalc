import importlib.util
import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "python" / "picocalc_minesweeper.py"
sys.path.insert(0, str(ROOT / "python"))


class PicoCalcMinesweeperTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_minesweeper", APP)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_render_menu_draws_large_selection(self):
        module = self.load_module()
        from picofb import Canvas

        canvas = Canvas(320, 320, module.C_BG)

        module.render_menu(canvas, selected=1)

        self.assertEqual(canvas.pixel(0, 0), module.C_PANEL_OUT)
        self.assertEqual(canvas.pixel(35, module.MENU_START_Y + module.MENU_LINE_H - 11), module.C_MENU_HILITE_BG)
        lit = sum(
            1
            for y in range(canvas.height)
            for x in range(canvas.width)
            if canvas.pixel(x, y) != module.C_BG
        )
        self.assertGreater(lit, 5000)

    def test_render_game_draws_grid_and_cursor(self):
        module = self.load_module()
        from picofb import Canvas
        from picogames.minesweeper import MinesweeperGame

        game = MinesweeperGame(width=module.GRID_W, height=module.GRID_H, mines=module.MINES_MED, rng=random.Random(2))
        canvas = Canvas(320, 320, module.C_BG)

        module.render_game(canvas, game)

        self.assertEqual(canvas.pixel(module.GRID_X, module.GRID_Y), module.C_CURSOR)
        self.assertNotEqual(canvas.pixel(10, 10), module.C_BG)

    def test_ctrl_f5_quits_minesweeper(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.F5, ctrl=True)), "quit")


if __name__ == "__main__":
    unittest.main()
