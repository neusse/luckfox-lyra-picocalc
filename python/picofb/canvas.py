"""Bytearray-backed RGB565 canvas and drawing primitives."""

from __future__ import annotations

from .colors import BLACK
from .font import FONT_5X7
from .ttf import draw_ttf_text


def _rgb_to_rgb565(red: int, green: int, blue: int) -> int:
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


class Canvas:
    """A clipped RGB565 pixel buffer."""

    def __init__(self, width: int, height: int, background: int = BLACK):
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = width
        self.height = height
        self.buffer = bytearray(width * height * 2)
        self.fill(background)

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def _contains(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def _offset(self, x: int, y: int) -> int:
        return ((y * self.width) + x) * 2

    def pixel(self, x: int, y: int, color: int | None = None):
        if not self._contains(x, y):
            return BLACK if color is None else self

        offset = self._offset(x, y)
        if color is None:
            return self.buffer[offset] | (self.buffer[offset + 1] << 8)

        self.buffer[offset] = color & 0xFF
        self.buffer[offset + 1] = (color >> 8) & 0xFF
        return self

    def fill(self, color: int):
        low = color & 0xFF
        high = (color >> 8) & 0xFF
        self.buffer[:] = bytes([low, high]) * (self.width * self.height)
        return self

    def clear(self):
        return self.fill(BLACK)

    def hline(self, x: int, y: int, width: int, color: int):
        if width <= 0 or y < 0 or y >= self.height:
            return self

        start = max(x, 0)
        end = min(x + width, self.width)
        for px in range(start, end):
            self.pixel(px, y, color)
        return self

    def vline(self, x: int, y: int, height: int, color: int):
        if height <= 0 or x < 0 or x >= self.width:
            return self

        start = max(y, 0)
        end = min(y + height, self.height)
        for py in range(start, end):
            self.pixel(x, py, color)
        return self

    def fill_rect(self, x: int, y: int, width: int, height: int, color: int):
        if width <= 0 or height <= 0:
            return self

        start_y = max(y, 0)
        end_y = min(y + height, self.height)
        for py in range(start_y, end_y):
            self.hline(x, py, width, color)
        return self

    def rect(self, x: int, y: int, width: int, height: int, color: int):
        if width <= 0 or height <= 0:
            return self

        self.hline(x, y, width, color)
        self.hline(x, y + height - 1, width, color)
        self.vline(x, y, height, color)
        self.vline(x + width - 1, y, height, color)
        return self

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int):
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy

        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            twice_error = 2 * error
            if twice_error >= dy:
                error += dy
                x0 += sx
            if twice_error <= dx:
                error += dx
                y0 += sy

        return self

    def text(self, value, x: int, y: int, color: int, background=None, scale: int = 1):
        scale = max(1, int(scale))
        origin_x = x
        cursor_x = x
        cursor_y = y

        for char in str(value):
            if char == "\n":
                cursor_x = origin_x
                cursor_y += 8 * scale
                continue

            glyph = FONT_5X7.get(char.upper(), FONT_5X7["?"])
            for row_index, row in enumerate(glyph):
                for column in range(5):
                    bit = row & (1 << (4 - column))
                    pixel_color = color if bit else background
                    if pixel_color is None:
                        continue

                    px = cursor_x + (column * scale)
                    py = cursor_y + (row_index * scale)
                    if scale == 1:
                        self.pixel(px, py, pixel_color)
                    else:
                        self.fill_rect(px, py, scale, scale, pixel_color)

            if background is not None:
                self.fill_rect(cursor_x + (5 * scale), cursor_y, scale, 7 * scale, background)

            cursor_x += 6 * scale

        return self

    def text_ttf(
        self,
        value,
        x: int,
        y: int,
        color: int,
        *,
        font: str = "sans",
        size: int = 16,
        background=None,
    ):
        return draw_ttf_text(
            self,
            value,
            x,
            y,
            color,
            font=font,
            size=size,
            background=background,
        )

    def blit(
        self,
        source,
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
        source_stride: int | None = None,
    ):
        if isinstance(source, Canvas):
            source_width = source.width
            source_height = source.height
            stride = source.width * 2
            data = memoryview(bytes(source.buffer))
            transparent = None
        elif hasattr(source, "width") and hasattr(source, "height") and hasattr(source, "buffer"):
            source_width = source.width
            source_height = source.height
            stride = source.width * 2
            data = memoryview(bytes(source.buffer))
            transparent = getattr(source, "transparent", None)
        elif isinstance(source, (bytes, bytearray, memoryview)):
            if width is None or height is None:
                raise ValueError("width and height are required for raw buffers")
            source_width = width
            source_height = height
            stride = source_stride if source_stride is not None else source_width * 2
            data = memoryview(source).cast("B")
            transparent = None
        else:
            raise TypeError("source must be a Canvas or raw RGB565 buffer")

        if source_width <= 0 or source_height <= 0:
            return self
        if stride < source_width * 2:
            raise ValueError("source_stride is too small for width")

        required_length = ((source_height - 1) * stride) + (source_width * 2)
        if len(data) < required_length:
            raise ValueError("source buffer is too small for dimensions")

        for source_y in range(source_height):
            row_offset = source_y * stride
            for source_x in range(source_width):
                if transparent is not None and transparent[(source_y * source_width) + source_x]:
                    continue
                offset = row_offset + (source_x * 2)
                pixel_color = data[offset] | (data[offset + 1] << 8)
                self.pixel(x + source_x, y + source_y, pixel_color)

        return self

    def image(self, image, x: int = 0, y: int = 0):
        if (
            not hasattr(image, "convert")
            or not hasattr(image, "getdata")
            or not hasattr(image, "size")
        ):
            raise TypeError("image must provide convert(), getdata(), and size")

        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        pixels = iter(rgb_image.getdata())

        for source_y in range(height):
            for source_x in range(width):
                red, green, blue = next(pixels)[:3]
                self.pixel(x + source_x, y + source_y, _rgb_to_rgb565(red, green, blue))

        return self
