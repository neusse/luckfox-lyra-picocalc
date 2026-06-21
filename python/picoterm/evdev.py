"""Linux evdev keyboard reader for PicoCalc apps."""

from __future__ import annotations

import os
import select
import struct
from pathlib import Path

from .keys import Key, KeyPress


EV_KEY = 0x01
KEY_ESC = 1
KEY_1 = 2
KEY_2 = 3
KEY_3 = 4
KEY_4 = 5
KEY_5 = 6
KEY_6 = 7
KEY_7 = 8
KEY_8 = 9
KEY_9 = 10
KEY_0 = 11
KEY_MINUS = 12
KEY_EQUAL = 13
KEY_BACKSPACE = 14
KEY_P = 25
KEY_Q = 16
KEY_LEFTSHIFT = 42
KEY_X = 45
KEY_C = 46
KEY_DOT = 52
KEY_SLASH = 53
KEY_RIGHTSHIFT = 54
KEY_Y = 21
KEY_ENTER = 28
KEY_LEFTCTRL = 29
KEY_A = 30
KEY_SPACE = 57
KEY_F1 = 59
KEY_F2 = 60
KEY_F3 = 61
KEY_F4 = 62
KEY_F5 = 63
KEY_F6 = 64
KEY_F7 = 65
KEY_F8 = 66
KEY_F9 = 67
KEY_F10 = 68
KEY_RIGHTCTRL = 97
KEY_S = 31
KEY_D = 32
KEY_H = 35
KEY_J = 36
KEY_K = 37
KEY_L = 38
KEY_N = 49
KEY_DELETE = 111
KEY_UP = 103
KEY_LEFT = 105
KEY_RIGHT = 106
KEY_DOWN = 108

EVENT32_SIZE = 16
EVENT64_SIZE = 24

_CODE_TO_KEY = {
    KEY_ESC: Key.ESCAPE,
    KEY_ENTER: Key.ENTER,
    KEY_BACKSPACE: Key.BACKSPACE,
    KEY_DELETE: Key.DELETE,
    KEY_UP: Key.UP,
    KEY_DOWN: Key.DOWN,
    KEY_LEFT: Key.LEFT,
    KEY_RIGHT: Key.RIGHT,
    KEY_F1: Key.F1,
    KEY_F2: Key.F2,
    KEY_F3: Key.F3,
    KEY_F4: Key.F4,
    KEY_F5: Key.F5,
    KEY_F6: Key.F6,
    KEY_F7: Key.F7,
    KEY_F8: Key.F8,
    KEY_F9: Key.F9,
    KEY_F10: Key.F10,
}
_DIGITS = {
    KEY_0: 0,
    KEY_1: 1,
    KEY_2: 2,
    KEY_3: 3,
    KEY_4: 4,
    KEY_5: 5,
    KEY_6: 6,
    KEY_7: 7,
    KEY_8: 8,
    KEY_9: 9,
}
_CHARS = {
    KEY_A: "a",
    KEY_MINUS: "-",
    KEY_EQUAL: "=",
    KEY_Q: "q",
    KEY_P: "p",
    KEY_X: "x",
    KEY_C: "c",
    KEY_DOT: ".",
    KEY_SLASH: "/",
    KEY_S: "s",
    KEY_D: "d",
    KEY_SPACE: " ",
    KEY_Y: "y",
    KEY_N: "n",
    KEY_H: "h",
    KEY_J: "j",
    KEY_K: "k",
    KEY_L: "l",
}
_SHIFT_CHARS = {
    KEY_5: "%",
    KEY_8: "*",
    KEY_EQUAL: "+",
}


def parse_input_event(data: bytes, *, ctrl: bool = False, shift: bool = False) -> KeyPress | None:
    """Parse one Linux input_event and return a normalized key press."""
    if len(data) not in (EVENT32_SIZE, EVENT64_SIZE):
        raise ValueError(f"unexpected input_event size: {len(data)}")

    event_type, code, value = struct.unpack_from("<HHi", data, len(data) - 8)
    if event_type != EV_KEY or value == 0:
        return None
    if code in (KEY_LEFTCTRL, KEY_RIGHTCTRL, KEY_LEFTSHIFT, KEY_RIGHTSHIFT):
        return None

    if shift and code in _SHIFT_CHARS:
        return KeyPress(Key.CHAR, _SHIFT_CHARS[code], data, ctrl=ctrl, shift=shift)
    if code in _DIGITS:
        return KeyPress(Key.DIGIT, _DIGITS[code], data, ctrl=ctrl, shift=shift)
    if code in _CHARS:
        return KeyPress(Key.CHAR, _CHARS[code], data, ctrl=ctrl, shift=shift)
    if code in _CODE_TO_KEY:
        return KeyPress(_CODE_TO_KEY[code], raw=data, ctrl=ctrl, shift=shift)
    return KeyPress(Key.UNKNOWN, code, data, ctrl=ctrl, shift=shift)


def find_picocalc_event(proc_devices: str | Path = "/proc/bus/input/devices") -> str:
    """Return the event device path for the PicoCalc keyboard."""
    text = Path(proc_devices).read_text(encoding="ascii", errors="ignore")
    for block in text.split("\n\n"):
        if 'Name="Picocalc Keyboard"' not in block and 'Name="PicoCalc Keyboard"' not in block:
            continue
        for line in block.splitlines():
            if line.startswith("H: Handlers="):
                for handler in line.split("=", 1)[1].split():
                    if handler.startswith("event"):
                        return "/dev/input/" + handler
    raise FileNotFoundError("Picocalc Keyboard event device not found")


class EventKeyboard:
    """Non-blocking key reader for a Linux evdev keyboard device."""

    def __init__(self, path: str | None = None, event_size: int = EVENT32_SIZE):
        self.path = path or find_picocalc_event()
        self.event_size = event_size
        self.fd: int | None = None
        self.ctrl_down = False
        self.shift_down = False

    def __enter__(self) -> "EventKeyboard":
        self.fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def read_key(self, timeout: float | None = None) -> KeyPress | None:
        if self.fd is None:
            raise RuntimeError("keyboard is not open")

        wait = None if timeout is None else max(0.0, timeout)
        ready, _, _ = select.select([self.fd], [], [], wait)
        if not ready:
            return None

        while True:
            try:
                data = os.read(self.fd, self.event_size)
            except BlockingIOError:
                return None
            if len(data) != self.event_size:
                return None
            event_type, code, value = struct.unpack_from("<HHi", data, len(data) - 8)
            if event_type == EV_KEY and code in (KEY_LEFTCTRL, KEY_RIGHTCTRL):
                self.ctrl_down = value != 0
                continue
            if event_type == EV_KEY and code in (KEY_LEFTSHIFT, KEY_RIGHTSHIFT):
                self.shift_down = value != 0
                continue
            key = parse_input_event(data, ctrl=self.ctrl_down, shift=self.shift_down)
            if key is not None:
                return key
