#!/usr/bin/env python3
"""Graphical Sudoku for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from picofb import RED, WHITE, YELLOW, Display, color565
from picogames.sudoku import (
    DEFAULT_SAVE_PATH,
    SudokuGame,
    compute_conflict_cells,
    delete_save,
    load_game,
    save_game,
)
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress


DARK = color565(0, 0, 0)
MENU_BG = DARK
HEADER = color565(17, 17, 17)
GRID = color565(232, 232, 232)
GRID_THICK = WHITE
BOX_HILITE = color565(10, 28, 60)
ROW_HILITE = color565(24, 58, 122)
SELECT = color565(255, 210, 0)
USER = color565(0, 215, 167)
MUTED = color565(176, 176, 176)
PANEL = color565(32, 32, 32)
MENU_TEXT = WHITE
TITLE_BLUE = color565(50, 125, 255)

WIDTH = 320
HEIGHT = 320
HEADER_H = 24
GRID_X = 16
GRID_Y = HEADER_H + 6
CELL = 32
GRID_SIZE = CELL * 9
FONT_TITLE = "Decker"
FONT_BODY = "Decker"
MENU_FIRST_Y = 62
MENU_ITEM_H = 34
MENU_ITEM_GAP = 11


@dataclass(frozen=True)
class MenuItem:
    label: str
    action: str
    value: str | None = None


def format_elapsed(seconds: int) -> str:
    minutes = seconds // 60
    return f"{minutes:02d}:{seconds % 60:02d}"


def text_width(value: object, scale: int = 1) -> int:
    return len(str(value)) * 6 * max(1, int(scale))


def draw_text_right(target, value: object, right: int, y: int, color: int, *, scale: int = 1) -> None:
    target.text(value, right - text_width(value, scale), y, color, scale=scale)


def draw_ttf_or_bitmap(target, value: object, x: int, y: int, color: int, *, size: int, scale: int = 1) -> None:
    try:
        target.text_ttf(value, x, y, color, font=FONT_BODY, size=size)
    except Exception:
        target.text(value, x, y, color, scale=scale)


def draw_thick_rect(target, x: int, y: int, width: int, height: int, color: int, thickness: int = 2) -> None:
    for offset in range(thickness):
        target.rect(x + offset, y + offset, width - offset * 2, height - offset * 2, color)


def draw_digit(target, value: int, row: int, col: int, color: int) -> None:
    size = 25
    x = GRID_X + col * CELL + 9
    y = GRID_Y + row * CELL + 5
    draw_ttf_or_bitmap(target, value, x, y, color, size=size, scale=3)


def draw_grid(target) -> None:
    for index in range(10):
        pos = index * CELL
        thick = index % 3 == 0
        color = GRID_THICK if thick else GRID
        line_width = 2 if thick else 1
        for offset in range(line_width):
            target.vline(GRID_X + pos + offset, GRID_Y, GRID_SIZE + 1, color)
            target.hline(GRID_X, GRID_Y + pos + offset, GRID_SIZE + 1, color)


def draw_highlights(target, game: SudokuGame) -> None:
    row = game.cursor_row
    col = game.cursor_col
    box_row = (row // 3) * 3
    box_col = (col // 3) * 3

    target.fill_rect(GRID_X + box_col * CELL + 1, GRID_Y + box_row * CELL + 1, CELL * 3 - 1, CELL * 3 - 1, BOX_HILITE)
    target.fill_rect(GRID_X + 1, GRID_Y + row * CELL + 1, GRID_SIZE - 1, CELL - 1, ROW_HILITE)
    target.fill_rect(GRID_X + col * CELL + 1, GRID_Y + 1, CELL - 1, GRID_SIZE - 1, ROW_HILITE)


def render_sudoku_frame(target, game: SudokuGame, message: str = ""):
    conflicts = compute_conflict_cells(game.grid)
    target.fill(DARK)
    target.fill_rect(0, 0, WIDTH, HEADER_H, HEADER)
    target.text("Sudoku", 5, 8, YELLOW, scale=1)
    target.text(f"[{game.difficulty.upper()}]", 92, 8, MUTED, scale=1)
    draw_text_right(target, format_elapsed(game.elapsed_seconds()), WIDTH - 7, 9, WHITE, scale=1)

    draw_highlights(target, game)
    draw_grid(target)

    for row in range(9):
        for col in range(9):
            value = game.grid[row][col]
            if not value:
                continue
            if (row, col) in conflicts:
                color = RED
            elif game.given[row][col]:
                color = WHITE
            else:
                color = USER
            draw_digit(target, value, row, col, color)

    selected_x = GRID_X + game.cursor_col * CELL
    selected_y = GRID_Y + game.cursor_row * CELL
    draw_thick_rect(target, selected_x, selected_y, CELL + 1, CELL + 1, SELECT, 3)

    if message:
        target.fill_rect(44, 134, 232, 52, PANEL)
        draw_thick_rect(target, 44, 134, 232, 52, SELECT, 2)
        x = 160 - text_width(message, 2) // 2
        target.text(message, max(50, x), 153, WHITE, scale=2)
    return target


def menu_options(save_exists: bool) -> list[MenuItem]:
    items = []
    if save_exists:
        items.append(MenuItem("CONTINUE", "resume"))
    items.extend(
        [
            MenuItem("EASY", "new", "easy"),
            MenuItem("MEDIUM", "new", "medium"),
            MenuItem("HARD", "new", "hard"),
            MenuItem("EXIT", "exit"),
        ]
    )
    return items


def menu_item_y(index: int) -> int:
    return MENU_FIRST_Y + index * (MENU_ITEM_H + MENU_ITEM_GAP)


def render_menu_frame(target, items: list[MenuItem], selected: int = 0):
    target.fill(MENU_BG)
    target.fill_rect(0, 0, WIDTH, 34, HEADER)
    draw_ttf_or_bitmap(target, "Sudoku", 6, 7, TITLE_BLUE, size=24, scale=2)

    for index, item in enumerate(items):
        y = menu_item_y(index)
        selected_item = index == selected
        fill = ROW_HILITE if selected_item else MENU_BG
        border = SELECT if selected_item else MUTED
        text_color = SELECT if selected_item else MENU_TEXT
        target.fill_rect(28, y, WIDTH - 56, MENU_ITEM_H, fill)
        draw_thick_rect(target, 28, y, WIDTH - 56, MENU_ITEM_H, border, 2 if selected_item else 1)
        draw_ttf_or_bitmap(target, item.label, 48, y + 5, text_color, size=21, scale=2)

    target.text("UP/DOWN SELECT  ENTER START", 10, HEIGHT - 22, MUTED, scale=1)
    target.text("BACKSPACE EXIT", 10, HEIGHT - 10, MUTED, scale=1)
    return target


def demo_game() -> SudokuGame:
    game = SudokuGame("medium")
    puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    game.grid = [row[:] for row in puzzle]
    game.given = [[value != 0 for value in row] for row in puzzle]
    game.cursor_row = 0
    game.cursor_col = 2
    game.set_elapsed(0)
    return game


def apply_key_action(game: SudokuGame, action: str, value: int | str | None) -> bool:
    if action in (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT):
        game.move_cursor(action)
        return True
    if action == Key.DIGIT and isinstance(value, int):
        if value == 0:
            return game.clear_cell(game.cursor_row, game.cursor_col)
        return game.set_cell(game.cursor_row, game.cursor_col, value)
    if action == "clear":
        return game.clear_cell(game.cursor_row, game.cursor_col)
    return False


def key_to_action(key: KeyPress) -> tuple[str, int | str | None]:
    if key.name in (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT):
        return key.name, None
    if key.name == Key.DIGIT:
        return key.name, key.value
    if key.name == Key.DELETE:
        return "clear", None
    if key.name == Key.CHAR and isinstance(key.value, str):
        char = key.value.lower()
        if char == "h":
            return Key.LEFT, None
        if char == "j":
            return Key.DOWN, None
        if char == "k":
            return Key.UP, None
        if char == "l":
            return Key.RIGHT, None
        return char, None
    if key.name == Key.BACKSPACE:
        return "quit", None
    return key.name, key.value


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def require_console_tty(ttyname=None) -> None:
    if ttyname is None:
        ttyname = os.ttyname
    try:
        path = ttyname(0)
    except OSError as exc:
        raise SystemExit("sudoku must be started from the PicoCalc console, not SSH or ADB") from exc
    if not is_console_tty(path):
        raise SystemExit(
            f"sudoku must be started from the PicoCalc console; current terminal is {path}"
        )


def load_or_new(save_path: Path, difficulty: str, force_new: bool) -> SudokuGame:
    if not force_new and save_path.exists():
        return load_game(save_path)
    game = SudokuGame(difficulty)
    game.generate_puzzle()
    return game


def show_frame(display: Display, game: SudokuGame, message: str = "") -> None:
    render_sudoku_frame(display, game, message)
    display.show()


def choose_start_action(display: Display, keyboard, save_path: Path) -> MenuItem:
    items = menu_options(save_path.exists())
    selected = 0
    if not save_path.exists():
        selected = 1
    selected = min(selected, len(items) - 1)
    render_menu_frame(display, items, selected)
    display.show()

    while True:
        key = keyboard.read_key(timeout=0.25)
        if key is None:
            continue
        action, _value = key_to_action(key)
        if action == Key.UP:
            selected = (selected - 1) % len(items)
        elif action == Key.DOWN:
            selected = (selected + 1) % len(items)
        elif action == Key.ENTER:
            return items[selected]
        elif action == "quit" or action == Key.ESCAPE:
            return MenuItem("EXIT", "exit")
        else:
            continue
        render_menu_frame(display, items, selected)
        display.show()


def game_from_menu_choice(choice: MenuItem, save_path: Path) -> SudokuGame | None:
    if choice.action == "exit":
        return None
    if choice.action == "resume":
        return load_game(save_path)
    game = SudokuGame(choice.value or "medium")
    game.generate_puzzle()
    return game


def run_interactive(game: SudokuGame, save_path: Path, keyboard_path: str | None = None) -> int:
    require_console_tty()
    message = ""
    with Display() as display, open_keyboard(keyboard_path) as keyboard:
        last_draw = 0.0
        while True:
            now = time.monotonic()
            if message or now - last_draw >= 1:
                show_frame(display, game, message)
                message = ""
                last_draw = now

            if game.is_complete():
                delete_save(save_path)
                show_frame(display, game, "SOLVED")
                keyboard.read_key()
                break

            key = keyboard.read_key(timeout=0.1)
            if key is None:
                continue
            action, value = key_to_action(key)
            if action == "q" or action == "quit" or action == Key.ESCAPE:
                save_game(game, save_path)
                show_frame(display, game, "SAVED")
                break
            if action == "s":
                save_game(game, save_path)
                message = "SAVED"
                continue
            if apply_key_action(game, action, value):
                show_frame(display, game)
                last_draw = time.monotonic()

    print()
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play graphical Sudoku on the PicoCalc framebuffer")
    parser.add_argument("--once", action="store_true", help="render one framebuffer screen and exit")
    parser.add_argument("--demo", action="store_true", help="use the built-in demo puzzle")
    parser.add_argument("--new", choices=("easy", "medium", "hard"), help="start a new puzzle")
    parser.add_argument("--save-path", type=Path, default=DEFAULT_SAVE_PATH)
    parser.add_argument("--keyboard", help="evdev keyboard path, default: auto-detect PicoCalc keyboard")
    parser.add_argument("--menu-once", action="store_true", help="render the graphical start menu and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.demo:
        game = demo_game()
    elif args.menu_once:
        with Display() as display:
            render_menu_frame(display, menu_options(args.save_path.exists()), selected=0)
            display.show()
        return 0
    elif args.new:
        game = load_or_new(args.save_path, args.new, force_new=True)
    else:
        require_console_tty()
        try:
            with Display() as display, open_keyboard(args.keyboard) as keyboard:
                choice = choose_start_action(display, keyboard, args.save_path)
                game = game_from_menu_choice(choice, args.save_path)
                if game is None:
                    return 0
                return run_game_loop(display, keyboard, game, args.save_path)
        except PermissionError as exc:
            raise SystemExit(
                "permission denied reading PicoCalc keyboard; add user neusse to group input "
                "or run S56console_permissions restart"
            ) from exc

    if args.once:
        with Display() as display:
            show_frame(display, game)
        return 0
    return run_interactive(game, args.save_path, args.keyboard)


def run_game_loop(display: Display, keyboard, game: SudokuGame, save_path: Path) -> int:
    message = ""
    last_draw = 0.0
    while True:
        now = time.monotonic()
        if message or now - last_draw >= 1:
            show_frame(display, game, message)
            message = ""
            last_draw = now

        if game.is_complete():
            delete_save(save_path)
            show_frame(display, game, "SOLVED")
            keyboard.read_key()
            break

        key = keyboard.read_key(timeout=0.1)
        if key is None:
            continue
        action, value = key_to_action(key)
        if action == "q" or action == "quit" or action == Key.ESCAPE:
            save_game(game, save_path)
            show_frame(display, game, "SAVED")
            break
        if action == "s":
            save_game(game, save_path)
            message = "SAVED"
            continue
        if apply_key_action(game, action, value):
            show_frame(display, game)
            last_draw = time.monotonic()

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
