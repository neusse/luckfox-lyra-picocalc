#!/usr/bin/env python3
"""Graphical PicoCalc app launcher for the Luckfox Lyra console."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from picofb import BLUE, GREEN, RED, WHITE, YELLOW, Display, color565, load_bmp
from picoterm.appkeys import is_app_exit_key
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.keys import Key, KeyPress
from picoterm.screen import RawTerminal


PROJECT_ROOT = Path(os.environ.get("PICOCALC_APP_ROOT", "/home/neusse/luckfox-dev"))
DEFAULT_DATA = PROJECT_ROOT / "launcher" / "launcher_data.json"
LEGACY_DATA = Path("/mnt/sdcard/backup_2026-02-01_181033/launcher_data.json")
BATTERY_PATH = Path("/sys/bus/i2c/devices/0-001f/battery_percent")

WIDTH = 320
HEIGHT = 320
ICON_SIZE = 64
ICON_GAP = 10
MARGIN_X = 10
MARGIN_Y = 8
TOP_OFFSET = 10
TIME_H = 16
BANNER_H = 22
FOOTER_H = 20
GAP_Y = 2

BG = color565(7, 12, 10)
PANEL = color565(16, 29, 23)
TEXT = GREEN
MUTED = color565(142, 190, 152)
HILITE = color565(64, 208, 255)
PLACEHOLDER_BG = color565(18, 24, 22)
PLACEHOLDER_OUTLINE = color565(54, 88, 72)
PLACEHOLDER_TEXT = color565(210, 228, 208)
BANNER_BG = color565(20, 78, 42)
BANNER_TEXT = YELLOW
BADGE_READY = color565(32, 180, 92)
BADGE_MISSING = RED

PORTED_APPS = {
    "picocalc_ios_calculator.py": "calculator",
    "picocalc_breakout.py": "breakout",
    "picocalc_fancy_clock.py": "clock",
    "picocalc_minesweeper.py": "minesweeper",
    "picocalc_weather.py": "weather",
    "picocalc_sudoku.py": "sudoku",
    "picocalc_bubble_clean.py": "bubble",
    "picocalc_bubble.py": "bubble",
    "picocalc_zork.py": "zork",
}


@dataclass(frozen=True)
class LauncherEntry:
    name: str
    app: str
    bmp: str
    icon_path: Path | None
    command: list[str]
    source_path: Path | None
    ported: bool
    status: str
    placeholder: str


@dataclass(frozen=True)
class GridGeometry:
    columns: int
    rows: int
    per_page: int
    grid_x: int
    grid_y: int
    slot_w: int
    slot_h: int


def normalize_legacy_path(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text if text.startswith("/") else "/" + text


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)] + "..."


def command_for_entry(name: str, app: str, item: dict) -> list[str]:
    raw_command = item.get("command")
    if isinstance(raw_command, str) and raw_command.strip():
        return raw_command.split()
    if isinstance(raw_command, list) and all(isinstance(part, str) for part in raw_command):
        return list(raw_command)

    app_name = Path(app).name
    target = PORTED_APPS.get(app_name)
    if target:
        return ["picocalc-app", target]
    return []


def resolve_config_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    env_path = os.environ.get("PICOCALC_LAUNCHER_DATA")
    if env_path:
        return Path(env_path)
    if DEFAULT_DATA.exists():
        return DEFAULT_DATA
    return LEGACY_DATA


def resolve_asset_path(config_dir: Path, legacy_path: str) -> Path:
    relative = legacy_path.lstrip("/")
    return config_dir / relative


def source_path_for(config_dir: Path, app: str, item: dict) -> Path | None:
    raw = item.get("source")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw)
        return path if path.is_absolute() else config_dir / path
    if not app:
        return None
    candidate = resolve_asset_path(config_dir, app)
    return candidate if candidate.exists() else None


def load_launcher_entries(path: str | Path | None = None) -> list[LauncherEntry]:
    config_path = resolve_config_path(path)
    config_dir = config_path.parent
    data = json.loads(config_path.read_text(encoding="utf-8"))
    entries: list[LauncherEntry] = []

    for item in data.get("icons", []):
        name = str(item.get("name", "") or "App").strip() or "App"
        app = normalize_legacy_path(item.get("app", ""))
        bmp = normalize_legacy_path(item.get("bmp", ""))
        command = command_for_entry(name, app, item)
        icon_path = None
        if bmp:
            candidate = resolve_asset_path(config_dir, bmp)
            if candidate.exists():
                icon_path = candidate

        ported = bool(command)
        status = "ready" if ported else "not ported yet"
        entries.append(
            LauncherEntry(
                name=name,
                app=app,
                bmp=bmp,
                icon_path=icon_path,
                command=command,
                source_path=source_path_for(config_dir, app, item),
                ported=ported,
                status=status,
                placeholder=(name[:1] or "?").upper(),
            )
        )

    return entries


def compute_grid_geometry(width: int, height: int) -> GridGeometry:
    banner_y = TOP_OFFSET + TIME_H
    grid_top = banner_y + BANNER_H + GAP_Y
    grid_bottom = height - FOOTER_H - MARGIN_Y
    grid_height = max(ICON_SIZE, grid_bottom - grid_top)
    slot_w = ICON_SIZE + ICON_GAP
    slot_h = ICON_SIZE + ICON_GAP

    columns = max(1, (width - (2 * MARGIN_X) + ICON_GAP) // slot_w)
    rows = max(1, (grid_height + ICON_GAP) // slot_h)
    per_page = max(1, columns * rows)

    grid_w = (columns * ICON_SIZE) + ((columns - 1) * ICON_GAP)
    grid_h = (rows * ICON_SIZE) + ((rows - 1) * ICON_GAP)
    grid_x = (width - grid_w) // 2
    grid_y = grid_top + ((grid_height - grid_h) // 2)
    return GridGeometry(columns, rows, per_page, grid_x, grid_y, slot_w, slot_h)


def move_selection(selected: int, direction: str, count: int, geometry: GridGeometry) -> int:
    if count <= 0:
        return 0
    selected = max(0, min(selected, count - 1))
    if direction == "left":
        return max(0, selected - 1)
    if direction == "right":
        return min(count - 1, selected + 1)
    if direction == "up":
        return max(0, selected - geometry.columns)
    if direction == "down":
        return min(count - 1, selected + geometry.columns)
    return selected


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def require_console_tty(ttyname=None) -> None:
    ttyname = os.ttyname if ttyname is None else ttyname
    try:
        path = ttyname(0)
    except OSError as exc:
        raise SystemExit("launcher must be started from the PicoCalc console, not SSH or ADB") from exc
    if not is_console_tty(path):
        raise SystemExit(f"launcher must be started from the PicoCalc console; current terminal is {path}")


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def read_battery_percent(path: Path = BATTERY_PATH) -> int | None:
    try:
        return int(path.read_text(encoding="ascii").strip())
    except (FileNotFoundError, PermissionError, ValueError):
        return None


def draw_text(display: Display, text: object, x: int, y: int, color: int, *, scale: int = 1, background=None):
    display.text(str(text), x, y, color, background=background, scale=scale)


def draw_center_text(display: Display, text: str, y: int, color: int, *, scale: int = 1, background=None):
    width = len(text) * 6 * scale
    x = max(0, (display.width - width) // 2)
    draw_text(display, text, x, y, color, scale=scale, background=background)


def draw_right_text(display: Display, text: str, right: int, y: int, color: int, *, scale: int = 1, background=None):
    width = len(text) * 6 * scale
    draw_text(display, text, right - width, y, color, scale=scale, background=background)


def draw_placeholder(display: Display, entry: LauncherEntry, x: int, y: int):
    display.fill_rect(x, y, ICON_SIZE, ICON_SIZE, PLACEHOLDER_BG)
    display.rect(x, y, ICON_SIZE, ICON_SIZE, PLACEHOLDER_OUTLINE)
    draw_centered_box_text(display, entry.placeholder, x, y, ICON_SIZE, ICON_SIZE, PLACEHOLDER_TEXT, scale=3)


def draw_centered_box_text(
    display: Display,
    text: str,
    x: int,
    y: int,
    width: int,
    height: int,
    color: int,
    *,
    scale: int = 1,
):
    text_w = len(text) * 6 * scale
    text_h = 7 * scale
    draw_text(
        display,
        text,
        x + max(0, (width - text_w) // 2),
        y + max(0, (height - text_h) // 2),
        color,
        scale=scale,
    )


def draw_icon(display: Display, entry: LauncherEntry, x: int, y: int):
    if entry.icon_path is None:
        draw_placeholder(display, entry, x, y)
        return
    try:
        display.blit(load_bmp(entry.icon_path, transparent_index=None), x, y)
    except Exception:
        draw_placeholder(display, entry, x, y)


def header_text(battery: int | None = None) -> tuple[str, str]:
    now = datetime.now().astimezone()
    left = now.strftime("%H:%M:%S %Z  %m/%d/%y")
    right = f"Batt:{battery}%" if battery is not None else "Batt:?"
    return left, right


def draw_header(display: Display, battery: int | None):
    left, right = header_text(battery)
    display.fill_rect(0, 0, display.width, TOP_OFFSET + TIME_H, BG)
    draw_text(display, left, MARGIN_X, TOP_OFFSET, TEXT)
    draw_right_text(display, right, display.width - MARGIN_X, TOP_OFFSET, TEXT)


def draw_static(display: Display):
    banner_y = TOP_OFFSET + TIME_H
    display.fill(BG)
    display.fill_rect(0, banner_y, display.width, BANNER_H, BANNER_BG)
    draw_center_text(display, "LAUNCHER", banner_y + 5, BANNER_TEXT)


def draw_footer(display: Display, entry: LauncherEntry | None, page: int, page_count: int, message: str | None = None):
    y = display.height - FOOTER_H
    display.fill_rect(0, y, display.width, FOOTER_H, BG)
    if message:
        text = truncate(message, display.width // 6)
        color = YELLOW
    elif entry is None:
        text = "No launcher entries"
        color = YELLOW
    else:
        suffix = "" if entry.ported else " (not ported)"
        text = truncate(entry.name + suffix, 35)
        color = TEXT if entry.ported else MUTED
    draw_center_text(display, text, y + 2, color)
    draw_right_text(display, f"{page}/{page_count}", display.width - 4, y + 2, MUTED)


def draw_page(
    display: Display,
    entries: list[LauncherEntry],
    selected: int,
    geometry: GridGeometry,
    *,
    message: str | None = None,
):
    draw_static(display)
    draw_header(display, read_battery_percent())
    if not entries:
        draw_footer(display, None, 0, 0, message)
        return

    page_start = (selected // geometry.per_page) * geometry.per_page
    page = (selected // geometry.per_page) + 1
    page_count = ((len(entries) - 1) // geometry.per_page) + 1
    for slot in range(geometry.per_page):
        index = page_start + slot
        if index >= len(entries):
            break
        row = slot // geometry.columns
        col = slot % geometry.columns
        x = geometry.grid_x + (col * geometry.slot_w)
        y = geometry.grid_y + (row * geometry.slot_h)
        entry = entries[index]
        draw_icon(display, entry, x, y)
        badge = BADGE_READY if entry.ported else BADGE_MISSING
        display.fill_rect(x + ICON_SIZE - 8, y + ICON_SIZE - 8, 6, 6, badge)
        if index == selected:
            display.rect(x - 3, y - 3, ICON_SIZE + 6, ICON_SIZE + 6, HILITE)
            display.rect(x - 2, y - 2, ICON_SIZE + 4, ICON_SIZE + 4, HILITE)

    draw_footer(display, entries[selected], page, page_count, message)


def key_to_action(key: KeyPress | None) -> str | None:
    if key is None:
        return None
    if is_app_exit_key(key):
        return "quit"
    if key.name == Key.LEFT:
        return "left"
    if key.name == Key.RIGHT:
        return "right"
    if key.name == Key.UP:
        return "up"
    if key.name == Key.DOWN:
        return "down"
    if key.name == Key.ENTER:
        return "launch"
    if key.name in (Key.BACKSPACE, Key.ESCAPE):
        return "quit"
    if key.name == Key.CHAR:
        if key.value == "q":
            return "quit"
        if key.value == "s":
            return "screenshot"
        if key.value == "v":
            return "view"
    return None


def screenshot_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path.home() / "screenshots" / f"launcher-{stamp}.png"


def take_screenshot() -> str:
    output = screenshot_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["picocalc-screenshot", str(output)], check=True)
    return str(output)


def run_once(config: Path | None = None) -> int:
    entries = load_launcher_entries(config)
    with Display() as display:
        draw_page(display, entries, 0, compute_grid_geometry(display.width, display.height))
        display.show()
    return 0


def run_interactive(config: Path | None = None, keyboard_path: str | None = None) -> list[str] | None:
    require_console_tty()
    entries = load_launcher_entries(config)
    selected = 0
    last_header = 0.0
    message: str | None = None
    message_until = 0.0

    with RawTerminal(), Display() as display, open_keyboard(keyboard_path) as keyboard:
        geometry = compute_grid_geometry(display.width, display.height)
        draw_page(display, entries, selected, geometry)
        display.show()

        while True:
            now = time.monotonic()
            if message and now >= message_until:
                message = None
                draw_page(display, entries, selected, geometry)
                display.show()
            elif now - last_header >= 1.0:
                last_header = now
                draw_header(display, read_battery_percent())
                display.show_region(0, 0, display.width, TOP_OFFSET + TIME_H)

            action = key_to_action(keyboard.read_key(timeout=0.08))
            if action is None:
                continue
            if action == "quit":
                return None
            if action in {"left", "right", "up", "down"}:
                new_selected = move_selection(selected, action, len(entries), geometry)
                if new_selected != selected:
                    selected = new_selected
                    draw_page(display, entries, selected, geometry)
                    display.show()
                continue
            if action == "screenshot":
                try:
                    path = take_screenshot()
                    message = f"Saved {Path(path).name}"
                except Exception as exc:
                    message = f"Screenshot failed: {exc}"
                message_until = time.monotonic() + 1.2
                draw_page(display, entries, selected, geometry, message=message)
                display.show()
                continue
            if not entries:
                continue

            entry = entries[selected]
            if action == "view":
                if entry.source_path is None:
                    message = "No source path"
                else:
                    return ["picoedit.py", str(entry.source_path)]
            elif action == "launch":
                if not entry.command:
                    message = entry.status
                else:
                    return entry.command
            message_until = time.monotonic() + 1.0
            draw_page(display, entries, selected, geometry, message=message)
            display.show()


def run_child_command(command: list[str]) -> int:
    try:
        return subprocess.run(command, check=False).returncode
    except OSError:
        return 127


def run_launcher_session(interactive=run_interactive, runner=run_child_command) -> int:
    while True:
        command = interactive()
        if not command:
            return 0
        runner(command)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PicoCalc graphical app launcher")
    parser.add_argument("--config", type=Path, help="launcher JSON config path")
    parser.add_argument("--keyboard", help="evdev keyboard path, default: auto-detect PicoCalc keyboard")
    parser.add_argument("--once", action="store_true", help="render one launcher frame and exit")
    parser.add_argument("--list", action="store_true", help="print launcher entries and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.list:
        for entry in load_launcher_entries(args.config):
            command = " ".join(entry.command) if entry.command else entry.status
            print(f"{entry.name}: {command}")
        return 0
    if args.once:
        return run_once(args.config)
    return run_launcher_session(
        lambda: run_interactive(args.config, args.keyboard),
        run_child_command,
    )


if __name__ == "__main__":
    raise SystemExit(main())
