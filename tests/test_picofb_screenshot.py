import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from picofb.screenshot import capture_framebuffer, rgb565_to_rgb888, write_png


def _png_chunks(data: bytes):
    offset = 8
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        yield kind, payload
        offset += 12 + length


class ScreenshotTests(unittest.TestCase):
    def test_rgb565_to_rgb888_expands_primary_colors(self):
        self.assertEqual(rgb565_to_rgb888(0xF800), (255, 0, 0))
        self.assertEqual(rgb565_to_rgb888(0x07E0), (0, 255, 0))
        self.assertEqual(rgb565_to_rgb888(0x001F), (0, 0, 255))

    def test_write_png_outputs_valid_rgb_png(self):
        rgb = bytes(
            [
                255,
                0,
                0,
                0,
                255,
                0,
                0,
                0,
                255,
                255,
                255,
                255,
            ]
        )
        png = write_png(rgb, 2, 2)

        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        chunks = dict(_png_chunks(png))
        self.assertIn(b"IHDR", chunks)
        self.assertIn(b"IDAT", chunks)
        self.assertIn(b"IEND", chunks)
        self.assertEqual(chunks[b"IHDR"][:8], struct.pack(">II", 2, 2))

        inflated = zlib.decompress(chunks[b"IDAT"])
        self.assertEqual(inflated, b"\x00" + rgb[:6] + b"\x00" + rgb[6:])

    def test_capture_framebuffer_respects_stride_padding(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fb_dir = root / "sys" / "class" / "graphics" / "fb0"
            fb_dir.mkdir(parents=True)
            (fb_dir / "virtual_size").write_text("2,2\n", encoding="ascii")
            (fb_dir / "bits_per_pixel").write_text("16\n", encoding="ascii")
            (fb_dir / "stride").write_text("6\n", encoding="ascii")

            framebuffer = root / "fb0"
            framebuffer.write_bytes(
                bytes(
                    [
                        0x00,
                        0xF8,
                        0xE0,
                        0x07,
                        0xAA,
                        0xAA,
                        0x1F,
                        0x00,
                        0xFF,
                        0xFF,
                        0xBB,
                        0xBB,
                    ]
                )
            )

            shot = capture_framebuffer(
                framebuffer,
                sysfs_root=root / "sys" / "class" / "graphics",
                fb_name="fb0",
            )

        self.assertEqual(shot.width, 2)
        self.assertEqual(shot.height, 2)
        self.assertEqual(
            shot.rgb,
            bytes(
                [
                    255,
                    0,
                    0,
                    0,
                    255,
                    0,
                    0,
                    0,
                    255,
                    255,
                    255,
                    255,
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
