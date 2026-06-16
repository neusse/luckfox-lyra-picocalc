import tempfile
import unittest
from pathlib import Path

from picofb import RED, Canvas, Display


class DisplayTests(unittest.TestCase):
    def make_display_files(self, width=4, height=3, bpp=16, stride=8, fb_size=None):
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        fb = root / "fb0"
        fb.mkdir(parents=True)
        (fb / "virtual_size").write_text(f"{width},{height}\n", encoding="ascii")
        (fb / "bits_per_pixel").write_text(f"{bpp}\n", encoding="ascii")
        (fb / "stride").write_text(f"{stride}\n", encoding="ascii")
        fb_path = root / "fb0-device"
        fb_path.write_bytes(bytes(fb_size if fb_size is not None else stride * height))
        self.addCleanup(temp_dir.cleanup)
        return root, fb_path

    def test_reads_sysfs_metadata_and_creates_canvas(self):
        root, fb_path = self.make_display_files()
        display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
        self.addCleanup(display.close)

        self.assertEqual(display.path, str(fb_path))
        self.assertEqual(display.width, 4)
        self.assertEqual(display.height, 3)
        self.assertEqual(display.bpp, 16)
        self.assertEqual(display.stride, 8)
        self.assertEqual(display.size, (4, 3))
        self.assertIsInstance(display.canvas, Canvas)
        self.assertIs(display.buffer, display.canvas.buffer)

    def test_rejects_32_bpp_framebuffer(self):
        root, fb_path = self.make_display_files(bpp=32)

        with self.assertRaisesRegex(ValueError, "16-bpp"):
            Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")

    def test_rejects_stride_smaller_than_row_bytes(self):
        root, fb_path = self.make_display_files(stride=7)

        with self.assertRaisesRegex(ValueError, "stride"):
            Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")

    def test_missing_framebuffer_file_raises_file_not_found_error(self):
        root, fb_path = self.make_display_files()
        fb_path.unlink()

        with self.assertRaisesRegex(FileNotFoundError, "framebuffer device missing"):
            Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")

    def test_invalid_virtual_size_metadata_raises_value_error(self):
        root, fb_path = self.make_display_files()
        (root / "fb0" / "virtual_size").write_text("4x3\n", encoding="ascii")

        with self.assertRaisesRegex(ValueError, "invalid framebuffer virtual_size"):
            Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")

    def test_show_writes_canvas_when_stride_matches_row_bytes(self):
        root, fb_path = self.make_display_files(stride=8)
        display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
        self.addCleanup(display.close)

        display.pixel(2, 1, RED)
        self.assertIs(display.show(), display)

        data = fb_path.read_bytes()
        offset = ((1 * 4) + 2) * 2
        self.assertEqual(data[offset : offset + 2], bytes([0x00, 0xF8]))

    def test_show_writes_canvas_rows_when_stride_is_padded(self):
        root, fb_path = self.make_display_files(stride=12)
        display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
        self.addCleanup(display.close)

        display.pixel(2, 1, RED)
        self.assertIs(display.show(), display)

        data = fb_path.read_bytes()
        offset = (1 * 12) + (2 * 2)
        self.assertEqual(data[offset : offset + 2], bytes([0x00, 0xF8]))
        self.assertEqual(data[20:24], bytes(4))

    def test_context_manager_closes_framebuffer(self):
        root, fb_path = self.make_display_files()

        with Display(str(fb_path), sysfs_root=str(root), fb_name="fb0") as display:
            framebuffer = display._fb
            self.assertFalse(framebuffer.closed)

        self.assertTrue(framebuffer.closed)

    def test_chainable_methods_delegate_to_canvas(self):
        root, fb_path = self.make_display_files()
        display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
        self.addCleanup(display.close)

        self.assertIs(display.fill(RED), display)
        self.assertEqual(display.pixel(0, 0), RED)

    def test_pixel_setter_returns_display_and_getter_returns_color(self):
        root, fb_path = self.make_display_files()
        display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
        self.addCleanup(display.close)

        self.assertIs(display.pixel(1, 1, RED), display)
        self.assertEqual(display.pixel(1, 1), RED)


if __name__ == "__main__":
    unittest.main()
