import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))


class BubbleModelTests(unittest.TestCase):
    def test_palette_and_tables_are_initialized(self):
        from picogames.bubble import BubbleUniverse, PALETTE_LEN, SINTABLEENTRIES

        bubble = BubbleUniverse(320, 320)

        self.assertEqual(len(bubble.palette), PALETTE_LEN)
        self.assertEqual(len(bubble.sin_table), SINTABLEENTRIES)
        self.assertEqual(len(bubble.cos_table), SINTABLEENTRIES)

    def test_render_writes_colored_pixels(self):
        from picofb import BLACK, Canvas
        from picogames.bubble import BubbleUniverse

        bubble = BubbleUniverse(96, 96)
        bubble.animation_time = 900.0
        canvas = Canvas(96, 96, BLACK)

        bubble.render(canvas)

        lit = sum(
            1
            for y in range(canvas.height)
            for x in range(canvas.width)
            if canvas.pixel(x, y) != BLACK
        )
        self.assertGreater(lit, 100)

    def test_actions_adjust_view_and_speed(self):
        from picogames.bubble import BubbleUniverse

        bubble = BubbleUniverse(320, 320)

        bubble.apply_action("speed_up")
        self.assertGreater(bubble.speed, 0.2)
        bubble.apply_action("zoom_in")
        self.assertGreater(bubble.size, 1.0)
        bubble.apply_action("left")
        self.assertGreater(bubble.x_offset, 0)
        bubble.apply_action("pause")
        self.assertEqual(bubble.speed, 0.0)
        bubble.apply_action("reset")
        self.assertEqual(bubble.size, 1.0)
        self.assertEqual(bubble.x_offset, 0)


if __name__ == "__main__":
    unittest.main()
