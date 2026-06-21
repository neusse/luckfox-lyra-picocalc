# PicoFB Framebuffer Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small dependency-free Python framebuffer graphics library for the Luckfox Lyra inside the ClockworkPi PicoCalc, with a demo that draws directly to `/dev/fb0`.

**Architecture:** `Display` owns Linux framebuffer metadata, device I/O, and a bytearray-backed `Canvas`. `Canvas` implements RGB565 drawing primitives and optional image conversion without requiring PyPI packages. Host tests cover color conversion, clipping, drawing behavior, and fake framebuffer flushes; device smoke tests verify the physical PicoCalc screen.

**Tech Stack:** Python 3 stdlib, Linux `/dev/fb0`, `/sys/class/graphics/fb0`, RGB565, `unittest`, existing `tools/luckfox-dev.py`, ADB.

---

## File Structure

- Create: `python/picofb/__init__.py`
  - Public package exports: `Display`, `Canvas`, `color565`, and color constants.
- Create: `python/picofb/colors.py`
  - RGB565 conversion and common color constants.
- Create: `python/picofb/font.py`
  - Built-in 5x7 bitmap font for digits, uppercase letters, common punctuation, and uppercase fallback for lowercase text.
- Create: `python/picofb/canvas.py`
  - Bytearray-backed RGB565 drawing surface and primitives.
- Create: `python/picofb/display.py`
  - Linux framebuffer metadata detection and flush logic.
- Create: `tests/test_picofb_colors.py`
  - Unit tests for color conversion and input validation.
- Create: `tests/test_picofb_canvas.py`
  - Unit tests for pixel storage, clipping, primitives, text, blit, and image adapter.
- Create: `tests/test_picofb_display.py`
  - Unit tests for sysfs metadata parsing and fake framebuffer writes.
- Create: `examples/python/fb_demo.py`
  - Physical PicoCalc screen demo with color bars, text, rectangles, and diagonal lines.
- Create: `scripts/device/enable-framebuffer-user.sh`
  - Device-side helper to keep `/dev/fb0` group-writable by `video` and add `neusse` to `video`.
- Modify: `tools/luckfox-dev.py`
  - Sync local `python/` package tree before `runpy`, and set remote `PYTHONPATH`.
- Create: `docs/picofb.md`
  - Short usage and troubleshooting notes.
- Modify: `luckfox-checklist.md`
  - Mark the framebuffer library work item with its new plan and pending execution status.

---

### Task 1: Package Scaffold And Color Helpers

**Files:**
- Create: `python/picofb/__init__.py`
- Create: `python/picofb/colors.py`
- Create: `tests/test_picofb_colors.py`

- [ ] **Step 1: Write the failing color tests**

Create `tests/test_picofb_colors.py`:

```python
import unittest

from picofb import BLACK, BLUE, GREEN, RED, WHITE, color565


class Color565Tests(unittest.TestCase):
    def test_primary_colors(self):
        self.assertEqual(color565(0, 0, 0), 0x0000)
        self.assertEqual(color565(255, 255, 255), 0xFFFF)
        self.assertEqual(color565(255, 0, 0), 0xF800)
        self.assertEqual(color565(0, 255, 0), 0x07E0)
        self.assertEqual(color565(0, 0, 255), 0x001F)

    def test_exported_constants(self):
        self.assertEqual(BLACK, 0x0000)
        self.assertEqual(WHITE, 0xFFFF)
        self.assertEqual(RED, 0xF800)
        self.assertEqual(GREEN, 0x07E0)
        self.assertEqual(BLUE, 0x001F)

    def test_rejects_non_integer_components(self):
        with self.assertRaises(TypeError):
            color565("255", 0, 0)

    def test_rejects_out_of_range_components(self):
        with self.assertRaises(ValueError):
            color565(-1, 0, 0)
        with self.assertRaises(ValueError):
            color565(0, 256, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `C:\Users\georg\Codex_Projects\luckfox-lyra`:

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest tests.test_picofb_colors
```

Expected: `ModuleNotFoundError: No module named 'picofb'`.

- [ ] **Step 3: Implement the package exports and color helper**

Create `python/picofb/colors.py`:

```python
"""RGB565 color helpers for PicoCalc framebuffer drawing."""

from __future__ import annotations


def _component(value: int, name: str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an int from 0 to 255")
    if value < 0 or value > 255:
        raise ValueError(f"{name} must be from 0 to 255")
    return value


def color565(r: int, g: int, b: int) -> int:
    """Convert 8-bit RGB components to a 16-bit RGB565 integer."""
    r = _component(r, "r")
    g = _component(g, "g")
    b = _component(b, "b")
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BLACK = color565(0, 0, 0)
WHITE = color565(255, 255, 255)
RED = color565(255, 0, 0)
GREEN = color565(0, 255, 0)
BLUE = color565(0, 0, 255)
CYAN = color565(0, 255, 255)
MAGENTA = color565(255, 0, 255)
YELLOW = color565(255, 255, 0)
```

Create `python/picofb/__init__.py`:

```python
"""Small RGB565 framebuffer drawing library for the PicoCalc Luckfox Lyra."""

from .colors import BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW, color565

try:
    from .canvas import Canvas
    from .display import Display
except ImportError:
    Canvas = None  # type: ignore[assignment]
    Display = None  # type: ignore[assignment]

__all__ = [
    "BLACK",
    "BLUE",
    "CYAN",
    "Canvas",
    "Display",
    "GREEN",
    "MAGENTA",
    "RED",
    "WHITE",
    "YELLOW",
    "color565",
]
```

- [ ] **Step 4: Run the color tests**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest tests.test_picofb_colors
```

Expected: `Ran 4 tests` and `OK`.

- [ ] **Step 5: Commit**

```powershell
git add python/picofb/__init__.py python/picofb/colors.py tests/test_picofb_colors.py
git commit -m "Add PicoFB color helpers"
```

---

### Task 2: Canvas Pixel Buffer And Drawing Primitives

**Files:**
- Create: `python/picofb/canvas.py`
- Create: `tests/test_picofb_canvas.py`
- Modify: `python/picofb/__init__.py`

- [ ] **Step 1: Write failing canvas tests**

Create `tests/test_picofb_canvas.py`:

```python
import unittest

from picofb import BLACK, BLUE, GREEN, RED, WHITE, Canvas, color565


class CanvasTests(unittest.TestCase):
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

    def test_fill_and_clear(self):
        canvas = Canvas(2, 2)
        canvas.fill(WHITE)
        self.assertEqual(canvas.buffer, bytearray(bytes([0xFF, 0xFF]) * 4))
        canvas.clear()
        self.assertEqual(canvas.buffer, bytearray(8))

    def test_fill_rect_clips_to_canvas(self):
        canvas = Canvas(4, 4)
        canvas.fill_rect(-1, -1, 3, 3, GREEN)
        self.assertEqual(canvas.pixel(0, 0), GREEN)
        self.assertEqual(canvas.pixel(1, 1), GREEN)
        self.assertEqual(canvas.pixel(2, 2), BLACK)

    def test_hline_vline_rect_and_line(self):
        canvas = Canvas(5, 5)
        canvas.hline(1, 0, 3, RED)
        canvas.vline(0, 1, 3, GREEN)
        canvas.rect(1, 1, 3, 3, BLUE)
        canvas.line(0, 4, 4, 0, WHITE)
        self.assertEqual(canvas.pixel(1, 0), RED)
        self.assertEqual(canvas.pixel(0, 1), GREEN)
        self.assertEqual(canvas.pixel(1, 1), BLUE)
        self.assertEqual(canvas.pixel(4, 0), WHITE)
        self.assertEqual(canvas.pixel(0, 4), WHITE)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the canvas tests to verify they fail**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest tests.test_picofb_canvas
```

Expected: import failure or `TypeError: 'NoneType' object is not callable` for `Canvas`.

- [ ] **Step 3: Implement `Canvas` primitives**

Create `python/picofb/canvas.py`:

```python
"""Bytearray-backed RGB565 drawing surface."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .colors import BLACK


def _pack565(color: int) -> bytes:
    color &= 0xFFFF
    return bytes((color & 0xFF, (color >> 8) & 0xFF))


class Canvas:
    """In-memory RGB565 canvas with clipping drawing operations."""

    def __init__(self, width: int, height: int, background: int = BLACK):
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = int(width)
        self.height = int(height)
        self.buffer = bytearray(self.width * self.height * 2)
        if background != BLACK:
            self.fill(background)

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def _offset(self, x: int, y: int) -> int | None:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None
        return ((y * self.width) + x) * 2

    def pixel(self, x: int, y: int, color: int | None = None) -> int:
        offset = self._offset(int(x), int(y))
        if offset is None:
            return BLACK
        if color is None:
            return self.buffer[offset] | (self.buffer[offset + 1] << 8)
        color &= 0xFFFF
        self.buffer[offset] = color & 0xFF
        self.buffer[offset + 1] = (color >> 8) & 0xFF
        return color

    def fill(self, color: int) -> "Canvas":
        self.buffer[:] = _pack565(color) * (self.width * self.height)
        return self

    def clear(self) -> "Canvas":
        return self.fill(BLACK)

    def hline(self, x: int, y: int, width: int, color: int) -> "Canvas":
        x = int(x)
        y = int(y)
        width = int(width)
        if width <= 0 or y < 0 or y >= self.height:
            return self
        start = max(0, x)
        end = min(self.width, x + width)
        if end <= start:
            return self
        row_offset = ((y * self.width) + start) * 2
        self.buffer[row_offset : row_offset + ((end - start) * 2)] = _pack565(color) * (end - start)
        return self

    def vline(self, x: int, y: int, height: int, color: int) -> "Canvas":
        x = int(x)
        y = int(y)
        height = int(height)
        if height <= 0 or x < 0 or x >= self.width:
            return self
        start = max(0, y)
        end = min(self.height, y + height)
        packed = _pack565(color)
        for yy in range(start, end):
            offset = ((yy * self.width) + x) * 2
            self.buffer[offset : offset + 2] = packed
        return self

    def fill_rect(self, x: int, y: int, width: int, height: int, color: int) -> "Canvas":
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
        if width <= 0 or height <= 0:
            return self
        start_x = max(0, x)
        start_y = max(0, y)
        end_x = min(self.width, x + width)
        end_y = min(self.height, y + height)
        if end_x <= start_x or end_y <= start_y:
            return self
        row = _pack565(color) * (end_x - start_x)
        for yy in range(start_y, end_y):
            offset = ((yy * self.width) + start_x) * 2
            self.buffer[offset : offset + len(row)] = row
        return self

    def rect(self, x: int, y: int, width: int, height: int, color: int) -> "Canvas":
        if width <= 0 or height <= 0:
            return self
        self.hline(x, y, width, color)
        self.hline(x, y + height - 1, width, color)
        self.vline(x, y, height, color)
        self.vline(x + width - 1, y, height, color)
        return self

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int) -> "Canvas":
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return self
```

Modify `python/picofb/__init__.py` to import directly:

```python
"""Small RGB565 framebuffer drawing library for the PicoCalc Luckfox Lyra."""

from .canvas import Canvas
from .colors import BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW, color565

try:
    from .display import Display
except ImportError:
    Display = None  # type: ignore[assignment]

__all__ = [
    "BLACK",
    "BLUE",
    "CYAN",
    "Canvas",
    "Display",
    "GREEN",
    "MAGENTA",
    "RED",
    "WHITE",
    "YELLOW",
    "color565",
]
```

- [ ] **Step 4: Run color and canvas tests**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest tests.test_picofb_colors tests.test_picofb_canvas
```

Expected: `Ran 9 tests` and `OK`.

- [ ] **Step 5: Commit**

```powershell
git add python/picofb/__init__.py python/picofb/canvas.py tests/test_picofb_canvas.py
git commit -m "Add PicoFB canvas primitives"
```

---

### Task 3: Text, Blit, And Image Adapter

**Files:**
- Create: `python/picofb/font.py`
- Modify: `python/picofb/canvas.py`
- Modify: `tests/test_picofb_canvas.py`

- [ ] **Step 1: Extend canvas tests for text, blit, and image conversion**

Append these tests inside `CanvasTests` in `tests/test_picofb_canvas.py`:

```python
    def test_text_draws_builtin_bitmap_font(self):
        canvas = Canvas(10, 10)
        canvas.text("A", 0, 0, WHITE)
        lit_pixels = sum(1 for y in range(7) for x in range(5) if canvas.pixel(x, y) == WHITE)
        self.assertGreater(lit_pixels, 8)

    def test_blit_canvas_clips(self):
        source = Canvas(2, 2)
        source.fill(RED)
        target = Canvas(3, 3)
        target.blit(source, 2, 2)
        self.assertEqual(target.pixel(2, 2), RED)
        self.assertEqual(target.pixel(1, 1), BLACK)

    def test_image_adapter_accepts_rgb_like_object(self):
        class FakeImage:
            size = (2, 1)
            mode = "RGB"

            def convert(self, mode):
                self.mode = mode
                return self

            def getdata(self):
                return [(255, 0, 0), (0, 0, 255)]

        canvas = Canvas(2, 1)
        canvas.image(FakeImage())
        self.assertEqual(canvas.pixel(0, 0), RED)
        self.assertEqual(canvas.pixel(1, 0), BLUE)
```

- [ ] **Step 2: Run the canvas tests to verify they fail**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest tests.test_picofb_canvas
```

Expected: `AttributeError` for missing `text`, `blit`, or `image`.

- [ ] **Step 3: Add the bitmap font**

Create `python/picofb/font.py`:

```python
"""Small 5x7 bitmap font used by PicoFB Canvas.text."""

FONT_5X7 = {
    " ": (0, 0, 0, 0, 0, 0, 0),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "-": (0, 0, 0, 31, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ":": (0, 12, 12, 0, 12, 12, 0),
    "/": (1, 2, 4, 8, 16, 0, 0),
    "?": (14, 17, 1, 2, 4, 0, 4),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31),
    "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (1, 1, 1, 1, 17, 17, 14),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 21, 10),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
}
```

- [ ] **Step 4: Add `text`, `blit`, and `image` to `Canvas`**

Modify `python/picofb/canvas.py`:

```python
"""Bytearray-backed RGB565 drawing surface."""

from __future__ import annotations

from typing import Any

from .colors import BLACK, color565
from .font import FONT_5X7


def _pack565(color: int) -> bytes:
    color &= 0xFFFF
    return bytes((color & 0xFF, (color >> 8) & 0xFF))


class Canvas:
    """In-memory RGB565 canvas with clipping drawing operations."""

    def __init__(self, width: int, height: int, background: int = BLACK):
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = int(width)
        self.height = int(height)
        self.buffer = bytearray(self.width * self.height * 2)
        if background != BLACK:
            self.fill(background)

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def _offset(self, x: int, y: int) -> int | None:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None
        return ((y * self.width) + x) * 2

    def pixel(self, x: int, y: int, color: int | None = None) -> int:
        offset = self._offset(int(x), int(y))
        if offset is None:
            return BLACK
        if color is None:
            return self.buffer[offset] | (self.buffer[offset + 1] << 8)
        color &= 0xFFFF
        self.buffer[offset] = color & 0xFF
        self.buffer[offset + 1] = (color >> 8) & 0xFF
        return color

    def fill(self, color: int) -> "Canvas":
        self.buffer[:] = _pack565(color) * (self.width * self.height)
        return self

    def clear(self) -> "Canvas":
        return self.fill(BLACK)

    def hline(self, x: int, y: int, width: int, color: int) -> "Canvas":
        x = int(x)
        y = int(y)
        width = int(width)
        if width <= 0 or y < 0 or y >= self.height:
            return self
        start = max(0, x)
        end = min(self.width, x + width)
        if end <= start:
            return self
        row_offset = ((y * self.width) + start) * 2
        self.buffer[row_offset : row_offset + ((end - start) * 2)] = _pack565(color) * (end - start)
        return self

    def vline(self, x: int, y: int, height: int, color: int) -> "Canvas":
        x = int(x)
        y = int(y)
        height = int(height)
        if height <= 0 or x < 0 or x >= self.width:
            return self
        start = max(0, y)
        end = min(self.height, y + height)
        packed = _pack565(color)
        for yy in range(start, end):
            offset = ((yy * self.width) + x) * 2
            self.buffer[offset : offset + 2] = packed
        return self

    def fill_rect(self, x: int, y: int, width: int, height: int, color: int) -> "Canvas":
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
        if width <= 0 or height <= 0:
            return self
        start_x = max(0, x)
        start_y = max(0, y)
        end_x = min(self.width, x + width)
        end_y = min(self.height, y + height)
        if end_x <= start_x or end_y <= start_y:
            return self
        row = _pack565(color) * (end_x - start_x)
        for yy in range(start_y, end_y):
            offset = ((yy * self.width) + start_x) * 2
            self.buffer[offset : offset + len(row)] = row
        return self

    def rect(self, x: int, y: int, width: int, height: int, color: int) -> "Canvas":
        if width <= 0 or height <= 0:
            return self
        self.hline(x, y, width, color)
        self.hline(x, y + height - 1, width, color)
        self.vline(x, y, height, color)
        self.vline(x + width - 1, y, height, color)
        return self

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int) -> "Canvas":
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return self

    def text(
        self,
        value: object,
        x: int,
        y: int,
        color: int,
        background: int | None = None,
        scale: int = 1,
    ) -> "Canvas":
        scale = max(1, int(scale))
        start_x = int(x)
        cursor_x = start_x
        cursor_y = int(y)
        for char in str(value):
            if char == "\n":
                cursor_x = start_x
                cursor_y += 8 * scale
                continue
            glyph = FONT_5X7.get(char) or FONT_5X7.get(char.upper()) or FONT_5X7["?"]
            for row_index, row_bits in enumerate(glyph):
                for col_index in range(5):
                    bit_set = row_bits & (1 << (4 - col_index))
                    px = cursor_x + (col_index * scale)
                    py = cursor_y + (row_index * scale)
                    if bit_set:
                        self.fill_rect(px, py, scale, scale, color)
                    elif background is not None:
                        self.fill_rect(px, py, scale, scale, background)
            if background is not None:
                self.fill_rect(cursor_x + (5 * scale), cursor_y, scale, 7 * scale, background)
            cursor_x += 6 * scale
        return self

    def blit(
        self,
        source: "Canvas | bytes | bytearray | memoryview",
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
        source_stride: int | None = None,
    ) -> "Canvas":
        if isinstance(source, Canvas):
            src_buffer = source.buffer
            src_width = source.width
            src_height = source.height
            stride = source.width * 2
        else:
            if width is None or height is None:
                raise ValueError("width and height are required when blitting a raw buffer")
            src_buffer = memoryview(source)
            src_width = int(width)
            src_height = int(height)
            stride = int(source_stride or (src_width * 2))
        dest_x = int(x)
        dest_y = int(y)
        for yy in range(src_height):
            target_y = dest_y + yy
            if target_y < 0 or target_y >= self.height:
                continue
            for xx in range(src_width):
                target_x = dest_x + xx
                if target_x < 0 or target_x >= self.width:
                    continue
                src_offset = (yy * stride) + (xx * 2)
                color = src_buffer[src_offset] | (src_buffer[src_offset + 1] << 8)
                self.pixel(target_x, target_y, color)
        return self

    def image(self, image: Any, x: int = 0, y: int = 0) -> "Canvas":
        if not hasattr(image, "convert") or not hasattr(image, "getdata") or not hasattr(image, "size"):
            raise TypeError("image must be a Pillow-compatible object with convert(), getdata(), and size")
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        pixels = list(rgb_image.getdata())
        for yy in range(height):
            for xx in range(width):
                r, g, b = pixels[(yy * width) + xx][:3]
                self.pixel(int(x) + xx, int(y) + yy, color565(int(r), int(g), int(b)))
        return self
```

- [ ] **Step 5: Run canvas tests**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest tests.test_picofb_canvas
```

Expected: `Ran 8 tests` and `OK`.

- [ ] **Step 6: Commit**

```powershell
git add python/picofb/font.py python/picofb/canvas.py tests/test_picofb_canvas.py
git commit -m "Add PicoFB text and image drawing"
```

---

### Task 4: Display Metadata And Framebuffer Flush

**Files:**
- Create: `python/picofb/display.py`
- Create: `tests/test_picofb_display.py`
- Modify: `python/picofb/__init__.py`

- [ ] **Step 1: Write failing display tests**

Create `tests/test_picofb_display.py`:

```python
import tempfile
import unittest
from pathlib import Path

from picofb import RED, Display


class DisplayTests(unittest.TestCase):
    def make_fake_sysfs(self, root: Path, name: str = "fb0", bpp: str = "16", stride: str = "8"):
        fb = root / name
        fb.mkdir(parents=True)
        (fb / "virtual_size").write_text("4,3\n", encoding="ascii")
        (fb / "bits_per_pixel").write_text(bpp + "\n", encoding="ascii")
        (fb / "stride").write_text(stride + "\n", encoding="ascii")
        return fb

    def test_reads_framebuffer_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fake_sysfs(root)
            fb_path = root / "fb0-device"
            fb_path.write_bytes(bytes(24))
            display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
            self.assertEqual(display.size, (4, 3))
            self.assertEqual(display.width, 4)
            self.assertEqual(display.height, 3)
            self.assertEqual(display.bpp, 16)
            self.assertEqual(display.stride, 8)
            display.close()

    def test_rejects_non_rgb565_framebuffer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fake_sysfs(root, bpp="32")
            fb_path = root / "fb0-device"
            fb_path.write_bytes(bytes(48))
            with self.assertRaises(ValueError):
                Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")

    def test_show_writes_canvas_to_fake_framebuffer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fake_sysfs(root)
            fb_path = root / "fb0-device"
            fb_path.write_bytes(bytes(24))
            display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
            display.pixel(1, 1, RED)
            display.show()
            display.close()
            data = fb_path.read_bytes()
            offset = ((1 * 4) + 1) * 2
            self.assertEqual(data[offset : offset + 2], bytes([0x00, 0xF8]))

    def test_show_handles_padded_stride(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fake_sysfs(root, stride="12")
            fb_path = root / "fb0-device"
            fb_path.write_bytes(bytes(36))
            display = Display(str(fb_path), sysfs_root=str(root), fb_name="fb0")
            display.pixel(3, 2, RED)
            display.show()
            display.close()
            data = fb_path.read_bytes()
            offset = (2 * 12) + (3 * 2)
            self.assertEqual(data[offset : offset + 2], bytes([0x00, 0xF8]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the display tests to verify they fail**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest tests.test_picofb_display
```

Expected: `TypeError: 'NoneType' object is not callable` or import failure for `Display`.

- [ ] **Step 3: Implement `Display`**

Create `python/picofb/display.py`:

```python
"""Linux framebuffer display wrapper for PicoFB."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from .canvas import Canvas


class Display:
    """User-facing framebuffer display backed by a Canvas."""

    def __init__(
        self,
        path: str = "/dev/fb0",
        *,
        sysfs_root: str = "/sys/class/graphics",
        fb_name: str | None = None,
    ):
        self.path = Path(path)
        self.fb_name = fb_name or self.path.name
        self.sysfs_path = Path(sysfs_root) / self.fb_name
        self.width, self.height = self._read_pair("virtual_size")
        self.bpp = self._read_int("bits_per_pixel")
        self.stride = self._read_int("stride")
        if self.bpp != 16:
            raise ValueError(f"{self.path} must be 16 bpp RGB565, got {self.bpp} bpp")
        if self.stride < self.width * 2:
            raise ValueError(f"{self.path} stride {self.stride} is smaller than width * 2 ({self.width * 2})")
        self.canvas = Canvas(self.width, self.height)
        self._fb = self._open_framebuffer()

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    @property
    def buffer(self) -> bytearray:
        return self.canvas.buffer

    def _metadata_path(self, name: str) -> Path:
        return self.sysfs_path / name

    def _read_text(self, name: str) -> str:
        path = self._metadata_path(name)
        try:
            return path.read_text(encoding="ascii").strip()
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"missing framebuffer metadata: {path}") from exc

    def _read_int(self, name: str) -> int:
        value = self._read_text(name)
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"invalid integer in {self._metadata_path(name)}: {value!r}") from exc

    def _read_pair(self, name: str) -> tuple[int, int]:
        value = self._read_text(name)
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 2:
            raise ValueError(f"invalid pair in {self._metadata_path(name)}: {value!r}")
        return (int(parts[0]), int(parts[1]))

    def _open_framebuffer(self) -> BinaryIO:
        try:
            return self.path.open("r+b", buffering=0)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"framebuffer device not found: {self.path}") from exc
        except PermissionError as exc:
            raise PermissionError(f"permission denied opening {self.path}; add the user to the video group") from exc

    def close(self) -> None:
        if not self._fb.closed:
            self._fb.close()

    def __enter__(self) -> "Display":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def show(self) -> "Display":
        row_bytes = self.width * 2
        if self.stride == row_bytes:
            self._fb.seek(0)
            self._fb.write(self.canvas.buffer)
        else:
            for y in range(self.height):
                src_offset = y * row_bytes
                self._fb.seek(y * self.stride)
                self._fb.write(self.canvas.buffer[src_offset : src_offset + row_bytes])
        self._fb.flush()
        return self

    def pixel(self, *args, **kwargs):
        return self.canvas.pixel(*args, **kwargs)

    def fill(self, *args, **kwargs) -> "Display":
        self.canvas.fill(*args, **kwargs)
        return self

    def clear(self) -> "Display":
        self.canvas.clear()
        return self

    def hline(self, *args, **kwargs) -> "Display":
        self.canvas.hline(*args, **kwargs)
        return self

    def vline(self, *args, **kwargs) -> "Display":
        self.canvas.vline(*args, **kwargs)
        return self

    def line(self, *args, **kwargs) -> "Display":
        self.canvas.line(*args, **kwargs)
        return self

    def rect(self, *args, **kwargs) -> "Display":
        self.canvas.rect(*args, **kwargs)
        return self

    def fill_rect(self, *args, **kwargs) -> "Display":
        self.canvas.fill_rect(*args, **kwargs)
        return self

    def text(self, *args, **kwargs) -> "Display":
        self.canvas.text(*args, **kwargs)
        return self

    def blit(self, *args, **kwargs) -> "Display":
        self.canvas.blit(*args, **kwargs)
        return self

    def image(self, *args, **kwargs) -> "Display":
        self.canvas.image(*args, **kwargs)
        return self
```

Modify `python/picofb/__init__.py`:

```python
"""Small RGB565 framebuffer drawing library for the PicoCalc Luckfox Lyra."""

from .canvas import Canvas
from .colors import BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW, color565
from .display import Display

__all__ = [
    "BLACK",
    "BLUE",
    "CYAN",
    "Canvas",
    "Display",
    "GREEN",
    "MAGENTA",
    "RED",
    "WHITE",
    "YELLOW",
    "color565",
]
```

- [ ] **Step 4: Run all host tests**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest discover -s tests -p "test_picofb*.py"
```

Expected: all PicoFB tests pass with `OK`.

- [ ] **Step 5: Commit**

```powershell
git add python/picofb/display.py python/picofb/__init__.py tests/test_picofb_display.py
git commit -m "Add PicoFB framebuffer display"
```

---

### Task 5: Remote Python Package Sync

**Files:**
- Modify: `tools/luckfox-dev.py`

- [ ] **Step 1: Add a remote package sync path to `tools/luckfox-dev.py`**

Modify `tools/luckfox-dev.py` with these changes:

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PYTHON_DIR = PROJECT_ROOT / "python"
REMOTE_PYTHON_DIR = f"{DEFAULT_REMOTE_DIR}/python"
```

Add this function after `adb_shell`:

```python
def sync_python_tree() -> None:
    if not LOCAL_PYTHON_DIR.exists():
        return
    say(f"Syncing {LOCAL_PYTHON_DIR} -> {REMOTE_PYTHON_DIR}")
    adb_shell(f"mkdir -p {q(DEFAULT_REMOTE_DIR)}; rm -rf {q(REMOTE_PYTHON_DIR)}")
    adb(["push", str(LOCAL_PYTHON_DIR), REMOTE_PYTHON_DIR])
    adb_shell(f"chown -R neusse:neusse {q(REMOTE_PYTHON_DIR)}")
```

Replace `remote_python_command` with:

```python
def remote_python_command(remote_path: str, argv: list[str]) -> str:
    args = " ".join(q(arg) for arg in argv)
    command = (
        "cd "
        + q(DEFAULT_REMOTE_DIR)
        + " && "
        + ". ~/venvs/nonroot/bin/activate 2>/dev/null || true; "
        + "PYTHONPATH="
        + q(REMOTE_PYTHON_DIR)
        + "${PYTHONPATH:+:$PYTHONPATH} "
        + "python "
        + q(remote_path)
        + (" " + args if args else "")
    )
    return "su - neusse -c " + q(command)
```

In `cmd_runpy`, insert `sync_python_tree()` immediately before uploading the script:

```python
def cmd_runpy(args: argparse.Namespace) -> None:
    local = Path(args.file)
    remote = f"{DEFAULT_REMOTE_DIR}/{local.name}"
    sync_python_tree()
    say(f"Uploading {local} -> {remote}")
    adb_shell(f"mkdir -p {q(DEFAULT_REMOTE_DIR)}; chown -R neusse:neusse {q(DEFAULT_REMOTE_DIR)}")
    adb(["push", str(local), remote])
    adb_shell(f"chown neusse:neusse {q(remote)}")
    adb_shell(remote_python_command(remote, args.args))
```

- [ ] **Step 2: Check helper syntax locally**

```powershell
python -m py_compile .\tools\luckfox-dev.py
```

Expected: no output and exit code `0`.

- [ ] **Step 3: Verify remote status still works**

```powershell
python .\tools\luckfox-dev.py status
```

Expected: ADB lists one connected device and prints `---device---`, `---network---`, `---python---`, and `---swap---`.

- [ ] **Step 4: Commit**

```powershell
git add tools/luckfox-dev.py
git commit -m "Sync local Python package for Luckfox runpy"
```

---

### Task 6: Framebuffer Demo And Device Permissions

**Files:**
- Create: `examples/python/fb_demo.py`
- Create: `scripts/device/enable-framebuffer-user.sh`

- [ ] **Step 1: Create the device permission helper**

Create `scripts/device/enable-framebuffer-user.sh`:

```sh
#!/bin/sh
set -eu

user="${1:-neusse}"

if ! id "$user" >/dev/null 2>&1; then
    echo "missing user: $user" >&2
    exit 1
fi

if ! grep -q '^video:' /etc/group; then
    echo 'video:x:44:' >> /etc/group
fi

members="$(awk -F: '$1 == "video" { print $4 }' /etc/group)"
case ",$members," in
    *,"$user",*) ;;
    *)
        sed -i "/^video:/ s/$/,$user/" /etc/group
        sed -i 's/:,/:/' /etc/group
        ;;
esac

if [ -e /dev/fb0 ]; then
    chgrp video /dev/fb0 2>/dev/null || true
    chmod 0660 /dev/fb0 2>/dev/null || true
fi

echo "$user is configured for framebuffer access"
```

- [ ] **Step 2: Create the framebuffer demo**

Create `examples/python/fb_demo.py`:

```python
#!/usr/bin/env python3
"""Draw a PicoFB smoke-test image on the physical PicoCalc screen."""

from picofb import BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW, Display, color565


def draw_demo(display: Display) -> None:
    width, height = display.size
    colors = [RED, YELLOW, GREEN, CYAN, BLUE, MAGENTA]
    bar_width = max(1, width // len(colors))
    display.fill(BLACK)
    for index, color in enumerate(colors):
        display.fill_rect(index * bar_width, 0, bar_width, 48, color)
    display.rect(0, 0, width, height, WHITE)
    display.text("PICOFB", 12, 64, WHITE, scale=2)
    display.text("LUCKFOX LYRA", 12, 88, GREEN)
    display.text(f"{width}X{height} RGB565", 12, 104, CYAN)
    display.fill_rect(20, 130, 120, 48, color565(20, 40, 80))
    display.rect(20, 130, 120, 48, YELLOW)
    display.text("FRAMEBUFFER", 28, 150, WHITE)
    display.line(0, height - 1, width - 1, 0, RED)
    display.line(0, 0, width - 1, height - 1, BLUE)
    for offset in range(0, 80, 10):
        display.rect(180 + offset // 2, 150 + offset // 3, 80 - offset, 80 - offset, color565(255 - offset, offset * 2, 120))
    display.text("RUNNING AS USER", 12, height - 24, WHITE)
    display.show()


def main() -> int:
    with Display("/dev/fb0") as display:
        draw_demo(display)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Push and run the permission helper**

```powershell
$adb = "C:\Users\georg\AppData\Local\Android\Sdk\platform-tools\adb.exe"
& $adb push .\scripts\device\enable-framebuffer-user.sh /tmp/enable-framebuffer-user.sh
& $adb shell "sh /tmp/enable-framebuffer-user.sh neusse"
```

Expected: `neusse is configured for framebuffer access`.

- [ ] **Step 4: Reconnect the `neusse` session**

Power-cycle or run:

```powershell
python .\tools\luckfox-dev.py shell
```

Expected on device:

```sh
id neusse
```

Expected output includes `video` in the group list. If an existing SSH session does not show `video`, log out and back in.

- [ ] **Step 5: Run the physical framebuffer demo**

```powershell
python .\tools\luckfox-dev.py runpy .\examples\python\fb_demo.py
```

Expected:
- Host output shows `Syncing ...\python -> /home/neusse/luckfox-dev/python`.
- Host output shows `Uploading examples\python\fb_demo.py -> /home/neusse/luckfox-dev/fb_demo.py`.
- PicoCalc screen changes to color bars, `PICOFB`, `LUCKFOX LYRA`, and diagonal lines.

- [ ] **Step 6: Commit**

```powershell
git add examples/python/fb_demo.py scripts/device/enable-framebuffer-user.sh
git commit -m "Add PicoFB framebuffer demo"
```

---

### Task 7: Documentation And Checklist Update

**Files:**
- Create: `docs/picofb.md`
- Modify: `luckfox-checklist.md`

- [ ] **Step 1: Create PicoFB documentation**

Create `docs/picofb.md`:

```markdown
# PicoFB

PicoFB is a small Python RGB565 framebuffer library for the Luckfox Lyra Model B inside the ClockworkPi PicoCalc.

Current target:

- Device: `/dev/fb0`
- Driver: `ili9488drmfb`
- Resolution: `320x320`
- Format: 16 bpp RGB565
- Stride: 640 bytes

## Host Test

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest discover -s tests -p "test_picofb*.py"
```

## Run On The PicoCalc

```powershell
python .\tools\luckfox-dev.py runpy .\examples\python\fb_demo.py
```

`tools/luckfox-dev.py runpy` syncs the local `python/` package tree to `/home/neusse/luckfox-dev/python` and sets `PYTHONPATH` before running the script as `neusse`.

## Permission Setup

`/dev/fb0` should be writable by users in the `video` group.

```powershell
$adb = "C:\Users\georg\AppData\Local\Android\Sdk\platform-tools\adb.exe"
& $adb push .\scripts\device\enable-framebuffer-user.sh /tmp/enable-framebuffer-user.sh
& $adb shell "sh /tmp/enable-framebuffer-user.sh neusse"
```

Log out and back in after changing groups.

## Minimal Example

```python
from picofb import Display, color565

with Display("/dev/fb0") as display:
    display.fill(color565(0, 0, 0))
    display.text("Hello", 8, 8, color565(255, 255, 255))
    display.rect(20, 40, 100, 50, color565(0, 255, 0))
    display.show()
```

## Notes

- Text uses a built-in 5x7 bitmap font.
- Lowercase letters render through uppercase fallback.
- Drawing clips silently when coordinates are outside the screen.
- The library does not restore the Linux console after drawing.
```

- [ ] **Step 2: Update the checklist**

Add this section to `luckfox-checklist.md` under the software/tooling or framebuffer section:

```markdown
### PicoFB Framebuffer Library

- [ ] Implement `python/picofb` RGB565 framebuffer library from `docs/superpowers/plans/2026-06-16-picofb-implementation-plan.md`.
- [ ] Run host tests with `python -m unittest discover -s tests -p "test_picofb*.py"`.
- [ ] Run `examples/python/fb_demo.py` on the PicoCalc with `tools/luckfox-dev.py runpy`.
- [ ] Confirm `neusse` has `video` group access and can open `/dev/fb0` without root.
- [ ] Capture any next library requests after the first physical screen demo.
```

- [ ] **Step 3: Run final host tests**

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest discover -s tests -p "test_picofb*.py"
```

Expected: all PicoFB tests pass with `OK`.

- [ ] **Step 4: Run final device smoke test**

```powershell
python .\tools\luckfox-dev.py runpy .\examples\python\fb_demo.py
```

Expected: the physical PicoCalc screen shows the PicoFB demo.

- [ ] **Step 5: Commit**

```powershell
git add docs/picofb.md luckfox-checklist.md
git commit -m "Document PicoFB framebuffer workflow"
```

---

## Self-Review

- Spec coverage:
  - Pure Python package: Tasks 1-4.
  - No required PyPI dependencies: Tasks 1-4 use stdlib only; image adapter is duck-typed and optional.
  - Direct `/dev/fb0` output: Task 4 and Task 6.
  - Runtime detection from `/sys/class/graphics/fb0`: Task 4.
  - RGB565 buffer and drawing primitives: Tasks 1-3.
  - Demo script: Task 6.
  - Permission path for non-root `neusse`: Task 6.
  - Host/device tests: Tasks 1-7.
  - Packaging under `python/picofb/` and `examples/python/fb_demo.py`: Tasks 1-6.
- Placeholder scan:
  - No unfinished placeholder steps remain.
  - Commands use concrete Windows PowerShell paths and repo-relative paths.
- Type consistency:
  - `Canvas` and `Display` expose matching drawing methods.
  - RGB565 color values are integers throughout.
  - `Display.image()` delegates to `Canvas.image()` and returns `Display` for chaining.
