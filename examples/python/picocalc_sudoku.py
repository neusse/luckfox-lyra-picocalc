#!/usr/bin/env python3
"""Graphical Sudoku for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from picofb import RED, WHITE, YELLOW, Canvas, Display, color565
from picogames.sudoku import (
    DEFAULT_SAVE_PATH,
    SudokuGame,
    compute_conflict_cells,
    delete_save,
    load_game,
    save_game,
)
from picoterm.appkeys import is_app_exit_key
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


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
SELECT_THICKNESS = 3
DIGIT_X_OFFSET = 2
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


@dataclass
class TextSprite:
    width: int
    height: int
    buffer: bytearray
    transparent: list[bool]


class TextSpriteCache:
    def __init__(self):
        self._sprites: dict[tuple[str, int, int, int], TextSprite] = {}

    def get(self, value: object, color: int, *, size: int, fallback_scale: int = 1) -> TextSprite:
        text = str(value)
        key = (text, color, int(size), int(fallback_scale))
        sprite = self._sprites.get(key)
        if sprite is None:
            sprite = self._render(text, color, int(size), int(fallback_scale))
            self._sprites[key] = sprite
        return sprite

    def _render(self, text: str, color: int, size: int, fallback_scale: int) -> TextSprite:
        width = max(6, int((len(text) * size * 0.72) + 10))
        height = max(8, size + 8)
        canvas = Canvas(width, height, DARK)
        try:
            canvas.text_ttf(text, 0, 0, color, font=FONT_BODY, size=size)
        except Exception:
            canvas.text(text, 0, 0, color, scale=fallback_scale)
        transparent = [
            canvas.pixel(x, y) == DARK
            for y in range(height)
            for x in range(width)
        ]
        lit = [index for index, is_transparent in enumerate(transparent) if not is_transparent]
        if lit:
            xs = [index % width for index in lit]
            ys = [index // width for index in lit]
            left = min(xs)
            right = max(xs) + 1
            top = min(ys)
            bottom = max(ys) + 1
            cropped = Canvas(right - left, bottom - top, DARK)
            cropped.blit(canvas, -left, -top)
            width = cropped.width
            height = cropped.height
            canvas = cropped
            transparent = [
                canvas.pixel(x, y) == DARK
                for y in range(height)
                for x in range(width)
            ]
        return TextSprite(width=width, height=height, buffer=canvas.buffer, transparent=transparent)


TEXT_CACHE = TextSpriteCache()


def format_elapsed(seconds: int) -> str:
    minutes = seconds // 60
    return f"{minutes:02d}:{seconds % 60:02d}"


def text_width(value: object, scale: int = 1) -> int:
    return len(str(value)) * 6 * max(1, int(scale))


def draw_text_right(target, value: object, right: int, y: int, color: int, *, scale: int = 1) -> None:
    target.text(value, right - text_width(value, scale), y, color, scale=scale)


def draw_ttf_or_bitmap(target, value: object, x: int, y: int, color: int, *, size: int, scale: int = 1) -> None:
    target.blit(TEXT_CACHE.get(value, color, size=size, fallback_scale=scale), x, y)


def draw_thick_rect(target, x: int, y: int, width: int, height: int, color: int, thickness: int = 2) -> None:
    for offset in range(thickness):
        target.rect(x + offset, y + offset, width - offset * 2, height - offset * 2, color)


def draw_digit(target, value: int, row: int, col: int, color: int) -> None:
    sprite = TEXT_CACHE.get(value, color, size=25, fallback_scale=3)
    x = GRID_X + col * CELL + (CELL - sprite.width) // 2 + DIGIT_X_OFFSET
    y = GRID_Y + row * CELL + (CELL - sprite.height) // 2
    target.blit(sprite, x, y)


def draw_header(target, game: SudokuGame) -> None:
    target.fill_rect(0, 0, WIDTH, HEADER_H, HEADER)
    target.text("Sudoku", 5, 8, YELLOW, scale=1)
    target.text(f"[{game.difficulty.upper()}]", 92, 8, MUTED, scale=1)
    draw_text_right(target, format_elapsed(game.elapsed_seconds()), WIDTH - 7, 9, WHITE, scale=1)


def cell_background(game: SudokuGame, row: int, col: int) -> int:
    if row == game.cursor_row or col == game.cursor_col:
        return ROW_HILITE
    if row // 3 == game.cursor_row // 3 and col // 3 == game.cursor_col // 3:
        return BOX_HILITE
    return DARK


def draw_grid(target) -> None:
    for index in range(10):
        pos = index * CELL
        thick = index % 3 == 0
        color = GRID_THICK if thick else GRID
        line_width = 2 if thick else 1
        for offset in range(line_width):
            target.vline(GRID_X + pos + offset, GRID_Y, GRID_SIZE + 1, color)
            target.hline(GRID_X, GRID_Y + pos + offset, GRID_SIZE + 1, color)


def draw_cell_grid(target, row: int, col: int) -> None:
    x = GRID_X + col * CELL
    y = GRID_Y + row * CELL
    for index in (col, col + 1):
        line_width = 2 if index % 3 == 0 else 1
        color = GRID_THICK if index % 3 == 0 else GRID
        px = GRID_X + index * CELL
        for offset in range(line_width):
            target.vline(px + offset, y, CELL + 1, color)
    for index in (row, row + 1):
        line_width = 2 if index % 3 == 0 else 1
        color = GRID_THICK if index % 3 == 0 else GRID
        py = GRID_Y + index * CELL
        for offset in range(line_width):
            target.hline(x, py + offset, CELL + 1, color)


def draw_cell(target, game: SudokuGame, row: int, col: int, conflicts: set[tuple[int, int]] | None = None) -> None:
    x = GRID_X + col * CELL
    y = GRID_Y + row * CELL
    target.fill_rect(x + 1, y + 1, CELL - 1, CELL - 1, cell_background(game, row, col))
    draw_cell_grid(target, row, col)

    value = game.grid[row][col]
    if value:
        if conflicts is None:
            conflicts = compute_conflict_cells(game.grid)
        if (row, col) in conflicts:
            color = RED
        elif game.given[row][col]:
            color = WHITE
        else:
            color = USER
        draw_digit(target, value, row, col, color)

    if row == game.cursor_row and col == game.cursor_col:
        draw_thick_rect(target, x, y, CELL + 1, CELL + 1, SELECT, SELECT_THICKNESS)


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
    draw_header(target, game)

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
    draw_thick_rect(target, selected_x, selected_y, CELL + 1, CELL + 1, SELECT, SELECT_THICKNESS)

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
    if is_app_exit_key(key):
        return "quit", None
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


class SudokuRenderer:
    def __init__(self, display: Display, game: SudokuGame):
        self.display = display
        self.game = game
        self.last_cursor: tuple[int, int] | None = None

    def show_full(self, message: str = "") -> None:
        show_frame(self.display, self.game, message)
        self.last_cursor = (self.game.cursor_row, self.game.cursor_col)

    def show_header(self) -> None:
        draw_header(self.display, self.game)
        self.display.show_region(0, 0, WIDTH, HEADER_H)

    def show_cursor_move(self, old_cursor: tuple[int, int] | None) -> None:
        if old_cursor is None:
            self.show_full()
            return

        cells = dirty_cells_for_cursor_move(old_cursor, (self.game.cursor_row, self.game.cursor_col))
        conflicts = compute_conflict_cells(self.game.grid)
        for row, col in cells:
            draw_cell(self.display, self.game, row, col, conflicts)
        self.display.show_regions(dirty_regions_for_cells(cells))
        self.last_cursor = (self.game.cursor_row, self.game.cursor_col)


def dirty_cells_for_cursor_move(
    old_cursor: tuple[int, int],
    new_cursor: tuple[int, int],
) -> set[tuple[int, int]]:
    old_row, old_col = old_cursor
    new_row, new_col = new_cursor
    cells: set[tuple[int, int]] = set()

    for col in range(9):
        cells.add((old_row, col))
        cells.add((new_row, col))
    for row in range(9):
        cells.add((row, old_col))
        cells.add((row, new_col))

    for base_row, base_col in (
        ((old_row // 3) * 3, (old_col // 3) * 3),
        ((new_row // 3) * 3, (new_col // 3) * 3),
    ):
        for row in range(base_row, base_row + 3):
            for col in range(base_col, base_col + 3):
                cells.add((row, col))

    return cells


def dirty_regions_for_cells(cells: set[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    regions: list[tuple[int, int, int, int]] = []
    by_row: dict[int, list[int]] = {}
    for row, col in cells:
        by_row.setdefault(row, []).append(col)

    for row in sorted(by_row):
        cols = sorted(set(by_row[row]))
        run_start = cols[0]
        previous = cols[0]
        for col in cols[1:]:
            if col == previous + 1:
                previous = col
                continue
            regions.append(cell_run_region(row, run_start, previous))
            run_start = previous = col
        regions.append(cell_run_region(row, run_start, previous))

    return regions


def cell_run_region(row: int, start_col: int, end_col: int) -> tuple[int, int, int, int]:
    return (
        GRID_X + start_col * CELL,
        GRID_Y + row * CELL,
        ((end_col - start_col + 1) * CELL) + SELECT_THICKNESS,
        CELL + SELECT_THICKNESS,
    )


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
    with RawTerminal(), Display() as display, open_keyboard(keyboard_path) as keyboard:
        renderer = SudokuRenderer(display, game)
        renderer.show_full()
        last_draw = time.monotonic()
        while True:
            now = time.monotonic()
            if message or now - last_draw >= 1:
                if message:
                    renderer.show_full(message)
                else:
                    renderer.show_header()
                message = ""
                last_draw = now

            if game.is_complete():
                delete_save(save_path)
                renderer.show_full("SOLVED")
                keyboard.read_key()
                break

            key = keyboard.read_key(timeout=0.1)
            if key is None:
                continue
            action, value = key_to_action(key)
            if action == "q" or action == "quit" or action == Key.ESCAPE:
                save_game(game, save_path)
                renderer.show_full("SAVED")
                break
            if action == "s":
                save_game(game, save_path)
                message = "SAVED"
                continue
            old_cursor = (game.cursor_row, game.cursor_col)
            if apply_key_action(game, action, value):
                if action in (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT):
                    renderer.show_cursor_move(old_cursor)
                else:
                    renderer.show_full()
                last_draw = time.monotonic()
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
            with RawTerminal(), Display() as display, open_keyboard(args.keyboard) as keyboard:
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
    renderer = SudokuRenderer(display, game)
    renderer.show_full()
    last_draw = time.monotonic()
    while True:
        now = time.monotonic()
        if message or now - last_draw >= 1:
            if message:
                renderer.show_full(message)
            else:
                renderer.show_header()
            message = ""
            last_draw = now

        if game.is_complete():
            delete_save(save_path)
            renderer.show_full("SOLVED")
            keyboard.read_key()
            break

        key = keyboard.read_key(timeout=0.1)
        if key is None:
            continue
        action, value = key_to_action(key)
        if action == "q" or action == "quit" or action == Key.ESCAPE:
            save_game(game, save_path)
            renderer.show_full("SAVED")
            break
        if action == "s":
            save_game(game, save_path)
            message = "SAVED"
            continue
        old_cursor = (game.cursor_row, game.cursor_col)
        if apply_key_action(game, action, value):
            if action in (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT):
                renderer.show_cursor_move(old_cursor)
            else:
                renderer.show_full()
            last_draw = time.monotonic()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
