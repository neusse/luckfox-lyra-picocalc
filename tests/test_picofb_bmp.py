import struct
import tempfile
import unittest
from pathlib import Path

from picofb import BLACK, Canvas, color565, load_bmp


def write_8bit_bmp(path: Path) -> None:
    width = 2
    height = 2
    palette = [
        (0, 0, 0, 0),
        (255, 0, 0, 0),
        (0, 255, 0, 0),
    ] + [(0, 0, 0, 0)] * 253
    rows = [
        bytes([1, 0]) + b"\x00\x00",
        bytes([0, 2]) + b"\x00\x00",
    ]
    pixel_data = b"".join(rows)
    offset = 14 + 40 + (256 * 4)
    size = offset + len(pixel_data)
    header = b"BM" + struct.pack("<IHHI", size, 0, 0, offset)
    dib = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        height,
        1,
        8,
        0,
        len(pixel_data),
        0,
        0,
        256,
        0,
    )
    palette_data = b"".join(bytes((b, g, r, 0)) for r, g, b, _ in palette)
    path.write_bytes(header + dib + palette_data + pixel_data)


class PicoFBBmpTests(unittest.TestCase):
    def test_loads_8bit_bmp_and_blits_transparently(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon.bmp"
            write_8bit_bmp(path)

            icon = load_bmp(path, transparent_index=0)
            canvas = Canvas(3, 3, background=color565(16, 16, 16))
            canvas.blit(icon, 1, 1)

            self.assertEqual(icon.width, 2)
            self.assertEqual(icon.height, 2)
            self.assertEqual(canvas.pixel(1, 2), color565(255, 0, 0))
            self.assertEqual(canvas.pixel(2, 1), color565(0, 255, 0))
            self.assertNotEqual(canvas.pixel(1, 1), BLACK)


if __name__ == "__main__":
    unittest.main()
