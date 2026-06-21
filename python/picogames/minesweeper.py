"""Minesweeper model for PicoCalc framebuffer apps."""

from __future__ import annotations

import random
import time


class MinesweeperGame:
    """Small Minesweeper board with first-click-safe mine placement."""

    def __init__(
        self,
        *,
        width: int = 16,
        height: int = 16,
        mines: int = 40,
        rng: random.Random | None = None,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if mines <= 0 or mines >= width * height:
            raise ValueError("mines must fit inside the board")
        self.width = int(width)
        self.height = int(height)
        self.mines = int(mines)
        self.rng = rng or random.Random()
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.revealed = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.flagged = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.cursor_x = 0
        self.cursor_y = 0
        self.mines_placed = False
        self.start_mono: float | None = None
        self.won = False
        self.lost = False

    def reset(self, mines: int | None = None) -> None:
        if mines is not None:
            if mines <= 0 or mines >= self.width * self.height:
                raise ValueError("mines must fit inside the board")
            self.mines = int(mines)
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.revealed = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.flagged = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.cursor_x = 0
        self.cursor_y = 0
        self.mines_placed = False
        self.start_mono = None
        self.won = False
        self.lost = False

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbors(self, x: int, y: int):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = x + dx
                ny = y + dy
                if self.in_bounds(nx, ny):
                    yield nx, ny

    def move_cursor(self, direction: str) -> None:
        if direction == "left":
            self.cursor_x = max(0, self.cursor_x - 1)
        elif direction == "right":
            self.cursor_x = min(self.width - 1, self.cursor_x + 1)
        elif direction == "up":
            self.cursor_y = max(0, self.cursor_y - 1)
        elif direction == "down":
            self.cursor_y = min(self.height - 1, self.cursor_y + 1)

    def place_mines(self, safe_x: int, safe_y: int) -> None:
        positions = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) != (safe_x, safe_y)
        ]
        self.rng.shuffle(positions)
        for x, y in positions[: self.mines]:
            self.grid[y][x] = -1
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == -1:
                    continue
                self.grid[y][x] = sum(1 for nx, ny in self.neighbors(x, y) if self.grid[ny][nx] == -1)
        self.mines_placed = True
        self.start_mono = time.monotonic()

    def count_mines(self) -> int:
        return sum(1 for row in self.grid for value in row if value == -1)

    def flags_used(self) -> int:
        return sum(1 for row in self.flagged for value in row if value)

    def mines_left(self) -> int:
        return self.mines - self.flags_used()

    def elapsed_seconds(self) -> int:
        if self.start_mono is None:
            return 0
        return int(time.monotonic() - self.start_mono)

    def toggle_flag(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y) or self.revealed[y][x] or self.won or self.lost:
            return False
        self.flagged[y][x] = not self.flagged[y][x]
        return True

    def reveal(self, x: int, y: int) -> str:
        if not self.in_bounds(x, y) or self.flagged[y][x] or self.revealed[y][x] or self.won or self.lost:
            return "blocked"
        if not self.mines_placed:
            self.place_mines(x, y)

        if self.grid[y][x] == -1:
            self.revealed[y][x] = True
            self.reveal_all_mines()
            self.lost = True
            return "lost"

        expanded = False
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if self.flagged[cy][cx] or self.revealed[cy][cx]:
                continue
            self.revealed[cy][cx] = True
            if self.grid[cy][cx] == 0:
                expanded = True
                for nx, ny in self.neighbors(cx, cy):
                    if not self.revealed[ny][nx]:
                        stack.append((nx, ny))

        if self.check_win():
            self.won = True
            return "won"
        return "expanded" if expanded else "revealed"

    def reveal_all_mines(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == -1:
                    self.revealed[y][x] = True

    def check_win(self) -> bool:
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != -1 and not self.revealed[y][x]:
                    return False
        return True
