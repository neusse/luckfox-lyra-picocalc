"""Line-oriented Z-machine shell for Linux terminals."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path

from .zmachine_opcodes import Frame, ZProcessor


SUPPORTED_VERSIONS = {3}
DEFAULT_STORY_DIR = Path("/mnt/sdcard/cpz/stories")
DEFAULT_SAVE_DIR = Path("/mnt/sdcard/cpz/saves")
DEFAULT_CONSOLE_FONT = "40"
MAX_STORY_SIZE = 1024 * 1024
ANSI_RESET = "\033[0m"
ANSI_GREEN = "\033[92m"
ANSI_BLACK_ON_GREEN = "\033[30;42m"
ANSI_CLEAR = "\033[2J\033[H"


@dataclass(frozen=True)
class TerminalProfile:
    columns: int
    rows: int
    physical_console: bool


def is_physical_console(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def terminal_tty(ttyname=None) -> str:
    if ttyname is None:
        ttyname = os.ttyname
    for fd in (0, 1):
        try:
            return ttyname(fd)
        except OSError:
            continue
    return ""


def detect_terminal_profile(
    *,
    width: int | None = None,
    tty_path: str | None = None,
) -> TerminalProfile:
    tty_path = terminal_tty() if tty_path is None else tty_path
    physical = is_physical_console(tty_path)
    fallback = (40, 20) if physical else (80, 24)
    size = shutil.get_terminal_size(fallback=fallback)
    columns = int(width or size.columns or fallback[0])
    rows = int(size.lines or fallback[1])
    if physical:
        columns = min(columns, 40)
    return TerminalProfile(columns=max(20, columns), rows=max(8, rows), physical_console=physical)


def maybe_set_console_font(
    font: str | None,
    *,
    physical_console: bool,
    runner=subprocess.run,
) -> None:
    if not physical_console or not font or font == "none":
        return
    runner(
        ["picofont", font],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


class TerminalZMachine:
    """Minimal terminal host for the CPZ Machine opcode processor."""

    def __init__(
        self,
        *,
        story_dir: str | Path = DEFAULT_STORY_DIR,
        save_dir: str | Path = DEFAULT_SAVE_DIR,
        columns: int | None = None,
        font: str | None = DEFAULT_CONSOLE_FONT,
        tty_path: str | None = None,
        status: bool = True,
        color: str = "auto",
    ):
        profile = detect_terminal_profile(width=columns, tty_path=tty_path)
        maybe_set_console_font(font, physical_console=profile.physical_console)
        if profile.physical_console and not columns:
            profile = detect_terminal_profile(width=40, tty_path=tty_path)

        self.profile = profile
        self.story_dir = Path(story_dir)
        self.save_dir = Path(save_dir)
        self.show_status = status
        self.color_mode = color
        self.debug = 0
        self.filename = ""
        self.save_game_name = "default"
        self.STACK_SIZE = 1024
        self.story_data = b""
        self.memory = bytearray()
        self.pc = 0
        self.call_stack: list[Frame] = []
        self.objects: dict[int, int] = {}
        self.dictionary: dict[str, object] = {}
        self.dictionary_size = 0
        self.dictionary_offset = 0
        self.lines_written = 0
        self.game_running = False
        self.z_version = 0
        self.processor: ZProcessor | None = None
        self.last_status = ""
        self.screen_ready = False

    @property
    def use_color(self) -> bool:
        if self.color_mode == "never":
            return False
        if self.color_mode == "always":
            return True
        return sys.stdout.isatty() or self.profile.physical_console

    @property
    def body_rows(self) -> int:
        return max(1, self.text_rows - 2)

    def _style(self, text: str, code: str) -> str:
        if not self.use_color:
            return text
        return f"{code}{text}{ANSI_RESET}"

    @property
    def text_cols(self) -> int:
        return self.profile.columns

    @property
    def text_rows(self) -> int:
        return self.profile.rows

    def load_story(self, filename: str) -> bool:
        try:
            story_path = self.story_dir / filename
            story = story_path.read_bytes()
            if len(story) > MAX_STORY_SIZE:
                raise ValueError(f"story file too large: {len(story)} bytes")
            if len(story) < 64:
                raise ValueError("invalid story file: header is too short")

            self.z_version = story[0]
            if self.z_version not in SUPPORTED_VERSIONS:
                raise ValueError(f"unsupported Z-machine version: {self.z_version}")

            self.story_data = story
            self.memory = bytearray(story)
            if len(self.memory) < 65536:
                self.memory.extend(bytearray(65536 - len(self.memory)))

            self.pc = self.read_word(0x06)
            self.dictionary_addr = self.read_word(0x08)
            self.object_table_addr = self.read_word(0x0A)
            self.variables_addr = self.read_word(0x0C)
            self.abbreviations_addr = self.read_word(0x18)
            self.synonyms_offset = self.read_word(0x18)
            self.call_stack = []
            self.init_objects()
            self.init_dictionary()
            self.processor = ZProcessor(self)
            self.filename = filename
            self.print_text(f"Loaded {filename} ({len(story)} bytes)")
            return True
        except Exception as exc:
            self.print_error(f"Error loading story: {exc}")
            return False

    def read_byte(self, addr: int) -> int:
        if 0 <= addr < len(self.memory):
            return self.memory[addr]
        return 0

    def read_word(self, addr: int) -> int:
        if 0 <= addr + 1 < len(self.memory):
            return (self.memory[addr] << 8) | self.memory[addr + 1]
        return 0

    def write_byte(self, addr: int, value: int) -> None:
        if 0 <= addr < len(self.memory):
            self.memory[addr] = value & 0xFF

    def write_word(self, addr: int, value: int) -> None:
        if 0 <= addr + 1 < len(self.memory):
            self.memory[addr] = (value >> 8) & 0xFF
            self.memory[addr + 1] = value & 0xFF

    def init_objects(self) -> None:
        if self.object_table_addr == 0:
            return
        defaults_size = 31 if self.z_version <= 3 else 63
        obj_start = self.object_table_addr + (defaults_size * 2)
        obj_size = 9 if self.z_version <= 3 else 14
        self.objects = {}
        for number in range(1, 256):
            address = obj_start + (number - 1) * obj_size
            if address + obj_size > len(self.memory):
                break
            self.objects[number] = address

    def init_dictionary(self) -> None:
        if self.dictionary_addr == 0:
            return
        sep_count = self.read_byte(self.dictionary_addr)
        dict_start = self.dictionary_addr + 1 + sep_count
        entry_length = self.read_byte(dict_start)
        self.dictionary_size = self.read_word(dict_start + 1)
        self.dictionary_offset = dict_start + 3
        self.dictionary = {
            "separators": [self.read_byte(self.dictionary_addr + 1 + i) for i in range(sep_count)],
            "entry_length": entry_length,
            "start_addr": self.dictionary_offset,
        }

    def _write(self, value: str = "", *, end: str = "\n") -> None:
        print(value, end=end, flush=True)

    def setup_screen(self) -> None:
        if self.screen_ready:
            return
        if self.profile.physical_console:
            self._write(ANSI_CLEAR, end="")
            self._write(f"\033[3;{self.text_rows}r\033[3;1H", end="")
        self.screen_ready = True

    def restore_screen(self) -> None:
        if not self.screen_ready:
            return
        if self.profile.physical_console:
            self._write(f"\033[1;{self.text_rows}r\033[{self.text_rows};1H{ANSI_RESET}", end="")
        elif self.use_color:
            self._write(ANSI_RESET, end="")
        self.screen_ready = False

    def _ansi_status(self, text: str) -> None:
        if not self.show_status:
            return
        text = text[: self.text_cols].ljust(self.text_cols)
        self.last_status = text
        if self.profile.physical_console:
            self.setup_screen()
            status = self._style(text, ANSI_BLACK_ON_GREEN)
            self._write(f"\0337\033[1;1H{status}\033[2;1H{' ' * self.text_cols}\0338", end="")
        else:
            self._write(self._style(f"[{text.rstrip()}]", ANSI_BLACK_ON_GREEN))

    def print_text(self, text: object) -> None:
        self.setup_screen()
        raw = str(text)
        for paragraph in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            if not paragraph:
                self._write()
                self.lines_written += 1
                self._page_if_needed()
                continue
            for line in textwrap.wrap(
                paragraph,
                width=self.text_cols,
                replace_whitespace=False,
                drop_whitespace=True,
                break_long_words=True,
            ):
                self._write(self._style(line, ANSI_GREEN))
                self.lines_written += 1
                self._page_if_needed()

    def _page_if_needed(self) -> None:
        if not self.profile.physical_console:
            return
        if self.lines_written <= max(1, self.body_rows - 1):
            return
        self.lines_written = 0
        self._write(self._style("Press <Enter> key to continue", ANSI_GREEN), end="")
        try:
            input()
        except EOFError:
            pass
        self._write("\r" + (" " * self.text_cols) + "\r", end="")

    def print_debug(self, level: int, msg: str) -> None:
        if self.debug >= level:
            self.print_text(f"debug:{msg}")

    def print_error(self, error_msg: str) -> None:
        self.print_text(f"*** ERROR: {error_msg}")

    def update_status_line(self, location: str = "", score: object = "", moves: object = "") -> None:
        if self.z_version <= 3:
            status = f" {location:<18} S:{score:>3} M:{moves:>3}"
        else:
            status = f" {location:<24} {score:>5}:{moves:>02}"
        self._ansi_status(status)

    def get_input(self) -> str:
        self.lines_written = 0
        try:
            return input(self._style("> ", ANSI_GREEN))
        except EOFError:
            self.game_running = False
            return "quit"

    def show_input_prompt(self) -> None:
        self._write(self._style("> ", ANSI_GREEN), end="")

    def get_stories(self) -> list[str]:
        try:
            files = os.listdir(self.story_dir)
        except OSError as exc:
            self.print_error(f"Error getting stories from {self.story_dir}: {exc}")
            return []
        return sorted(f for f in files if f.lower().endswith((".z3", ".z5", ".z8", ".dat", ".zip")))

    def list_stories(self) -> list[str]:
        stories = self.get_stories()
        if not stories:
            self.print_text("No story files found.")
            self.print_text(f"Copy Z-machine story files to {self.story_dir}/")
        else:
            self.print_text("Available stories:")
            for index, filename in enumerate(stories, 1):
                self.print_text(f"  {index}. {filename}")
        return stories

    def choose_story(self, requested: str | None = None) -> str | None:
        stories = self.get_stories()
        if requested:
            if requested in stories:
                return requested
            matches = [story for story in stories if story.lower().startswith(requested.lower())]
            if len(matches) == 1:
                return matches[0]
            self.print_error(f"Story not found: {requested}")
            return None
        if len(stories) == 1:
            return stories[0]
        self.list_stories()
        if not stories:
            return None
        while True:
            answer = self.get_input().strip()
            if answer in {"0", "q", "quit", "exit"}:
                return None
            try:
                index = int(answer)
            except ValueError:
                self.print_error(f"Select a number between 1 and {len(stories)}, or 0 to exit.")
                continue
            if 1 <= index <= len(stories):
                return stories[index - 1]
            self.print_error(f"Select a number between 1 and {len(stories)}, or 0 to exit.")

    def get_save_game_name(self) -> str:
        self.print_text(f"Enter file name ({self.save_game_name}):")
        name = self.get_input().lower().strip()
        return name or self.save_game_name

    def _save_path(self, save: str) -> Path:
        base = Path(self.filename).stem.lower()
        return self.save_dir / f"{base}.{save}.sav"

    def restore_game(self) -> bool:
        save = self.get_save_game_name()
        save_path = self._save_path(save)
        try:
            with save_path.open("rb") as handle:
                magic = handle.read(4)
                if magic != b"ZSAV":
                    raise ValueError("invalid save file")
                version = int.from_bytes(handle.read(1), "big")
                if version != self.z_version:
                    raise ValueError("save file version mismatch")
                self.pc = int.from_bytes(handle.read(2), "big")
                mem_size = int.from_bytes(handle.read(2), "big")
                self.memory[0:mem_size] = handle.read(mem_size)
                stack_size = int.from_bytes(handle.read(2), "big")
                self.call_stack = []
                for _ in range(stack_size):
                    frame_size = int.from_bytes(handle.read(2), "big")
                    frame = Frame()
                    frame.unserialize(handle.read(frame_size), 0)
                    self.call_stack.append(frame)
            self.save_game_name = save
            self.print_text(f"Game restored from {save}")
            return True
        except Exception as exc:
            self.print_error(f"Restore failed: {exc}")
            return False

    def save_game(self) -> bool:
        save = self.get_save_game_name()
        save_path = self._save_path(save)
        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)
            with save_path.open("wb") as handle:
                handle.write(b"ZSAV")
                handle.write(self.z_version.to_bytes(1, "big"))
                handle.write(self.pc.to_bytes(2, "big"))
                mem_size = self.read_word(0x0E)
                handle.write(mem_size.to_bytes(2, "big"))
                handle.write(self.memory[0:mem_size])
                handle.write(len(self.call_stack).to_bytes(2, "big"))
                for frame in self.call_stack:
                    data = frame.serialize(0)
                    handle.write(len(data).to_bytes(2, "big"))
                    handle.write(data)
            self.save_game_name = save
            self.print_text(f"Game saved as {save}")
            return True
        except Exception as exc:
            self.print_error(f"Save failed: {exc}")
            return False

    def restart_game(self) -> bool:
        try:
            story_path = self.story_dir / self.filename
            mem_size = self.read_word(0x0E)
            self.memory[0:mem_size] = story_path.read_bytes()[0:mem_size]
            self.pc = self.read_word(0x06)
            self.call_stack = []
            if self.processor:
                self.processor.init_frame()
            return True
        except Exception as exc:
            self.print_error(f"Restart failed: {exc}")
            return False

    def run_interpreter(self, story: str | None = None) -> int:
        try:
            self.setup_screen()
            self._ansi_status(" PicoZork")
            self.game_running = True
            self.print_text(f"Stories: {self.story_dir}")
            self.print_text(f"Terminal: {self.text_cols}x{self.text_rows}")
            selected = self.choose_story(story)
            if not selected:
                return 1
            if not self.load_story(selected):
                return 1
            self.execute_game()
            return 0
        finally:
            self.restore_screen()

    def execute_game(self) -> None:
        if not self.processor:
            self.processor = ZProcessor(self)
        try:
            self.processor.init_frame()
            while self.game_running and self.pc < len(self.memory):
                self.processor.execute_instruction()
                if self.processor.instruction_count % 100 == 0:
                    time.sleep(0.001)
        except KeyboardInterrupt:
            self.print_text("\nGame interrupted.")
            self.game_running = False
        except Exception as exc:
            self.print_error(f"Game execution error: {exc}")
            self.game_running = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Zork/Z-machine v3 stories on the PicoCalc terminal.")
    parser.add_argument("story", nargs="?", help="story filename or unique prefix")
    parser.add_argument("--story-dir", default=str(DEFAULT_STORY_DIR))
    parser.add_argument("--save-dir", default=str(DEFAULT_SAVE_DIR))
    parser.add_argument("--font", default=DEFAULT_CONSOLE_FONT, help="console font: 40, small, original, none")
    parser.add_argument("--width", type=int, help="override terminal width")
    parser.add_argument("--list", action="store_true", help="list stories and exit")
    parser.add_argument("--no-status", action="store_true", help="disable status-line output")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    machine = TerminalZMachine(
        story_dir=args.story_dir,
        save_dir=args.save_dir,
        columns=args.width,
        font=args.font,
        status=not args.no_status,
        color=args.color,
    )
    if args.list:
        return 0 if machine.list_stories() else 1
    return machine.run_interpreter(args.story)


if __name__ == "__main__":
    raise SystemExit(main())
