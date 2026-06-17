"""Bubble Universe model for PicoCalc framebuffer apps."""

from __future__ import annotations

import math

from picofb import BLACK, color565


# Total virtual curve positions in the effect.
# Allowed: integer >= 1. Practical PicoCalc range: 128-512.
# Actual drawn curve count is CURVECOUNT // CURVESTEP, so raising this only has
# a visible effect when it increases that quotient.
CURVECOUNT = 256

# Spacing between drawn curves. Lower values draw more curves and make the
# image denser/brighter; higher values draw fewer curves and run faster.
# Allowed: integer 1..CURVECOUNT. If greater than CURVECOUNT, nothing draws.
# Practical PicoCalc range: 4-32. Impressive-but-still-fast range: 8-12.
CURVESTEP = 16

# Points plotted per curve. This is the main detail knob: higher values make
# longer, richer tendrils but cost CPU every frame.
# Allowed: integer >= 1.
# Color-safe/no-clamp range with the current palette formula: 1-64.
# Values above 64 still draw more geometry, but later green values saturate at
# 255 unless the palette formula is changed.
# Practical PicoCalc range: 64-160. Try 96 or 128 for a denser effect.
ITERATIONS = 64
PI = math.pi

# Sine/cosine lookup table size as a power of two. 12 means 4096 entries.
# Higher values improve angular precision but use more RAM and slightly more
# cache; lower values are faster/coarser.
# Allowed: integer >= 8. Practical PicoCalc range: 10-16.
# Memory use is about 2 * (1 << SINTABLEPOWER) Python integers, so 16 works but
# is much larger than 12.
SINTABLEPOWER = 12
SINTABLEENTRIES = 1 << SINTABLEPOWER

# Phase advance between neighboring curves for the two coupled oscillators.
# These ratios shape the spiral/lissajous structure. Small denominator changes
# can make the image tighter, wider, more symmetric, or more chaotic.
# Denominators must be non-zero. Good ANG1 denominator trials: 181, 197, 211,
# 223, 235, 251, 269, 307. ANG2 currently uses int(2 * pi) == 6.
ANG1INC = (CURVESTEP * SINTABLEENTRIES) // 235
ANG2INC = (CURVESTEP * SINTABLEENTRIES) // int(2 * PI)

# Interactive controls. SCALESPEED is the zoom multiplier per keypress,
# MOVESPEED is pixels per pan keypress, and ANIMSPEEDCHANGE is the animation
# speed delta per keypress.
# SCALESPEED practical range: 1.01-1.20. MOVESPEED practical range: 1-12 pixels.
# ANIMSPEEDCHANGE practical range: 0.005-0.10.
SCALESPEED = 1.04
MOVESPEED = 2.0
ANIMSPEEDCHANGE = 0.02
CURVE_STEPS = CURVECOUNT // CURVESTEP
PALETTE_LEN = (CURVE_STEPS * ITERATIONS) + 1


def calculate_color(curve_index: int, iteration: int) -> int:
    i = curve_index >> 1
    red_level = (i >> 4) & 0x07
    green_level = iteration >> 2
    red = (255 * red_level) // 7
    green = (255 * green_level) // 15
    blue = (510 - (red + green)) >> 1
    # RGB565 input channels must be 0..255. With the current formula, green is
    # naturally 0..255 only for iteration 0..63. Larger ITERATIONS still add
    # geometry, but green will clamp to 255 for later points.
    return color565(
        max(0, min(255, red)),
        max(0, min(255, green)),
        max(0, min(255, blue)),
    )


class BubbleUniverse:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.scale_mul = int(height * PI / 2)
        self.sin_table, self.cos_table = self._create_tables()
        self.palette = self._create_palette()
        self.reset()

    def reset(self) -> None:
        self.speed = 0.2
        self.old_speed = 0.0
        self.size = 1.0
        self.x_offset = 0
        self.y_offset = 0
        self.animation_time = 0.0

    def step(self, delta_ms: float) -> None:
        self.animation_time += delta_ms * self.speed

    def apply_action(self, action: str | None) -> None:
        if action == "reset":
            self.reset()
        elif action == "speed_down":
            self.speed -= ANIMSPEEDCHANGE / self.size
        elif action == "speed_up":
            self.speed += ANIMSPEEDCHANGE / self.size
        elif action == "zoom_in":
            self.size *= SCALESPEED
            self.x_offset = int(self.x_offset * SCALESPEED)
            self.y_offset = int(self.y_offset * SCALESPEED)
        elif action == "zoom_out":
            self.size /= SCALESPEED
            self.x_offset = int(self.x_offset / SCALESPEED)
            self.y_offset = int(self.y_offset / SCALESPEED)
        elif action == "pause":
            self.speed, self.old_speed = self.old_speed, self.speed
        elif action == "left":
            self.x_offset += int(MOVESPEED)
        elif action == "right":
            self.x_offset -= int(MOVESPEED)
        elif action == "up":
            self.y_offset += int(MOVESPEED)
        elif action == "down":
            self.y_offset -= int(MOVESPEED)

    def render(self, canvas) -> None:
        canvas.fill(BLACK)
        ang1_start = int(self.animation_time)
        ang2_start = int(self.animation_time)
        xs: list[int] = []
        ys: list[int] = []
        colors: list[int] = []

        for curve_idx in range(CURVE_STEPS):
            curve_index = curve_idx * CURVESTEP
            x = 0
            y = 0
            for iteration in range(ITERATIONS):
                idx1 = (ang1_start + x) & (SINTABLEENTRIES - 1)
                idx2 = (ang2_start + y) & (SINTABLEENTRIES - 1)

                sin1 = self.sin_table[idx1]
                cos1 = self.cos_table[idx1]
                sin2 = self.sin_table[idx2]
                cos2 = self.cos_table[idx2]

                x = sin1 + sin2
                y = cos1 + cos2

                px = int((x * self.scale_mul * self.size) / (1 << SINTABLEPOWER)) + self.x_offset
                py = int((y * self.scale_mul * self.size) / (1 << SINTABLEPOWER)) + self.y_offset

                if -self.center_x < px < self.center_x and -self.center_y < py < self.center_y:
                    sx = self.center_x + px
                    sy = self.center_y + py
                    xs.append(sx)
                    ys.append(sy)
                    colors.append(self.palette[1 + (curve_idx * ITERATIONS) + iteration])

            ang1_start += ANG1INC
            ang2_start += ANG2INC

        canvas.scatter_rgb565(xs, ys, colors)

    @staticmethod
    def _create_tables() -> tuple[list[int], list[int]]:
        sin_table = [0] * SINTABLEENTRIES
        cos_table = [0] * SINTABLEENTRIES
        for index in range(SINTABLEENTRIES):
            angle = index * 2 * PI / SINTABLEENTRIES
            sin_table[index] = int(math.sin(angle) * SINTABLEENTRIES / (2 * PI))
            cos_table[index] = int(math.sin(angle + (PI / 2)) * SINTABLEENTRIES / (2 * PI))
        return sin_table, cos_table

    @staticmethod
    def _create_palette() -> list[int]:
        palette = [BLACK] * PALETTE_LEN
        for curve_idx in range(CURVE_STEPS):
            curve_index = curve_idx * CURVESTEP
            for iteration in range(ITERATIONS):
                palette[1 + (curve_idx * ITERATIONS) + iteration] = calculate_color(curve_index, iteration)
        return palette
