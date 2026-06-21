"""Four-function calculator model used by the PicoCalc framebuffer app."""

from __future__ import annotations

import math


OP_DISPLAY = {
    "+": "+",
    "-": "-",
    "*": "x",
    "/": "/",
}


def format_number(value: float, max_len: int = 12) -> str:
    if math.isinf(value) or math.isnan(value):
        return "Error"
    if abs(value - int(value)) < 1e-10:
        text = str(int(value))
    else:
        text = f"{value:.8f}".rstrip("0").rstrip(".")
    if len(text) > max_len:
        text = f"{value:.8g}"
    return text


def apply_op(a: float, b: float, op: str) -> float:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return a / b if b != 0 else float("inf")
    return b


class CalculatorState:
    def __init__(self) -> None:
        self.acc = 0.0
        self.pending_op: str | None = None
        self.last_op: str | None = None
        self.last_operand: float | None = None
        self.entering = False
        self.input_text = "0"
        self.expression = ""

    @property
    def display(self) -> str:
        return self.input_text

    @property
    def clear_label(self) -> str:
        if self.input_text != "0" or self.entering or self.pending_op is not None:
            return "C"
        return "AC"

    def commit_input(self) -> float:
        if self.input_text in ("", "-", "Error"):
            return 0.0
        try:
            return float(self.input_text)
        except ValueError:
            return 0.0

    def press(self, key: str) -> None:
        if len(key) == 1 and key.isdigit():
            self.digit(key)
        elif key == ".":
            self.decimal()
        elif key in ("+", "-", "*", "/", "x", "X"):
            self.operator("*" if key in ("x", "X") else key)
        elif key in ("=", "\n", "\r"):
            self.equals()
        elif key in ("c", "C", "AC"):
            self.clear()
        elif key in ("p", "P", "%"):
            self.percent()
        elif key in ("s", "S", "+/-"):
            self.sign()
        elif key == "backspace":
            self.backspace()

    def digit(self, ch: str) -> None:
        if self.input_text == "Error":
            self.clear_all()
        if not self.entering:
            self.input_text = ch
            self.entering = True
        elif self.input_text == "0" and ch != ".":
            self.input_text = ch
        else:
            self.input_text += ch

    def decimal(self) -> None:
        if self.input_text == "Error":
            self.clear_all()
        if not self.entering:
            self.input_text = "0."
            self.entering = True
        elif "." not in self.input_text:
            self.input_text += "."

    def clear(self) -> None:
        if self.input_text != "0" or self.entering:
            self.input_text = "0"
            self.entering = False
        else:
            self.clear_all()

    def clear_all(self) -> None:
        self.acc = 0.0
        self.pending_op = None
        self.last_op = None
        self.last_operand = None
        self.entering = False
        self.input_text = "0"
        self.expression = ""

    def sign(self) -> None:
        if self.input_text == "Error":
            return
        if self.input_text.startswith("-"):
            self.input_text = self.input_text[1:]
        elif self.input_text != "0":
            self.input_text = "-" + self.input_text
        self.entering = True

    def percent(self) -> None:
        value = self.commit_input() / 100.0
        self.input_text = format_number(value)
        self.entering = True

    def operator(self, op: str) -> None:
        value = self.commit_input()
        if self.pending_op is not None and self.entering:
            self.acc = apply_op(self.acc, value, self.pending_op)
        elif self.pending_op is None:
            self.acc = value
        self.pending_op = op
        self.entering = False
        self.input_text = format_number(self.acc)
        self.expression = f"{format_number(self.acc)} {OP_DISPLAY.get(op, op)}"
        self.last_op = None
        self.last_operand = None

    def equals(self) -> None:
        value = self.commit_input()
        if self.pending_op is not None:
            self.expression = (
                f"{format_number(self.acc)} "
                f"{OP_DISPLAY.get(self.pending_op, self.pending_op)} "
                f"{format_number(value)}"
            )
            self.acc = apply_op(self.acc, value, self.pending_op)
            self.last_op = self.pending_op
            self.last_operand = value
            self.pending_op = None
            self.entering = False
            self.input_text = format_number(self.acc)
            return
        if self.last_op is not None and self.last_operand is not None:
            self.acc = apply_op(self.acc, self.last_operand, self.last_op)
            self.input_text = format_number(self.acc)

    def backspace(self) -> None:
        if self.entering and len(self.input_text) > 1:
            self.input_text = self.input_text[:-1]
        else:
            self.input_text = "0"
            self.entering = False
