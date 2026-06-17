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

    def test_cached_background_gives_sphere_subtle_body(self):
        from picofb import BLACK, color565
        from picogames.bubble import BubbleUniverse, SPHERE_CENTER_RGB

        bubble = BubbleUniverse(64, 64)

        self.assertEqual(bubble.background.pixel(32, 32), color565(*SPHERE_CENTER_RGB))
        self.assertEqual(bubble.background.pixel(0, 0), BLACK)

    def test_render_starts_from_cached_background(self):
        from picofb import BLACK, Canvas
        from picogames.bubble import BubbleUniverse

        class BlitCanvas(Canvas):
            def __init__(self, width, height, background=BLACK):
                super().__init__(width, height, background)
                self.blit_calls = 0

            def blit(self, *args, **kwargs):
                self.blit_calls += 1
                return super().blit(*args, **kwargs)

        bubble = BubbleUniverse(96, 96)
        canvas = BlitCanvas(96, 96, BLACK)

        bubble.render(canvas)

        self.assertGreaterEqual(canvas.blit_calls, 1)
        self.assertNotEqual(canvas.pixel(48, 48), BLACK)

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

    def test_render_uses_bulk_pixel_scatter_when_available(self):
        from picofb import BLACK, Canvas
        from picogames.bubble import BubbleUniverse

        class ScatterCanvas(Canvas):
            def __init__(self, width, height, background=BLACK):
                super().__init__(width, height, background)
                self.scatter_calls = 0

            def scatter_rgb565(self, xs, ys, colors):
                self.scatter_calls += 1
                return super().scatter_rgb565(xs, ys, colors)

        bubble = BubbleUniverse(96, 96)
        bubble.animation_time = 900.0
        canvas = ScatterCanvas(96, 96, BLACK)

        bubble.render(canvas)

        self.assertEqual(canvas.scatter_calls, 1)

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

    def test_color_generation_tolerates_high_iteration_counts(self):
        from picogames.bubble import calculate_color

        color = calculate_color(curve_index=0, iteration=127)

        self.assertIsInstance(color, int)


if __name__ == "__main__":
    unittest.main()
