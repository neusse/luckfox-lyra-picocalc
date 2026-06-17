"""Keyboard decoding for small Linux console apps."""

from __future__ import annotations

from dataclasses import dataclass


class Key:
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    ENTER = "enter"
    BACKSPACE = "backspace"
    DELETE = "delete"
    ESCAPE = "escape"
    DIGIT = "digit"
    CHAR = "char"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class KeyPress:
    name: str
    value: int | str | None = None
    raw: bytes = b""


_SEQUENCES = {
    b"\x1b[A": Key.UP,
    b"\x1b[B": Key.DOWN,
    b"\x1b[C": Key.RIGHT,
    b"\x1b[D": Key.LEFT,
    b"\x1b[3~": Key.DELETE,
}


def parse_key(raw: bytes) -> KeyPress:
    """Convert one terminal key byte sequence into a small normalized event."""
    if raw in _SEQUENCES:
        return KeyPress(_SEQUENCES[raw], raw=raw)
    if raw in (b"\r", b"\n"):
        return KeyPress(Key.ENTER, raw=raw)
    if raw in (b"\x7f", b"\b"):
        return KeyPress(Key.BACKSPACE, raw=raw)
    if raw == b"\x1b":
        return KeyPress(Key.ESCAPE, raw=raw)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return KeyPress(Key.UNKNOWN, raw=raw)

    if len(text) != 1:
        return KeyPress(Key.UNKNOWN, raw=raw)
    if "0" <= text <= "9":
        return KeyPress(Key.DIGIT, int(text), raw)
    if text.isprintable():
        return KeyPress(Key.CHAR, text, raw)
    return KeyPress(Key.UNKNOWN, raw=raw)
