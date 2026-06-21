#!/usr/bin/env python3
"""Minesweeper for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import os
import random
import sys
import time

from picofb import Display, color565
from picogames.minesweeper import MinesweeperGame
from picoterm.appkeys import is_app_exit_key
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


def hex565(value: int) -> int:
    return color565((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)


CELL_SIZE = 16
GRID_W = 16
GRID_H = 16
MINES_EASY = 24
MINES_MED = 40
MINES_HARD = 64

HEADER_H = 22
FOOTER_H = 20
GRID_PX_W = GRID_W * CELL_SIZE
GRID_PX_H = GRID_H * CELL_SIZE
GRID_X = (320 - GRID_PX_W) // 2
GRID_Y = HEADER_H + 4

MENU_START_Y = HEADER_H + 28
MENU_LINE_H = 24

C_BG = hex565(0x000000)
C_PANEL = hex565(0x1C1C1C)
C_PANEL_OUT = hex565(0x303030)
C_TEXT = hex565(0xFFFFFF)
C_DIM = hex565(0x7A7A7A)
C_CURSOR = hex565(0x00FF00)
C_MINE = hex565(0xFF0000)
C_FLAG = hex565(0x00FFAA)
C_MENU_HILITE_BG = hex565(0x0000AA)
C_MENU_HILITE_OUT = hex565(0x00FF00)
C_MENU_TEXT_SELECTED = hex565(0xFFFF00)
C_REVEALED = C_BG

NUM_COLORS = [
    C_TEXT,
    hex565(0x00AAFF),
    hex565(0x00CC00),
    hex565(0xFF5555),
    hex565(0x6666FF),
    hex565(0xFFAA00),
    hex565(0x00FFFF),
    hex565(0xFFFFFF),
    hex565(0xAAAAAA),
]

MENU_ITEMS = [
    ("Easy", MINES_EASY),
    ("Medium", MINES_MED),
    ("Hard", MINES_HARD),
    ("Exit", 0),
]


def draw_text(canvas, value: str, x: int, y: int, color: int, *, scale: int = 1, background=None) -> None:
    canvas.text(value, x, y, color, background=background, scale=scale)


def draw_center_text(canvas, value: str, cx: int, y: int, color: int, *, scale: int = 1) -> None:
    width = len(value) * 6 * scale
    draw_text(canvas, value, cx - width // 2, y, color, scale=scale)


def render_menu(canvas, selected: int = 1) -> None:
    canvas.fill(C_BG)
    canvas.fill_rect(0, 0, canvas.width, HEADER_H, C_PANEL)
    canvas.rect(0, 0, canvas.width, HEADER_H, C_PANEL_OUT)
    draw_text(canvas, "Minesweeper", 8, 5, C_MENU_TEXT_SELECTED, scale=2)

    labels = [f"{name} {mines}" if mines else name for name, mines in MENU_ITEMS]
    max_w = max(len(text) * 12 for text in labels)
    selected = max(0, min(selected, len(MENU_ITEMS) - 1))
    hilite_y = MENU_START_Y + selected * MENU_LINE_H - 12
    canvas.fill_rect(34, hilite_y, max_w + 20, 22, C_MENU_HILITE_BG)
    canvas.rect(34, hilite_y, max_w + 20, 22, C_MENU_HILITE_OUT)

    for index, text in enumerate(labels):
        color = C_MENU_TEXT_SELECTED if index == selected else C_TEXT
        draw_text(canvas, text, 40, MENU_START_Y + index * MENU_LINE_H - 8, color, scale=2)

    footer_h = 36
    canvas.fill_rect(0, canvas.height - footer_h, canvas.width, footer_h, C_PANEL)
    canvas.rect(0, canvas.height - footer_h, canvas.width, footer_h, C_PANEL_OUT)
    draw_text(canvas, "Up/Down select  Enter start  Back exit", 8, canvas.height - 13, C_DIM)


def render_cell(canvas, game: MinesweeperGame, x: int, y: int) -> None:
    rx = GRID_X + x * CELL_SIZE
    ry = GRID_Y + y * CELL_SIZE
    if game.revealed[y][x]:
        canvas.fill_rect(rx, ry, CELL_SIZE, CELL_SIZE, C_REVEALED)
        canvas.rect(rx, ry, CELL_SIZE, CELL_SIZE, C_PANEL_OUT)
        value = game.grid[y][x]
        if value == -1:
            draw_center_text(canvas, "*", rx + CELL_SIZE // 2, ry + 4, C_MINE)
        elif value > 0:
            color = NUM_COLORS[value] if value < len(NUM_COLORS) else C_TEXT
            draw_center_text(canvas, str(value), rx + CELL_SIZE // 2, ry + 4, color)
    else:
        canvas.fill_rect(rx, ry, CELL_SIZE, CELL_SIZE, C_PANEL)
        canvas.rect(rx, ry, CELL_SIZE, CELL_SIZE, C_PANEL_OUT)
        if game.flagged[y][x]:
            draw_center_text(canvas, "F", rx + CELL_SIZE // 2, ry + 4, C_FLAG)


def render_game(canvas, game: MinesweeperGame, message: str | None = None) -> None:
    canvas.fill(C_BG)
    canvas.fill_rect(0, 0, canvas.width, HEADER_H, C_PANEL)
    canvas.rect(0, 0, canvas.width, HEADER_H, C_PANEL_OUT)
    draw_text(canvas, "Minesweeper", 8, 7, C_MENU_TEXT_SELECTED)
    status = f"Mines:{game.mines_left()} Time:{game.elapsed_seconds()}"
    draw_text(canvas, status, canvas.width - len(status) * 6 - 8, 7, C_DIM)

    for y in range(game.height):
        for x in range(game.width):
            render_cell(canvas, game, x, y)

    cursor_x = GRID_X + game.cursor_x * CELL_SIZE
    cursor_y = GRID_Y + game.cursor_y * CELL_SIZE
    canvas.rect(cursor_x, cursor_y, CELL_SIZE, CELL_SIZE, C_CURSOR)

    canvas.fill_rect(0, canvas.height - FOOTER_H, canvas.width, FOOTER_H, C_PANEL)
    canvas.rect(0, canvas.height - FOOTER_H, canvas.width, FOOTER_H, C_PANEL_OUT)
    footer = message or "Arrows move  Enter reveal  F flag  Back menu"
    draw_text(canvas, footer[:50], 8, canvas.height - 13, C_DIM if message is None else C_MENU_TEXT_SELECTED)


def key_to_action(key: KeyPress | None) -> str | None:
    if key is None:
        return None
    if is_app_exit_key(key):
        return "quit"
    if key.name == Key.UP:
        return "up"
    if key.name == Key.DOWN:
        return "down"
    if key.name == Key.LEFT:
        return "left"
    if key.name == Key.RIGHT:
        return "right"
    if key.name == Key.ENTER:
        return "reveal"
    if key.name in (Key.BACKSPACE, Key.ESCAPE):
        return "back"
    if key.name == Key.CHAR:
        value = str(key.value).lower()
        if value == "q":
            return "quit"
        if value in (" ", "r"):
            return "reveal"
        if value == "f":
            return "flag"
    return None


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def require_console_tty(ttyname=None) -> None:
    ttyname = getattr(os, "ttyname", None) if ttyname is None else ttyname
    if ttyname is None:
        raise SystemExit("minesweeper must be started from the PicoCalc console, not SSH or ADB")
    try:
        path = ttyname(0)
    except OSError as exc:
        raise SystemExit("minesweeper must be started from the PicoCalc console, not SSH or ADB") from exc
    if not is_console_tty(path):
        raise SystemExit(f"minesweeper must be started from the PicoCalc console; current terminal is {path}")


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def run_once(framebuffer: str = "/dev/fb0") -> int:
    with Display(framebuffer) as display:
        render_menu(display, selected=1)
        display.show()
    return 0


def run_interactive(framebuffer: str = "/dev/fb0", keyboard_path: str | None = None) -> int:
    require_console_tty()
    state = "menu"
    selected = 1
    game = MinesweeperGame(width=GRID_W, height=GRID_H, mines=MINES_MED, rng=random.Random())
    message: str | None = None

    with RawTerminal(), Display(framebuffer) as display, open_keyboard(keyboard_path) as keyboard:
        render_menu(display, selected)
        display.show()
        last_status = time.monotonic()
        while True:
            action = key_to_action(keyboard.read_key(timeout=0.05))
            if action == "quit":
                return 0

            if state == "menu":
                if action == "up":
                    selected = max(0, selected - 1)
                elif action == "down":
                    selected = min(len(MENU_ITEMS) - 1, selected + 1)
                elif action == "back":
                    return 0
                elif action == "reveal":
                    label, mines = MENU_ITEMS[selected]
                    if label == "Exit":
                        return 0
                    game = MinesweeperGame(width=GRID_W, height=GRID_H, mines=mines, rng=random.Random())
                    state = "game"
                    message = None
                    render_game(display, game)
                    display.show()
                    continue
                if action:
                    render_menu(display, selected)
                    display.show()
                continue

            if action == "back":
                state = "menu"
                render_menu(display, selected)
                display.show()
                continue
            if action in {"up", "down", "left", "right"}:
                game.move_cursor(action)
                message = None
            elif action == "flag":
                game.toggle_flag(game.cursor_x, game.cursor_y)
                message = None
            elif action == "reveal":
                result = game.reveal(game.cursor_x, game.cursor_y)
                if result == "lost":
                    message = "BOOM! Back menu  Enter new game"
                elif result == "won":
                    message = "You win! Back menu  Enter new game"
                elif game.won or game.lost:
                    game.reset()
                    message = None
                else:
                    message = None

            now = time.monotonic()
            if action or (state == "game" and now - last_status >= 1.0):
                last_status = now
                render_game(display, game, message)
                display.show()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Minesweeper on the PicoCalc framebuffer")
    parser.add_argument("--fb", default="/dev/fb0")
    parser.add_argument("--keyboard", help="evdev keyboard path, default: auto-detect PicoCalc keyboard")
    parser.add_argument("--once", action="store_true", help="render one menu frame and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.once:
        return run_once(args.fb)
    return run_interactive(args.fb, args.keyboard)


if __name__ == "__main__":
    raise SystemExit(main())
