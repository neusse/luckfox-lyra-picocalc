#!/usr/bin/env python3
"""Fancy analog clock for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from picofb import Display, color565
from picoterm.appkeys import is_app_exit_key
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


def hex565(value: int) -> int:
    return color565((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)


BG = hex565(0x0B0F14)
FACE = hex565(0x111827)
FACE_SHADOW = hex565(0x0F172A)
RING_OUTER = hex565(0x8B6B1F)
RING_INNER = hex565(0xF0C75E)
TICK_MAJOR = hex565(0xE2E8F0)
TICK_MINOR = hex565(0xAAAA00)
ACCENT = hex565(0x38BDF8)
HAND_HOUR = hex565(0xF59E0B)
HAND_MIN = hex565(0xE2E8F0)
PIVOT = hex565(0xEF4444)
SECOND_HAND = hex565(0xFF3B30)
TEXT = hex565(0xF8FAFC)
DATE_BG = hex565(0x0B1220)
DATE_OUTLINE = hex565(0xF59E0B)
DATE_TEXT = hex565(0xF8FAFC)
SUBDIAL_FACE = hex565(0x555555)
CHIME_ON_COLOR = hex565(0x3AD98A)
CHIME_OFF_COLOR = hex565(0xFF5A5A)
MOON_LIGHT = hex565(0xE5E7EB)
MOON_DARK = hex565(0x1F2937)
MOON_RING = hex565(0x9CA3AF)
CHIMES_TEXT = hex565(0x64748B)

DAY_NAMES = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


def polar_to_xy(cx: int, cy: int, angle_deg: float, radius: float) -> tuple[float, float]:
    rad = math.radians(angle_deg - 90.0)
    return cx + math.cos(rad) * radius, cy + math.sin(rad) * radius


def fill_circle(canvas, cx: int, cy: int, radius: int, color: int) -> None:
    radius = int(radius)
    for dy in range(-radius, radius + 1):
        width = int(math.sqrt(max(0, radius * radius - dy * dy)))
        canvas.hline(cx - width, cy + dy, width * 2 + 1, color)


def circle_outline(canvas, cx: int, cy: int, radius: int, color: int, *, step_degrees: int = 2) -> None:
    last = None
    for angle in range(0, 361, step_degrees):
        x, y = polar_to_xy(cx, cy, angle, radius)
        point = (int(round(x)), int(round(y)))
        if last is not None:
            canvas.line(last[0], last[1], point[0], point[1], color)
        last = point


def draw_ring(canvas, cx: int, cy: int, radius: int) -> None:
    fill_circle(canvas, cx, cy, radius, RING_OUTER)
    circle_outline(canvas, cx, cy, radius, RING_INNER)
    fill_circle(canvas, cx, cy, radius - 6, FACE)
    circle_outline(canvas, cx, cy, radius - 6, RING_INNER)
    fill_circle(canvas, cx, cy, radius - 12, FACE_SHADOW)


def draw_hand(
    canvas,
    cx: int,
    cy: int,
    angle_deg: float,
    length: float,
    color: int,
    *,
    thickness: int = 1,
    tail: float = 0,
) -> None:
    x0, y0 = polar_to_xy(cx, cy, angle_deg, -tail)
    x1, y1 = polar_to_xy(cx, cy, angle_deg, length)
    rad = math.radians(angle_deg - 90.0)
    perp_x = -math.sin(rad)
    perp_y = math.cos(rad)
    half = max(0, thickness // 2)
    for index in range(-half, half + 1):
        ox = int(round(perp_x * index))
        oy = int(round(perp_y * index))
        canvas.line(int(x0 + ox), int(y0 + oy), int(x1 + ox), int(y1 + oy), color)


def draw_text(canvas, value: str, x: int, y: int, color: int, *, size: int = 16, font: str = "Decker") -> None:
    try:
        canvas.text_ttf(value, x, y, color, font=font, size=size)
    except Exception:
        scale = 2 if size >= 18 else 1
        canvas.text(value, x, y, color, scale=scale)


def draw_center_text(canvas, value: str, cx: int, cy: int, color: int, *, size: int = 16) -> None:
    width = int(len(value) * size * 0.58)
    height = size
    draw_text(canvas, value, cx - width // 2, cy - height // 2, color, size=size)


def _julian_day(year: int, month: int, day: int) -> int:
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + (a // 4)
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524


def moon_phase_fraction(tt: time.struct_time) -> float:
    ref_jd = _julian_day(2000, 1, 6)
    jd = _julian_day(tt.tm_year, tt.tm_mon, tt.tm_mday)
    return ((jd - ref_jd) % 29.53059) / 29.53059


def draw_moon(canvas, cx: int, cy: int, radius: int, tt: time.struct_time) -> None:
    phase = moon_phase_fraction(tt)
    fill_circle(canvas, cx, cy, radius, MOON_LIGHT)
    if phase <= 0.5:
        shadow_x = cx - int(phase * 4 * radius)
    else:
        shadow_x = cx + int((1 - phase) * 4 * radius)
    fill_circle(canvas, shadow_x, cy, radius, MOON_DARK)
    circle_outline(canvas, cx, cy, radius, MOON_RING)


def draw_ticks(canvas, cx: int, cy: int, radius: int) -> None:
    for index in range(60):
        angle = index * 6
        is_hour = index % 5 == 0
        r_outer = radius - 4
        r_inner = radius - (18 if is_hour else 12)
        color = TICK_MAJOR if is_hour else TICK_MINOR
        x0, y0 = polar_to_xy(cx, cy, angle, r_outer)
        x1, y1 = polar_to_xy(cx, cy, angle, r_inner)
        canvas.line(int(x0), int(y0), int(x1), int(y1), color)
        if is_hour:
            dx, dy = polar_to_xy(cx, cy, angle, radius - 26)
            fill_circle(canvas, int(dx), int(dy), 2, ACCENT if index % 15 == 0 else TICK_MAJOR)


def draw_subdial(canvas, cx: int, cy: int, radius: int, second: int) -> None:
    fill_circle(canvas, cx, cy, radius, SUBDIAL_FACE)
    circle_outline(canvas, cx, cy, radius, RING_INNER)
    for index in range(12):
        angle = index * 30
        x0, y0 = polar_to_xy(cx, cy, angle, radius - 1)
        x1, y1 = polar_to_xy(cx, cy, angle, radius - (7 if index % 3 == 0 else 5))
        canvas.line(int(x0), int(y0), int(x1), int(y1), TICK_MAJOR if index % 3 == 0 else TICK_MINOR)
    sec_angle = second * 6.0
    draw_hand(canvas, cx, cy, sec_angle, radius - 4, SECOND_HAND, thickness=1, tail=6)
    tip_x, tip_y = polar_to_xy(cx, cy, sec_angle, radius - 3)
    fill_circle(canvas, int(tip_x), int(tip_y), 2, SECOND_HAND)
    fill_circle(canvas, cx, cy, 2, TEXT)


def render_clock(canvas, tt: time.struct_time | None = None, *, chimes_enabled: bool = False) -> None:
    tt = time.localtime() if tt is None else tt
    width, height = canvas.width, canvas.height
    cx = width // 2
    cy = height // 2
    radius = min(width, height) // 2 - 8

    canvas.fill(BG)
    draw_ring(canvas, cx, cy, radius)
    draw_ticks(canvas, cx, cy, radius)

    for text, angle in (("12", 0), ("3", 90), ("6", 180), ("9", 270)):
        tx, ty = polar_to_xy(cx, cy, angle, radius - 44)
        draw_center_text(canvas, text, int(tx), int(ty), TEXT, size=18)

    draw_center_text(canvas, "PicoCalc", cx, cy - 40, ACCENT, size=18)
    draw_center_text(canvas, "clockworkpi", cx, cy + 31, TEXT, size=13)
    draw_moon(canvas, cx, cy - 74, 18, tt)
    draw_subdial(canvas, cx, cy + 72, 22, tt.tm_sec)

    date_text = f"{DAY_NAMES[tt.tm_wday]} {tt.tm_mday:02d}"
    date_w = 46
    date_h = 18
    date_x = int(cx + radius * 0.35)
    date_y = int(cy - date_h // 2)
    canvas.fill_rect(date_x, date_y, date_w, date_h, DATE_BG)
    canvas.rect(date_x, date_y, date_w, date_h, DATE_OUTLINE)
    draw_center_text(canvas, date_text, date_x + date_w // 2, date_y + date_h // 2, DATE_TEXT, size=12)

    minute = tt.tm_min + (tt.tm_sec / 60.0)
    hour = (tt.tm_hour % 12) + (minute / 60.0)
    draw_hand(canvas, cx, cy, hour * 30.0, radius * 0.45, HAND_HOUR, thickness=5, tail=10)
    draw_hand(canvas, cx, cy, minute * 6.0, radius * 0.7, HAND_MIN, thickness=4, tail=14)
    fill_circle(canvas, cx, cy, 4, PIVOT)
    circle_outline(canvas, cx, cy, 4, TEXT)

    label = "Chimes:"
    dot_x = 10 + (len(label) * 6) + 8
    dot_y = height - 14
    canvas.text(label, 10, height - 18, CHIMES_TEXT)
    fill_circle(canvas, dot_x, dot_y, 3, CHIME_ON_COLOR if chimes_enabled else CHIME_OFF_COLOR)


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def require_console_tty(ttyname=None) -> None:
    ttyname = getattr(os, "ttyname", None) if ttyname is None else ttyname
    if ttyname is None:
        raise SystemExit("clock must be started from the PicoCalc console, not SSH or ADB")
    try:
        path = ttyname(0)
    except OSError as exc:
        raise SystemExit("clock must be started from the PicoCalc console, not SSH or ADB") from exc
    if not is_console_tty(path):
        raise SystemExit(f"clock must be started from the PicoCalc console; current terminal is {path}")


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def key_to_action(key: KeyPress | None) -> str | None:
    if key is None:
        return None
    if is_app_exit_key(key):
        return "quit"
    if key.name in (Key.BACKSPACE, Key.ESCAPE):
        return "quit"
    if key.name == Key.CHAR:
        if str(key.value).lower() == "q":
            return "quit"
        if str(key.value).lower() == "c":
            return "toggle_chimes"
        if str(key.value).lower() == "s":
            return "screenshot"
    return None


def screenshot_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path.home() / "screenshots" / f"fancy-clock-{stamp}.png"


def take_screenshot() -> str:
    output = screenshot_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["picocalc-screenshot", str(output)], check=True)
    return str(output)


def run_once(framebuffer: str = "/dev/fb0") -> int:
    with Display(framebuffer) as display:
        render_clock(display, time.localtime())
        display.show()
    return 0


def run_interactive(framebuffer: str = "/dev/fb0", keyboard_path: str | None = None) -> int:
    require_console_tty()
    chimes_enabled = False
    last_second = -1
    with RawTerminal(), Display(framebuffer) as display, open_keyboard(keyboard_path) as keyboard:
        while True:
            now = time.localtime()
            if now.tm_sec != last_second:
                last_second = now.tm_sec
                render_clock(display, now, chimes_enabled=chimes_enabled)
                display.show()

            action = key_to_action(keyboard.read_key(timeout=0.05))
            if action == "quit":
                return 0
            if action == "toggle_chimes":
                chimes_enabled = not chimes_enabled
                render_clock(display, time.localtime(), chimes_enabled=chimes_enabled)
                display.show()
            elif action == "screenshot":
                take_screenshot()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PicoCalc fancy analog clock")
    parser.add_argument("--fb", default="/dev/fb0")
    parser.add_argument("--keyboard", help="evdev keyboard path, default: auto-detect PicoCalc keyboard")
    parser.add_argument("--once", action="store_true", help="render one framebuffer frame and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.once:
        return run_once(args.fb)
    return run_interactive(args.fb, args.keyboard)


if __name__ == "__main__":
    raise SystemExit(main())
