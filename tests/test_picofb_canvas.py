import unittest

from picofb import BLACK, BLUE, GREEN, RED, WHITE, Canvas


class CanvasTests(unittest.TestCase):
    def test_rejects_non_positive_dimensions(self):
        with self.assertRaises(ValueError):
            Canvas(0, 1)
        with self.assertRaises(ValueError):
            Canvas(1, 0)

    def test_size_and_buffer_are_initialized_from_background(self):
        canvas = Canvas(3, 2, BLUE)
        self.assertEqual(canvas.size, (3, 2))
        self.assertEqual(canvas.buffer, bytearray(bytes([0x1F, 0x00]) * 6))

    def test_pixel_writes_rgb565_little_endian(self):
        canvas = Canvas(4, 3)
        canvas.pixel(1, 2, RED)
        offset = ((2 * 4) + 1) * 2
        self.assertEqual(canvas.buffer[offset : offset + 2], bytes([0x00, 0xF8]))
        self.assertEqual(canvas.pixel(1, 2), RED)

    def test_out_of_bounds_pixel_is_clipped(self):
        canvas = Canvas(2, 2)
        canvas.pixel(-1, 0, RED)
        canvas.pixel(2, 0, RED)
        canvas.pixel(0, -1, RED)
        canvas.pixel(0, 2, RED)
        self.assertEqual(canvas.buffer, bytearray(8))
        self.assertEqual(canvas.pixel(-1, 0), BLACK)

    def test_scatter_rgb565_writes_and_clips_multiple_pixels(self):
        canvas = Canvas(3, 2)

        self.assertIs(
            canvas.scatter_rgb565(
                xs=[0, 2, -1, 3, 1],
                ys=[0, 1, 0, 1, 1],
                colors=[RED, BLUE, GREEN, GREEN, WHITE],
            ),
            canvas,
        )

        self.assertEqual(canvas.pixel(0, 0), RED)
        self.assertEqual(canvas.pixel(2, 1), BLUE)
        self.assertEqual(canvas.pixel(1, 1), WHITE)
        self.assertEqual(canvas.pixel(0, 1), BLACK)

    def test_fill_and_clear(self):
        canvas = Canvas(2, 2)
        self.assertIs(canvas.fill(WHITE), canvas)
        self.assertEqual(canvas.buffer, bytearray(bytes([0xFF, 0xFF]) * 4))
        self.assertIs(canvas.clear(), canvas)
        self.assertEqual(canvas.buffer, bytearray(8))

    def test_fill_rect_clips_to_canvas(self):
        canvas = Canvas(4, 4)
        self.assertIs(canvas.fill_rect(-1, -1, 3, 3, GREEN), canvas)
        self.assertEqual(canvas.pixel(0, 0), GREEN)
        self.assertEqual(canvas.pixel(1, 1), GREEN)
        self.assertEqual(canvas.pixel(2, 2), BLACK)

    def test_hline_vline_rect_and_line(self):
        canvas = Canvas(5, 5)
        self.assertIs(canvas.hline(1, 0, 3, RED), canvas)
        self.assertIs(canvas.vline(0, 1, 3, GREEN), canvas)
        self.assertIs(canvas.rect(1, 1, 3, 3, BLUE), canvas)
        self.assertIs(canvas.line(0, 4, 4, 0, WHITE), canvas)
        self.assertEqual(canvas.pixel(1, 0), RED)
        self.assertEqual(canvas.pixel(0, 1), GREEN)
        self.assertEqual(canvas.pixel(1, 1), BLUE)
        self.assertEqual(canvas.pixel(4, 0), WHITE)
        self.assertEqual(canvas.pixel(0, 4), WHITE)

    def test_text_draws_uppercase_glyph_pixels(self):
        canvas = Canvas(5, 7)
        self.assertIs(canvas.text("A", 0, 0, WHITE), canvas)

        lit_pixels = sum(
            1
            for y in range(7)
            for x in range(5)
            if canvas.pixel(x, y) == WHITE
        )
        self.assertGreater(lit_pixels, 8)

    def test_text_draws_lowercase_using_uppercase_fallback(self):
        canvas = Canvas(5, 7)
        canvas.text("a", 0, 0, WHITE)

        lit_pixels = sum(
            1
            for y in range(7)
            for x in range(5)
            if canvas.pixel(x, y) == WHITE
        )
        self.assertGreater(lit_pixels, 0)

    def test_text_draws_percent_glyph(self):
        canvas = Canvas(5, 7)
        canvas.text("%", 0, 0, WHITE)

        lit_pixels = sum(
            1
            for y in range(7)
            for x in range(5)
            if canvas.pixel(x, y) == WHITE
        )
        self.assertGreater(lit_pixels, 0)

    def test_text_draws_square_brackets(self):
        canvas = Canvas(17, 7)
        canvas.text("[M]", 0, 0, WHITE)

        left_pixels = sum(1 for y in range(7) if canvas.pixel(0, y) == WHITE)
        right_pixels = sum(1 for y in range(7) if canvas.pixel(16, y) == WHITE)
        self.assertGreater(left_pixels, 2)
        self.assertGreater(right_pixels, 2)

    def test_text_background_clears_inter_character_spacer(self):
        canvas = Canvas(11, 7, RED)

        self.assertIs(canvas.text("AA", 0, 0, WHITE, background=BLACK), canvas)

        for y in range(7):
            self.assertEqual(canvas.pixel(5, y), BLACK)

    def test_blit_canvas_clips_to_visible_bottom_right_pixel(self):
        source = Canvas(2, 2)
        source.pixel(0, 0, RED)
        source.pixel(1, 0, GREEN)
        source.pixel(0, 1, BLUE)
        source.pixel(1, 1, WHITE)
        target = Canvas(3, 3)

        self.assertIs(target.blit(source, 2, 2), target)

        self.assertEqual(target.pixel(2, 2), RED)
        self.assertEqual(target.pixel(1, 2), BLACK)
        self.assertEqual(target.pixel(2, 1), BLACK)

    def test_raw_buffer_blit_copies_rgb565_pixels(self):
        target = Canvas(2, 1)
        source = bytes([0x00, 0xF8, 0x1F, 0x00])

        self.assertIs(target.blit(source, width=2, height=1), target)

        self.assertEqual(target.pixel(0, 0), RED)
        self.assertEqual(target.pixel(1, 0), BLUE)

    def test_raw_buffer_blit_requires_width_and_height(self):
        canvas = Canvas(1, 1)

        with self.assertRaises(ValueError):
            canvas.blit(bytes([0x00, 0xF8]), width=1)

        with self.assertRaises(ValueError):
            canvas.blit(bytes([0x00, 0xF8]), height=1)

    def test_image_converts_fake_rgb_data_to_rgb565_pixels(self):
        class FakeImage:
            size = (2, 1)
            mode = "RGB"

            def convert(self, mode):
                self.mode = mode
                return self

            def getdata(self):
                return [(255, 0, 0), (0, 0, 255)]

        canvas = Canvas(2, 1)

        self.assertIs(canvas.image(FakeImage()), canvas)

        self.assertEqual(canvas.pixel(0, 0), RED)
        self.assertEqual(canvas.pixel(1, 0), BLUE)

    def test_image_rejects_unsupported_objects(self):
        with self.assertRaises(TypeError):
            Canvas(1, 1).image(object())


if __name__ == "__main__":
    unittest.main()
