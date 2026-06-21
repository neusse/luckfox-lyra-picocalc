import tempfile
import unittest
from pathlib import Path

from picofb import BLACK, RED, WHITE, Canvas
from picofb.ttf import measure_ttf_text, resolve_font


class TrueTypeTextTests(unittest.TestCase):
    def test_resolve_font_returns_existing_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            font_path = Path(temp_dir) / "example.ttf"
            font_path.write_bytes(b"not-a-real-font")

            self.assertEqual(resolve_font(font_path), str(font_path))

    def test_text_ttf_draws_scalable_text_with_pillow_font(self):
        canvas = Canvas(80, 32, BLACK)

        self.assertIs(
            canvas.text_ttf("Hi", 2, 2, WHITE, font="DejaVuSans.ttf", size=18),
            canvas,
        )

        lit_pixels = sum(
            1
            for y in range(canvas.height)
            for x in range(canvas.width)
            if canvas.pixel(x, y) != BLACK
        )
        self.assertGreater(lit_pixels, 20)

    def test_text_ttf_uses_background_for_text_bounds(self):
        canvas = Canvas(80, 32, RED)

        canvas.text_ttf("Hi", 2, 2, WHITE, font="DejaVuSans.ttf", size=18, background=BLACK)

        black_pixels = sum(
            1
            for y in range(canvas.height)
            for x in range(canvas.width)
            if canvas.pixel(x, y) == BLACK
        )
        self.assertGreater(black_pixels, 0)

    def test_measure_ttf_text_returns_real_bounds(self):
        small = measure_ttf_text("Hi", font="DejaVuSans.ttf", size=12)
        large = measure_ttf_text("Hi", font="DejaVuSans.ttf", size=24)

        self.assertGreater(small.width, 0)
        self.assertGreater(small.height, 0)
        self.assertGreater(large.width, small.width)
        self.assertGreater(large.height, small.height)


if __name__ == "__main__":
    unittest.main()
