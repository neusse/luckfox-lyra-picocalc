"""Small BMP loader for PicoFB icon assets."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .colors import color565


@dataclass
class Bitmap:
    """RGB565 bitmap with an optional transparency mask."""

    width: int
    height: int
    buffer: bytearray
    transparent: bytearray | None = None


def _rgb565_from_bgr(entry: bytes, tint: int | None = None) -> int:
    if tint is not None and entry[:3] != b"\x00\x00\x00":
        return tint
    blue, green, red = entry[:3]
    return color565(red, green, blue)


def load_bmp(path: str | Path, *, transparent_index: int | None = 0, tint: int | None = None) -> Bitmap:
    """Load an uncompressed 8-bit or 24-bit BMP as an RGB565 bitmap.

    The weather icons used by the CircuitPython PicoCalc app are 8-bit
    paletted BMPs. Palette index 0 is transparent by default.
    """
    data = Path(path).read_bytes()
    if data[:2] != b"BM":
        raise ValueError("not a BMP file")

    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40:
        raise ValueError("unsupported BMP DIB header")

    width = struct.unpack_from("<i", data, 18)[0]
    raw_height = struct.unpack_from("<i", data, 22)[0]
    planes = struct.unpack_from("<H", data, 26)[0]
    bpp = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    colors_used = struct.unpack_from("<I", data, 46)[0]

    if planes != 1 or compression != 0:
        raise ValueError("only uncompressed BMP files are supported")
    if width <= 0 or raw_height == 0:
        raise ValueError("invalid BMP dimensions")
    if bpp not in (8, 24):
        raise ValueError("only 8-bit paletted and 24-bit BMP files are supported")

    top_down = raw_height < 0
    height = abs(raw_height)
    out = bytearray(width * height * 2)
    transparent = bytearray(width * height) if transparent_index is not None and bpp == 8 else None

    palette = []
    if bpp == 8:
        count = colors_used or 256
        palette_start = 14 + dib_size
        for index in range(count):
            start = palette_start + (index * 4)
            palette.append(_rgb565_from_bgr(data[start : start + 4], tint=tint))
        row_stride = ((width + 3) // 4) * 4
    else:
        row_stride = (((width * 3) + 3) // 4) * 4

    for source_y in range(height):
        dest_y = source_y if top_down else height - source_y - 1
        row = pixel_offset + (source_y * row_stride)
        for x in range(width):
            dest_index = (dest_y * width) + x
            if bpp == 8:
                palette_index = data[row + x]
                color = palette[palette_index]
                if transparent is not None and palette_index == transparent_index:
                    transparent[dest_index] = 1
            else:
                start = row + (x * 3)
                color = _rgb565_from_bgr(data[start : start + 3], tint=tint)

            offset = dest_index * 2
            out[offset] = color & 0xFF
            out[offset + 1] = (color >> 8) & 0xFF

    return Bitmap(width=width, height=height, buffer=out, transparent=transparent)
