#!/usr/bin/env python3
"""Bubble Universe for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import os
import sys
import time

from picofb import Display
from picogames.bubble import BubbleUniverse
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


DEFAULT_DEMO_TIME = 900.0


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def require_console_tty(ttyname=None) -> None:
    if ttyname is None:
        ttyname = os.ttyname
    try:
        path = ttyname(0)
    except OSError as exc:
        raise SystemExit("bubble must be started from the PicoCalc console, not SSH or ADB") from exc
    if not is_console_tty(path):
        raise SystemExit(
            f"bubble must be started from the PicoCalc console; current terminal is {path}"
        )


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def key_to_action(key: KeyPress) -> str | None:
    if key.name == Key.LEFT:
        return "left"
    if key.name == Key.RIGHT:
        return "right"
    if key.name == Key.UP:
        return "up"
    if key.name == Key.DOWN:
        return "down"
    if key.name == Key.ENTER:
        return "zoom_in"
    if key.name == Key.DELETE:
        return "zoom_out"
    if key.name == Key.ESCAPE:
        return "reset"
    if key.name == Key.BACKSPACE:
        return "quit"
    if key.name == Key.CHAR:
        if key.value == "-":
            return "speed_down"
        if key.value == "=":
            return "speed_up"
        if key.value == " ":
            return "pause"
        if key.value == "q":
            return "quit"
    return None


def render_frame(target, bubble: BubbleUniverse):
    bubble.render(target)
    return target


def run_once(display: Display, demo_time: float) -> None:
    bubble = BubbleUniverse(display.width, display.height)
    bubble.animation_time = demo_time
    render_frame(display, bubble)
    display.show()


def run_interactive(keyboard_path: str | None = None) -> int:
    require_console_tty()
    with RawTerminal(), Display() as display, open_keyboard(keyboard_path) as keyboard:
        bubble = BubbleUniverse(display.width, display.height)
        last_time = time.monotonic()

        while True:
            now = time.monotonic()
            delta_ms = (now - last_time) * 1000.0
            last_time = now
            bubble.step(delta_ms)
            render_frame(display, bubble)
            display.show()

            key = keyboard.read_key(timeout=0.0)
            if key is None:
                continue
            action = key_to_action(key)
            if action == "quit":
                break
            bubble.apply_action(action)

    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Bubble Universe on the PicoCalc framebuffer")
    parser.add_argument("--once", action="store_true", help="render one framebuffer frame and exit")
    parser.add_argument("--time", type=float, default=DEFAULT_DEMO_TIME, help="animation time for --once")
    parser.add_argument("--keyboard", help="evdev keyboard path, default: auto-detect PicoCalc keyboard")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.once:
        with Display() as display:
            run_once(display, args.time)
        return 0
    return run_interactive(args.keyboard)


if __name__ == "__main__":
    raise SystemExit(main())
