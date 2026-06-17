#!/usr/bin/env python3
"""Sudoku for the Luckfox Lyra PicoCalc Linux console."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from picogames.sudoku import (
    DEFAULT_SAVE_PATH,
    SudokuGame,
    compute_conflict_cells,
    delete_save,
    load_game,
    save_game,
)
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal, clear_screen, hide_cursor, show_cursor, strip_ansi


RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RED = "\x1b[31;1m"
CYAN = "\x1b[36;1m"
YELLOW = "\x1b[33;1m"
REVERSE = "\x1b[7m"


def format_elapsed(seconds: int) -> str:
    minutes = seconds // 60
    return f"{minutes:02d}:{seconds % 60:02d}"


def clamp_line(line: str, width: int) -> str:
    visible = strip_ansi(line)
    if len(visible) <= width:
        return line
    return visible[:width]


def styled_cell(game: SudokuGame, row: int, col: int, conflicts: set[tuple[int, int]]) -> str:
    value = game.grid[row][col]
    text = "." if value == 0 else str(value)
    if (row, col) == (game.cursor_row, game.cursor_col):
        return f"{REVERSE}{text}{RESET}"
    if (row, col) in conflicts:
        return f"{RED}{text}{RESET}"
    if game.given[row][col]:
        return f"{BOLD}{text}{RESET}"
    if value:
        return f"{CYAN}{text}{RESET}"
    return text


def render_board(game: SudokuGame) -> list[str]:
    conflicts = compute_conflict_cells(game.grid)
    border = "+-------+-------+-------+"
    lines = [border]
    for row in range(9):
        parts = ["|"]
        for col in range(9):
            parts.append(" " + styled_cell(game, row, col, conflicts))
            if col in (2, 5, 8):
                parts.append(" |")
        lines.append("".join(parts))
        if row in (2, 5, 8):
            lines.append(border)
    return lines


def render_game_screen(game: SudokuGame, width: int = 45, show_help: bool = True, message: str = "") -> str:
    conflicts = compute_conflict_cells(game.grid)
    header = f"{YELLOW}PicoCalc Sudoku{RESET} {game.difficulty} {format_elapsed(game.elapsed_seconds())}"
    lines = [header, ""]
    lines.extend(render_board(game))
    lines.append("")
    lines.append(f"Cell r{game.cursor_row + 1} c{game.cursor_col + 1}  conflicts {len(conflicts)}")
    if message:
        lines.append(f"{YELLOW}{message}{RESET}")
    if show_help:
        lines.extend(
            [
                "Arrows move   1-9 set",
                "0/Del clear   s save   q quit",
            ]
        )
    return "\n".join(clamp_line(line, width) for line in lines)


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


def write_frame(screen: RawTerminal, game: SudokuGame, message: str = "") -> None:
    screen.stdout.write(clear_screen())
    screen.stdout.write(render_game_screen(game, width=45, message=message))
    screen.stdout.flush()


def load_or_new(save_path: Path, difficulty: str, force_new: bool) -> SudokuGame:
    if not force_new and save_path.exists():
        return load_game(save_path)
    game = SudokuGame(difficulty)
    game.generate_puzzle()
    return game


def run_interactive(game: SudokuGame, save_path: Path) -> int:
    if not sys.stdin.isatty():
        print(render_game_screen(game, width=45))
        return 0

    message = ""
    with RawTerminal() as screen:
        while True:
            write_frame(screen, game, message)
            message = ""

            if game.is_complete():
                delete_save(save_path)
                write_frame(screen, game, "Solved. Press any key.")
                screen.read_key()
                break

            action, value = key_to_action(screen.read_key())
            if action == "q" or action == "quit" or action == Key.ESCAPE:
                save_game(game, save_path)
                message = "Saved."
                write_frame(screen, game, message)
                break
            if action == "s":
                save_game(game, save_path)
                message = "Saved."
                continue
            apply_key_action(game, action, value)

    print()
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Sudoku on the PicoCalc console")
    parser.add_argument("--once", action="store_true", help="render one screen and exit")
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
        print(render_game_screen(game, width=45))
        return 0
    return run_interactive(game, args.save_path)


if __name__ == "__main__":
    raise SystemExit(main())
