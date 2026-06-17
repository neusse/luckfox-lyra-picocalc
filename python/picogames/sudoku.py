"""Sudoku model and persistence for PicoCalc console apps."""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Iterable


DIFFICULTY_CLUES = {"easy": 40, "medium": 32, "hard": 26}
DEFAULT_SAVE_PATH = Path.home() / ".local" / "share" / "picocalc" / "sudoku_save.json"


def blank_grid() -> list[list[int]]:
    return [[0 for _ in range(9)] for _ in range(9)]


def blank_given() -> list[list[bool]]:
    return [[False for _ in range(9)] for _ in range(9)]


def compute_conflict_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    """Return cells that duplicate a non-zero value in a row, column, or box."""
    conflicts: set[tuple[int, int]] = set()

    def collect(cells: Iterable[tuple[int, int]]) -> None:
        positions: dict[int, list[tuple[int, int]]] = {}
        for row, col in cells:
            value = grid[row][col]
            if value:
                positions.setdefault(value, []).append((row, col))
        for duplicates in positions.values():
            if len(duplicates) > 1:
                conflicts.update(duplicates)

    for row in range(9):
        collect((row, col) for col in range(9))
    for col in range(9):
        collect((row, col) for row in range(9))
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            collect(
                (row, col)
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            )

    return conflicts


class SudokuGame:
    def __init__(self, difficulty: str = "medium", rng: random.Random | None = None):
        self.difficulty = difficulty if difficulty in DIFFICULTY_CLUES else "medium"
        self.grid = blank_grid()
        self.given = blank_given()
        self.cursor_row = 0
        self.cursor_col = 0
        self.start_mono = time.monotonic()
        self.completed = False
        self._rng = rng or random.Random()

    def reset_timer(self) -> None:
        self.start_mono = time.monotonic()

    def set_elapsed(self, elapsed_seconds: int) -> None:
        self.start_mono = time.monotonic() - max(0, int(elapsed_seconds))

    def elapsed_seconds(self) -> int:
        return int(time.monotonic() - self.start_mono)

    def move_cursor(self, direction: str) -> None:
        if direction == "up":
            self.cursor_row = (self.cursor_row - 1) % 9
        elif direction == "down":
            self.cursor_row = (self.cursor_row + 1) % 9
        elif direction == "left":
            self.cursor_col = (self.cursor_col - 1) % 9
        elif direction == "right":
            self.cursor_col = (self.cursor_col + 1) % 9

    def set_cell(self, row: int, col: int, value: int) -> bool:
        if self.given[row][col]:
            return False
        if not 0 <= value <= 9:
            return False
        old = self.grid[row][col]
        self.grid[row][col] = value
        return old != value

    def clear_cell(self, row: int, col: int) -> bool:
        return self.set_cell(row, col, 0)

    def is_complete(self) -> bool:
        return all(all(value for value in row) for row in self.grid) and not compute_conflict_cells(self.grid)

    def to_state(self) -> dict:
        return {
            "version": 1,
            "difficulty": self.difficulty,
            "grid": self.grid,
            "given": self.given,
            "cursor_row": self.cursor_row,
            "cursor_col": self.cursor_col,
            "elapsed": self.elapsed_seconds(),
            "completed": self.completed,
        }

    @classmethod
    def from_state(cls, state: dict) -> "SudokuGame":
        if int(state.get("version", 0)) != 1:
            raise ValueError("unsupported sudoku save version")
        game = cls(str(state.get("difficulty", "medium")))
        game.grid = state.get("grid", blank_grid())
        game.given = state.get("given", blank_given())
        game.cursor_row = max(0, min(8, int(state.get("cursor_row", 0))))
        game.cursor_col = max(0, min(8, int(state.get("cursor_col", 0))))
        game.completed = bool(state.get("completed", False))
        game.set_elapsed(int(state.get("elapsed", 0)))
        return game

    def generate_puzzle(self) -> None:
        self.completed = False
        self.given = blank_given()

        for _ in range(3):
            self.grid = blank_grid()
            self._fill_diagonal_boxes()
            if self._solve_iterative():
                break

        clues = DIFFICULTY_CLUES[self.difficulty]
        cells_to_remove = 81 - clues
        removed = 0
        attempts = 0
        while removed < cells_to_remove and attempts < 300:
            row = self._rng.randint(0, 8)
            col = self._rng.randint(0, 8)
            if self.grid[row][col]:
                self.grid[row][col] = 0
                removed += 1
            attempts += 1

        for row in range(9):
            for col in range(9):
                self.given[row][col] = self.grid[row][col] != 0
        self.reset_timer()

    def _fill_diagonal_boxes(self) -> None:
        for box in range(0, 9, 3):
            nums = list(range(1, 10))
            self._rng.shuffle(nums)
            idx = 0
            for row in range(3):
                for col in range(3):
                    self.grid[box + row][box + col] = nums[idx]
                    idx += 1

    def _is_valid(self, row: int, col: int, value: int) -> bool:
        if value in self.grid[row]:
            return False
        if any(self.grid[r][col] == value for r in range(9)):
            return False
        box_row = 3 * (row // 3)
        box_col = 3 * (col // 3)
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if self.grid[r][c] == value:
                    return False
        return True

    def _solve_iterative(self) -> bool:
        empty = [(r, c) for r in range(9) for c in range(9) if self.grid[r][c] == 0]
        idx = 0
        attempts = [0] * len(empty)

        while 0 <= idx < len(empty):
            row, col = empty[idx]
            self.grid[row][col] = 0
            found = False

            for value in range(attempts[idx] + 1, 10):
                if self._is_valid(row, col, value):
                    self.grid[row][col] = value
                    attempts[idx] = value
                    found = True
                    break

            if found:
                idx += 1
            else:
                attempts[idx] = 0
                idx -= 1

        return idx == len(empty)


def save_game(game: SudokuGame, path: Path | str = DEFAULT_SAVE_PATH) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(game.to_state()), encoding="ascii")
    os.replace(tmp, target)


def load_game(path: Path | str = DEFAULT_SAVE_PATH) -> SudokuGame:
    state = json.loads(Path(path).read_text(encoding="ascii"))
    if not isinstance(state, dict):
        raise ValueError("bad sudoku save")
    return SudokuGame.from_state(state)


def delete_save(path: Path | str = DEFAULT_SAVE_PATH) -> None:
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
