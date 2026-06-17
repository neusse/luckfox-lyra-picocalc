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

    def test_text_sprite_cache_reuses_rendered_glyphs(self):
        module = self.load_module()

        cache = module.TextSpriteCache()

        first = cache.get("5", module.WHITE, size=25, fallback_scale=3)
        second = cache.get("5", module.WHITE, size=25, fallback_scale=3)

        self.assertIs(first, second)
        self.assertGreater(first.width, 0)
        self.assertGreater(first.height, 0)

    def test_menu_options_offer_resume_and_difficulties(self):
        module = self.load_module()

        with_resume = module.menu_options(save_exists=True)
        without_resume = module.menu_options(save_exists=False)

        self.assertEqual([item.label for item in with_resume], ["CONTINUE", "EASY", "MEDIUM", "HARD", "EXIT"])
        self.assertEqual([item.label for item in without_resume], ["EASY", "MEDIUM", "HARD", "EXIT"])
        self.assertEqual(with_resume[0].action, "resume")
        self.assertEqual(without_resume[1].value, "medium")

    def test_menu_draws_large_graphical_selection(self):
        module = self.load_module()
        from picofb import Canvas

        canvas = Canvas(320, 320)

        module.render_menu_frame(canvas, module.menu_options(save_exists=True), selected=1)

        self.assertEqual(canvas.pixel(0, 0), module.HEADER)
        self.assertEqual(canvas.pixel(0, 40), module.MENU_BG)
        self.assertEqual(canvas.pixel(28, module.menu_item_y(1)), module.SELECT)
        self.assertNotEqual(canvas.pixel(70, 20), module.MENU_BG)
        last_bottom = module.menu_item_y(4) + module.MENU_ITEM_H
        self.assertLessEqual(last_bottom, 282)

    def test_applies_key_actions_to_game(self):
        module = self.load_module()
        game = module.demo_game()
        game.cursor_row = 0
        game.cursor_col = 2

        self.assertTrue(module.apply_key_action(game, "digit", 4))
        self.assertEqual(game.grid[0][2], 4)

        self.assertTrue(module.apply_key_action(game, "clear", None))
        self.assertEqual(game.grid[0][2], 0)

    def test_interactive_app_rejects_ssh_tty(self):
        module = self.load_module()

        self.assertTrue(module.is_console_tty("/dev/tty1"))
        self.assertFalse(module.is_console_tty("/dev/pts/0"))

        with self.assertRaises(SystemExit):
            module.require_console_tty(lambda _fd: "/dev/pts/0")


if __name__ == "__main__":
    unittest.main()
