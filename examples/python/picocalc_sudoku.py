#!/usr/bin/env python3
"""Graphical Sudoku for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from picofb import BLACK, CYAN, RED, WHITE, YELLOW, Canvas, Display, color565
from picogames.sudoku import (
    DEFAULT_SAVE_PATH,
    SudokuGame,
    compute_conflict_cells,
    delete_save,
    load_game,
    save_game,
)
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


DARK = color565(1, 5, 10)
HEADER = color565(9, 18, 28)
GRID = color565(190, 205, 215)
GRID_THICK = color565(248, 252, 255)
BOX_HILITE = color565(11, 33, 54)
ROW_HILITE = color565(8, 27, 43)
SELECT = color565(255, 218, 54)
USER = color565(70, 238, 210)
MUTED = color565(150, 166, 178)
PANEL = color565(17, 28, 38)

WIDTH = 320
HEIGHT = 320
HEADER_H = 24
GRID_X = 16
GRID_Y = HEADER_H + 6
CELL = 32
GRID_SIZE = CELL * 9


def format_elapsed(seconds: int) -> str:
    minutes = seconds // 60
    return f"{minutes:02d}:{seconds % 60:02d}"


def text_width(value: object, scale: int = 1) -> int:
    return len(str(value)) * 6 * max(1, int(scale))


def draw_text_right(target, value: object, right: int, y: int, color: int, *, scale: int = 1) -> None:
    target.text(value, right - text_width(value, scale), y, color, scale=scale)


def draw_thick_rect(target, x: int, y: int, width: int, height: int, color: int, thickness: int = 2) -> None:
    for offset in range(thickness):
        target.rect(x + offset, y + offset, width - offset * 2, height - offset * 2, color)


def draw_digit(target, value: int, row: int, col: int, color: int) -> None:
    scale = 3
    digit_w = 5 * scale
    digit_h = 7 * scale
    x = GRID_X + col * CELL + (CELL - digit_w) // 2
    y = GRID_Y + row * CELL + (CELL - digit_h) // 2
    target.text(str(value), x, y, color, scale=scale)


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
    target.text("SUDOKU", 6, 6, YELLOW, scale=2)
    target.text(game.difficulty.upper(), 98, 9, MUTED, scale=1)
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


def load_or_new(save_path: Path, difficulty: str, force_new: bool) -> SudokuGame:
    if not force_new and save_path.exists():
        return load_game(save_path)
    game = SudokuGame(difficulty)
    game.generate_puzzle()
    return game


def show_frame(display: Display, game: SudokuGame, message: str = "") -> None:
    render_sudoku_frame(display, game, message)
    display.show()


def run_interactive(game: SudokuGame, save_path: Path) -> int:
    if not sys.stdin.isatty():
        with Display() as display:
            show_frame(display, game)
        return 0

    message = ""
    with Display() as display, RawTerminal() as terminal:
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
                terminal.read_key()
                break

            key = terminal.read_key(timeout=0.1)
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.demo:
        game = demo_game()
    else:
        game = load_or_new(
            args.save_path,
            args.new or "medium",
            force_new=args.new is not None,
        )

    if args.once:
        with Display() as display:
            show_frame(display, game)
        return 0
    return run_interactive(game, args.save_path)


if __name__ == "__main__":
    raise SystemExit(main())
