#!/usr/bin/env python3
"""iOS-style calculator for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import math
import os
import sys
import time

from picofb import Display, color565
from picofb.ttf import measure_ttf_text
from picogames.calculator import CalculatorState
from picoterm.appkeys import is_app_exit_key
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


def hex565(value: int) -> int:
    return color565((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)


BG = hex565(0x1C1C1E)
BTN_DARK = hex565(0x2C2C2E)
BTN_LIGHT = hex565(0x5C5C5F)
BTN_ORANGE = hex565(0xFF9F0A)
TEXT_LIGHT = hex565(0xF2F2F7)
TEXT_DARK = hex565(0x0B0B0B)
TEXT_DIM = hex565(0x8E8E93)
FONT_UI = "DejaVu Sans Mono"

WIDTH = 320
HEIGHT = 320
TOP_H = int(HEIGHT * 0.28)
GRID_MARGIN = 8
GRID_GAP = 6
BUTTON_SIZE = 40
GRID_W = (BUTTON_SIZE * 4) + (GRID_GAP * 3)
GRID_H = (BUTTON_SIZE * 5) + (GRID_GAP * 4)
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = TOP_H

BUTTON_LAYOUT = [
    [("AC", BTN_LIGHT, TEXT_DARK), ("+/-", BTN_LIGHT, TEXT_DARK), ("%", BTN_LIGHT, TEXT_DARK), ("/", BTN_ORANGE, TEXT_LIGHT)],
    [("7", BTN_DARK, TEXT_LIGHT), ("8", BTN_DARK, TEXT_LIGHT), ("9", BTN_DARK, TEXT_LIGHT), ("x", BTN_ORANGE, TEXT_LIGHT)],
    [("4", BTN_DARK, TEXT_LIGHT), ("5", BTN_DARK, TEXT_LIGHT), ("6", BTN_DARK, TEXT_LIGHT), ("-", BTN_ORANGE, TEXT_LIGHT)],
    [("1", BTN_DARK, TEXT_LIGHT), ("2", BTN_DARK, TEXT_LIGHT), ("3", BTN_DARK, TEXT_LIGHT), ("+", BTN_ORANGE, TEXT_LIGHT)],
    [("0", BTN_DARK, TEXT_LIGHT), None, (".", BTN_DARK, TEXT_LIGHT), ("=", BTN_ORANGE, TEXT_LIGHT)],
]


def fill_circle(canvas, cx: int, cy: int, radius: int, color: int) -> None:
    for dy in range(-radius, radius + 1):
        width = int(math.sqrt(max(0, radius * radius - dy * dy)))
        canvas.hline(cx - width, cy + dy, width * 2 + 1, color)


def fill_pill(canvas, x: int, y: int, width: int, height: int, color: int) -> None:
    radius = height // 2
    canvas.fill_rect(x + radius, y, max(0, width - height), height, color)
    fill_circle(canvas, x + radius, y + radius, radius, color)
    fill_circle(canvas, x + width - radius, y + radius, radius, color)


def draw_ttf_text(canvas, value: str, x: int, y: int, color: int, *, size: int) -> None:
    canvas.text_ttf(value, x, y, color, font=FONT_UI, size=size)


def draw_center_text(canvas, value: str, cx: int, cy: int, color: int, *, size: int = 22) -> None:
    bounds = measure_ttf_text(value, font=FONT_UI, size=size)
    draw_ttf_text(canvas, value, cx - bounds.width // 2, cy - bounds.height // 2, color, size=size)


def draw_right_text(canvas, value: str, right: int, y: int, color: int, *, size: int = 16) -> None:
    bounds = measure_ttf_text(value, font=FONT_UI, size=size)
    draw_ttf_text(canvas, value, right - bounds.width, y, color, size=size)


def display_size(text: str) -> int:
    if len(text) > 14:
        return 24
    if len(text) > 10:
        return 32
    return 42


def display_region() -> tuple[int, int, int, int]:
    return (0, 0, WIDTH, TOP_H)


def button_label_size(text: str) -> int:
    if len(text) >= 3:
        return 17
    if len(text) == 2:
        return 18
    return 24


def render_button(canvas, text: str, x: int, y: int, width: int, height: int, fill: int, text_color: int) -> None:
    if width > height:
        fill_pill(canvas, x, y, width, height, fill)
    else:
        fill_circle(canvas, x + width // 2, y + height // 2, width // 2, fill)
    cx = x + width // 2
    cy = y + height // 2
    draw_center_text(canvas, text, cx, cy, text_color, size=button_label_size(text))


def render_static_buttons(canvas, state: CalculatorState | None = None) -> None:
    state = CalculatorState() if state is None else state
    canvas.fill(BG)

    for row, entries in enumerate(BUTTON_LAYOUT):
        for col, entry in enumerate(entries):
            if row == 4 and col == 1:
                continue
            if entry is None:
                continue
            label, fill, text_color = entry
            if label == "AC":
                label = state.clear_label
            x = GRID_X + col * (BUTTON_SIZE + GRID_GAP)
            y = GRID_Y + row * (BUTTON_SIZE + GRID_GAP)
            width = BUTTON_SIZE
            if row == 4 and col == 0:
                width = BUTTON_SIZE * 2 + GRID_GAP
            render_button(canvas, label, x, y, width, BUTTON_SIZE, fill, text_color)


def render_display(canvas, state: CalculatorState) -> None:
    canvas.fill_rect(0, 0, canvas.width, TOP_H, BG)
    if state.expression:
        draw_right_text(canvas, state.expression[-32:], canvas.width - 12, 12, TEXT_DIM, size=14)
    value = state.display
    size = display_size(value)
    draw_right_text(canvas, value, canvas.width - 12, TOP_H - size - 2, TEXT_LIGHT, size=size)


def render_calculator(canvas, state: CalculatorState) -> None:
    render_static_buttons(canvas, state)
    render_display(canvas, state)


def key_to_action(key: KeyPress | None) -> str | None:
    if key is None:
        return None
    if is_app_exit_key(key):
        return "quit"
    if key.name == Key.DIGIT:
        return str(key.value)
    if key.name == Key.ENTER:
        return "="
    if key.name in (Key.BACKSPACE, Key.DELETE):
        return "backspace"
    if key.name == Key.ESCAPE:
        return "quit"
    if key.name == Key.CHAR and isinstance(key.value, str):
        value = key.value
        if value.lower() == "q":
            return "quit"
        if value in "0123456789.+-*/=%":
            return value
        if value.lower() in ("x", "c", "p", "s"):
            return value.lower()
    return None


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def require_console_tty(ttyname=None) -> None:
    ttyname = getattr(os, "ttyname", None) if ttyname is None else ttyname
    if ttyname is None:
        raise SystemExit("calculator must be started from the PicoCalc console, not SSH or ADB")
    try:
        path = ttyname(0)
    except OSError as exc:
        raise SystemExit("calculator must be started from the PicoCalc console, not SSH or ADB") from exc
    if not is_console_tty(path):
        raise SystemExit(f"calculator must be started from the PicoCalc console; current terminal is {path}")


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def run_once(framebuffer: str = "/dev/fb0") -> int:
    with Display(framebuffer) as display:
        render_calculator(display, CalculatorState())
        display.show()
    return 0


def run_interactive(framebuffer: str = "/dev/fb0", keyboard_path: str | None = None) -> int:
    require_console_tty()
    state = CalculatorState()
    with RawTerminal(), Display(framebuffer) as display, open_keyboard(keyboard_path) as keyboard:
        render_static_buttons(display, state)
        render_display(display, state)
        display.show()
        while True:
            action = key_to_action(keyboard.read_key(timeout=0.02))
            if action is None:
                continue
            if action == "quit":
                return 0
            state.press(action)
            render_display(display, state)
            display.show_region(*display_region())


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PicoCalc calculator")
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
