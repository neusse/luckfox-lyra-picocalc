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
