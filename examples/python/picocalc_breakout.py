#!/usr/bin/env python3
"""Breakout for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import os
import random
import sys
import time

from picofb import Display, color565
from picogames.breakout import BreakoutGame
from picoterm.appkeys import is_app_exit_key
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


def hex565(value: int) -> int:
    return color565((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)


C_BG = hex565(0x05090E)
C_PANEL = hex565(0x121A24)
C_PANEL_OUT = hex565(0x33485D)
C_TEXT = hex565(0xF8FAFC)
C_DIM = hex565(0x7F92A6)
C_PADDLE = hex565(0x00FFFF)
C_BALL = hex565(0xFFFFFF)
C_MESSAGE = hex565(0xFFFF00)


def draw_text(canvas, value: str, x: int, y: int, color: int, *, scale: int = 1, background=None) -> None:
    canvas.text(value, x, y, color, background=background, scale=scale)


def draw_center_text(canvas, value: str, y: int, color: int, *, scale: int = 1) -> None:
    width = len(value) * 6 * scale
    draw_text(canvas, value, max(0, (canvas.width - width) // 2), y, color, scale=scale)


def fill_circle(canvas, cx: int, cy: int, radius: int, color: int) -> None:
    for dy in range(-radius, radius + 1):
        span = int((radius * radius - dy * dy) ** 0.5)
        canvas.hline(cx - span, cy + dy, span * 2 + 1, color)


def render_game(canvas, game: BreakoutGame) -> None:
    canvas.fill(C_BG)
    canvas.fill_rect(0, 0, canvas.width, 22, C_PANEL)
    canvas.rect(0, 0, canvas.width, 22, C_PANEL_OUT)
    draw_text(canvas, f"Score:{game.score}", 6, 7, C_TEXT)
    lives = f"Lives:{game.lives}"
    draw_text(canvas, lives, canvas.width - len(lives) * 6 - 6, 7, C_TEXT)

    for brick in game.bricks:
        if brick.alive:
            canvas.fill_rect(brick.x, brick.y, brick.width, brick.height, brick.color)
            canvas.rect(brick.x, brick.y, brick.width, brick.height, C_BG)

    canvas.fill_rect(int(game.paddle_x), game.paddle_y, game.paddle_width, game.paddle_height, C_PADDLE)
    fill_circle(canvas, int(game.ball_x), int(game.ball_y), game.ball_radius, C_BALL)

    if game.message:
        draw_center_text(canvas, game.message[:40], 158, C_MESSAGE)

    canvas.fill_rect(0, canvas.height - game.status_height, canvas.width, game.status_height, C_PANEL)
    canvas.rect(0, canvas.height - game.status_height, canvas.width, game.status_height, C_PANEL_OUT)
    footer = "Left/Right move  Space launch  Back exit"
    draw_text(canvas, footer[:51], 6, canvas.height - 13, C_DIM)


def key_to_action(key: KeyPress | None) -> str | None:
    if key is None:
        return None
    if is_app_exit_key(key):
        return "quit"
    if key.name == Key.LEFT:
        return "left"
    if key.name == Key.RIGHT:
        return "right"
    if key.name == Key.ENTER:
        return "launch"
    if key.name in (Key.BACKSPACE, Key.ESCAPE):
        return "quit"
    if key.name == Key.CHAR:
        value = str(key.value).lower()
        if value == "q":
            return "quit"
        if value == " ":
            return "launch"
        if value == "a":
            return "left"
        if value == "d":
            return "right"
    return None


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def require_console_tty(ttyname=None) -> None:
    ttyname = getattr(os, "ttyname", None) if ttyname is None else ttyname
    if ttyname is None:
        raise SystemExit("breakout must be started from the PicoCalc console, not SSH or ADB")
    try:
        path = ttyname(0)
    except OSError as exc:
        raise SystemExit("breakout must be started from the PicoCalc console, not SSH or ADB") from exc
    if not is_console_tty(path):
        raise SystemExit(f"breakout must be started from the PicoCalc console; current terminal is {path}")


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def run_once(framebuffer: str = "/dev/fb0") -> int:
    with Display(framebuffer) as display:
        render_game(display, BreakoutGame(rng=random.Random(1)))
        display.show()
    return 0


def run_interactive(framebuffer: str = "/dev/fb0", keyboard_path: str | None = None) -> int:
    require_console_tty()
    game = BreakoutGame(rng=random.Random())
    held_left = False
    held_right = False
    last_frame = time.monotonic()

    with RawTerminal(), Display(framebuffer) as display, open_keyboard(keyboard_path) as keyboard:
        while True:
            action = key_to_action(keyboard.read_key(timeout=0.0))
            if action == "quit":
                return 0
            if action == "launch":
                game.launch()
            elif action == "left":
                held_left = True
                held_right = False
            elif action == "right":
                held_right = True
                held_left = False
            elif action is None:
                held_left = False
                held_right = False

            if held_left:
                game.move_paddle("left")
            if held_right:
                game.move_paddle("right")

            now = time.monotonic()
            game.step(now - last_frame)
            last_frame = now
            render_game(display, game)
            display.show()
            time.sleep(0.016)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Breakout on the PicoCalc framebuffer")
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
