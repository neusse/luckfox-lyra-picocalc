"""ANSI screen and raw terminal helpers."""

from __future__ import annotations

import re
import select
import sys
from types import TracebackType
from typing import BinaryIO

from .keys import KeyPress, parse_key


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def clear_screen() -> str:
    return "\x1b[2J\x1b[H"


def hide_cursor() -> str:
    return "\x1b[?25l"


def show_cursor() -> str:
    return "\x1b[?25h"


def move_cursor(row: int, col: int) -> str:
    return f"\x1b[{row};{col}H"


class RawTerminal:
    """Context manager for raw key reads on a POSIX terminal."""

    def __init__(
        self,
        stdin: BinaryIO | None = None,
        stdout=None,
        escape_timeout: float = 0.02,
    ) -> None:
        self.stdin = stdin or sys.stdin.buffer
        self.stdout = stdout or sys.stdout
        self.escape_timeout = escape_timeout
        self._termios = None
        self._old_attrs = None

    def __enter__(self) -> "RawTerminal":
        import termios
        import tty

        self._termios = termios
        self._old_attrs = termios.tcgetattr(self.stdin)
        tty.setraw(self.stdin.fileno())
        self.stdout.write(hide_cursor())
        self.stdout.flush()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._termios is not None and self._old_attrs is not None:
            self._termios.tcsetattr(self.stdin, self._termios.TCSADRAIN, self._old_attrs)
        self.stdout.write(show_cursor())
        self.stdout.flush()

    def read_key(self, timeout: float | None = None) -> KeyPress | None:
        if timeout is not None:
            fd = self.stdin.fileno()
            ready, _, _ = select.select([fd], [], [], timeout)
            if not ready:
                return None

        raw = self.stdin.read(1)
        if raw == b"\x1b":
            fd = self.stdin.fileno()
            ready, _, _ = select.select([fd], [], [], self.escape_timeout)
            if ready:
                raw += self.stdin.read(1)
                if raw == b"\x1b[":
                    ready, _, _ = select.select([fd], [], [], self.escape_timeout)
                    if ready:
                        raw += self.stdin.read(1)
                        if raw[-1:] == b"3":
                            ready, _, _ = select.select([fd], [], [], self.escape_timeout)
                            if ready:
                                raw += self.stdin.read(1)
        return parse_key(raw)
