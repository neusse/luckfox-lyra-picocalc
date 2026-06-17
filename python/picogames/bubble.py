"""Bubble Universe model for PicoCalc framebuffer apps."""

from __future__ import annotations

import math

from picofb import BLACK, color565


CURVECOUNT = 256
CURVESTEP = 16
ITERATIONS = 64
PI = math.pi
SINTABLEPOWER = 12
SINTABLEENTRIES = 1 << SINTABLEPOWER
ANG1INC = (CURVESTEP * SINTABLEENTRIES) // 235
ANG2INC = (CURVESTEP * SINTABLEENTRIES) // int(2 * PI)
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
    return color565(red, green, max(0, min(255, blue)))


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
                    canvas.pixel(sx, sy, self.palette[1 + (curve_idx * ITERATIONS) + iteration])

            ang1_start += ANG1INC
            ang2_start += ANG2INC

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
