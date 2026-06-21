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
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"


@dataclass(frozen=True)
class KeyPress:
    name: str
    value: int | str | None = None
    raw: bytes = b""
    ctrl: bool = False
    shift: bool = False


_SEQUENCES = {
    b"\x1b[A": Key.UP,
    b"\x1b[B": Key.DOWN,
    b"\x1b[C": Key.RIGHT,
    b"\x1b[D": Key.LEFT,
    b"\x1b[3~": Key.DELETE,
    b"\x1bOP": Key.F1,
    b"\x1bOQ": Key.F2,
    b"\x1bOR": Key.F3,
    b"\x1bOS": Key.F4,
    b"\x1b[11~": Key.F1,
    b"\x1b[12~": Key.F2,
    b"\x1b[13~": Key.F3,
    b"\x1b[14~": Key.F4,
    b"\x1b[15~": Key.F5,
    b"\x1b[17~": Key.F6,
    b"\x1b[18~": Key.F7,
    b"\x1b[19~": Key.F8,
    b"\x1b[20~": Key.F9,
    b"\x1b[21~": Key.F10,
    b"\x1b[15;5~": Key.F5,
}


def parse_key(raw: bytes) -> KeyPress:
    """Convert one terminal key byte sequence into a small normalized event."""
    if raw in _SEQUENCES:
        return KeyPress(_SEQUENCES[raw], raw=raw, ctrl=b";5" in raw)
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
