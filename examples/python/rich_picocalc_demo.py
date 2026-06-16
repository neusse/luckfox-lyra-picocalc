"""Compact Rich terminal demo sized for the PicoCalc console."""

from __future__ import annotations

import argparse
from io import StringIO
from typing import BinaryIO, TextIO

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


PICO_WIDTH = 50


def build_demo() -> Group:
    """Build a bright Rich scene that fits on the PicoCalc terminal."""
    title = Text("Rich", style="bold magenta")
    title.append(" on ", style="white")
    title.append("Luckfox Lyra PicoCalc", style="bold cyan")

    ramp = Text()
    for color in ("red", "yellow", "green", "cyan", "blue", "magenta"):
        ramp.append("######", style=f"on {color}")

    features = Table.grid(padding=(0, 1))
    features.add_column(justify="right", style="bold yellow", no_wrap=True)
    features.add_column(style="white", no_wrap=True)
    features.add_row("Color", "ANSI blocks + truecolor")
    features.add_row("Style", "bold italic reverse")
    features.add_row("Markup", "tables logs panels")

    progress = Text("Progress ", style="bold magenta")
    progress.append("[", style="white")
    progress.append("####################", style="bold green")
    progress.append("------", style="dim")
    progress.append("] 77%", style="white")

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column(style="white", no_wrap=True)
    table.add_column(style="bold green", no_wrap=True)
    table.add_row("Table", "wifi", "up")
    table.add_row("Data", "screen", "320x320")
    table.add_row("Status", "rich", "clean")

    columns = Table.grid(padding=(0, 1))
    columns.add_column(style="bold red", no_wrap=True)
    columns.add_column(style="bold yellow", no_wrap=True)
    columns.add_column(style="bold green", no_wrap=True)
    columns.add_row("Columns", "Tools", "Logs")
    columns.add_row("Menus", "Stats", "Shell")

    markdown = Text()
    markdown.append("# Markdown", style="bold blue")
    markdown.append("\n- ")
    markdown.append("bold", style="bold")
    markdown.append(" / ")
    markdown.append("italic", style="italic")
    markdown.append(" / ")
    markdown.append("code", style="reverse")

    log = Text()
    log.append("09:41 ", style="dim")
    log.append("wifi up", style="green")
    log.append("\n09:42 ", style="dim")
    log.append("fb0 screenshot ok", style="cyan")
    log.append("\n09:43 ", style="dim")
    log.append("Rich render clean", style="magenta")

    return Group(
        Panel(
            Align.center(title),
            box=box.ASCII,
            border_style="magenta",
            padding=(0, 1),
        ),
        Panel(
            Align.center(ramp),
            title="Color",
            box=box.ASCII,
            border_style="red",
            padding=(0, 1),
        ),
        Panel(
            features,
            title="Rich features",
            box=box.ASCII,
            border_style="green",
            padding=(0, 1),
        ),
        Panel(
            progress,
            title="Progress",
            box=box.ASCII,
            border_style="cyan",
            padding=(0, 1),
        ),
        Panel(
            table,
            title="Table",
            box=box.ASCII,
            border_style="cyan",
            padding=(0, 1),
        ),
        Panel(
            columns,
            title="Columns",
            box=box.ASCII,
            border_style="magenta",
            padding=(0, 1),
        ),
        Panel(
            markdown,
            title="Markdown",
            box=box.ASCII,
            border_style="blue",
            padding=(0, 1),
        ),
        Panel(
            log,
            title="Log",
            box=box.ASCII,
            border_style="yellow",
            padding=(0, 1),
        ),
    )


def render_demo(width: int = PICO_WIDTH, color: bool = False) -> str:
    """Return a fixed-width capture of the compact demo."""
    buffer = StringIO()
    console = Console(
        file=buffer,
        width=width,
        height=20,
        color_system="standard" if color else None,
        force_terminal=color,
        legacy_windows=False,
        _environ={"COLUMNS": str(width), "LINES": "20"},
    )
    console.print(build_demo())
    return buffer.getvalue()


def write_demo(file: TextIO, width: int = PICO_WIDTH, clear: bool = True, crlf: bool = False) -> None:
    """Write the demo with terminal styling to an output stream."""
    if clear:
        file.write("\033[2J\033[H")
    output = render_demo(width=width, color=True)
    if crlf:
        output = output.replace("\n", "\r\n")
    file.write(output)
    file.flush()


def write_demo_bytes(file: BinaryIO, width: int = PICO_WIDTH, clear: bool = True) -> None:
    """Write exact terminal bytes for direct console devices such as /dev/tty1."""
    output = render_demo(width=width, color=True).replace("\n", "\r\n")
    data = output.encode("utf-8")
    if clear:
        data = b"\033[2J\033[H" + data
    file.write(data)
    file.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="Show a compact Rich demo for PicoCalc.")
    parser.add_argument("--width", type=int, default=PICO_WIDTH)
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--crlf", action="store_true", help="emit CRLF line endings for direct tty writes")
    parser.add_argument("--tty", help="write directly to a console device such as /dev/tty1")
    args = parser.parse_args()

    import sys

    if args.tty:
        with open(args.tty, "wb", buffering=0) as tty:
            write_demo_bytes(tty, width=args.width, clear=not args.no_clear)
        return 0

    write_demo(sys.stdout, width=args.width, clear=not args.no_clear, crlf=args.crlf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
