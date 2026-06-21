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

    def test_dirty_cells_cover_old_and_new_cursor_context(self):
        module = self.load_module()

        dirty = module.dirty_cells_for_cursor_move((0, 2), (0, 3))

        self.assertIn((0, 0), dirty)
        self.assertIn((8, 2), dirty)
        self.assertIn((8, 3), dirty)
        self.assertIn((1, 1), dirty)
        self.assertIn((1, 4), dirty)

    def test_dirty_cells_are_merged_into_row_regions(self):
        module = self.load_module()

        regions = module.dirty_regions_for_cells({(0, 0), (0, 1), (0, 3), (1, 3)})

        self.assertEqual(
            regions,
            [
                (module.GRID_X, module.GRID_Y, module.CELL * 2 + module.SELECT_THICKNESS, module.CELL + module.SELECT_THICKNESS),
                (module.GRID_X + module.CELL * 3, module.GRID_Y, module.CELL + module.SELECT_THICKNESS, module.CELL + module.SELECT_THICKNESS),
                (module.GRID_X + module.CELL * 3, module.GRID_Y + module.CELL, module.CELL + module.SELECT_THICKNESS, module.CELL + module.SELECT_THICKNESS),
            ],
        )

    def test_digit_sprite_is_trimmed_for_cell_centering(self):
        module = self.load_module()

        sprite = module.TEXT_CACHE.get("5", module.WHITE, size=25, fallback_scale=3)

        self.assertLess(sprite.width, 28)
        self.assertLess(sprite.height, 33)

    def test_interactive_app_rejects_ssh_tty(self):
        module = self.load_module()

        self.assertTrue(module.is_console_tty("/dev/tty1"))
        self.assertFalse(module.is_console_tty("/dev/pts/0"))

        with self.assertRaises(SystemExit):
            module.require_console_tty(lambda _fd: "/dev/pts/0")

    def test_ctrl_f5_quits_sudoku(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        action, value = module.key_to_action(KeyPress(Key.F5, ctrl=True))

        self.assertEqual(action, "quit")
        self.assertIsNone(value)


if __name__ == "__main__":
    unittest.main()
