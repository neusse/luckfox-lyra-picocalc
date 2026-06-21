import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "python" / "picocalc_bubble.py"
sys.path.insert(0, str(ROOT / "python"))


class PicoCalcBubbleAppTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_bubble", DEMO)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_render_once_draws_full_screen_effect(self):
        module = self.load_module()
        from picofb import BLACK, Canvas
        from picogames.bubble import BubbleUniverse

        canvas = Canvas(320, 320, BLACK)
        bubble = BubbleUniverse(320, 320)
        bubble.animation_time = 900.0

        module.render_frame(canvas, bubble)

        lit = sum(
            1
            for y in range(canvas.height)
            for x in range(canvas.width)
            if canvas.pixel(x, y) != BLACK
        )
        self.assertGreater(lit, 500)

    def test_key_actions_match_bubble_controls(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.CHAR, "-")), "speed_down")
        self.assertEqual(module.key_to_action(KeyPress(Key.CHAR, "=")), "speed_up")
        self.assertEqual(module.key_to_action(KeyPress(Key.CHAR, " ")), "pause")
        self.assertEqual(module.key_to_action(KeyPress(Key.ENTER)), "zoom_in")
        self.assertEqual(module.key_to_action(KeyPress(Key.DELETE)), "zoom_out")
        self.assertEqual(module.key_to_action(KeyPress(Key.LEFT)), "left")

    def test_ctrl_f5_quits_bubble(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.F5, ctrl=True)), "quit")


if __name__ == "__main__":
    unittest.main()
