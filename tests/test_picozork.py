import io
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from picozork.terminal import (
    ANSI_BLACK_ON_GREEN,
    ANSI_GREEN,
    DEFAULT_SAVE_DIR,
    DEFAULT_STORY_DIR,
    TerminalZMachine,
    detect_terminal_profile,
    maybe_set_console_font,
    terminal_tty,
)
from picozork.zmachine_opcodes import Frame


class PicoZorkTests(unittest.TestCase):
    def test_defaults_use_picocalc_cpz_sdcard_paths(self):
        self.assertEqual(DEFAULT_STORY_DIR, Path("/mnt/sdcard/cpz/stories"))
        self.assertEqual(DEFAULT_SAVE_DIR, Path("/mnt/sdcard/cpz/saves"))

    def test_physical_console_caps_width_at_40_columns(self):
        profile = detect_terminal_profile(width=80, tty_path="/dev/tty1")

        self.assertEqual(profile.columns, 40)
        self.assertTrue(profile.physical_console)

    def test_remote_terminal_keeps_requested_width(self):
        profile = detect_terminal_profile(width=72, tty_path="/dev/pts/0")

        self.assertEqual(profile.columns, 72)
        self.assertFalse(profile.physical_console)

    def test_terminal_tty_falls_back_to_stdout(self):
        def ttyname(fd):
            if fd == 0:
                raise OSError("stdin is a pipe")
            return "/dev/tty1"

        self.assertEqual(terminal_tty(ttyname), "/dev/tty1")

    def test_console_font_runs_only_for_physical_console(self):
        calls = []

        def runner(cmd, **kwargs):
            calls.append((cmd, kwargs))

        maybe_set_console_font("40", physical_console=False, runner=runner)
        maybe_set_console_font("40", physical_console=True, runner=runner)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], ["picofont", "40"])

    def test_story_listing_accepts_zork_zip_story_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "zork1.zip").write_bytes(b"\x03" + b"\0" * 80)
            (root / "notes.txt").write_text("ignore")
            machine = TerminalZMachine(story_dir=root, tty_path="/dev/pts/0")

            self.assertEqual(machine.get_stories(), ["zork1.zip"])

    def test_text_output_wraps_to_40_column_console_width(self):
        machine = TerminalZMachine(
            story_dir=Path("."),
            columns=40,
            tty_path="/dev/tty1",
            font="none",
            color="never",
        )
        out = io.StringIO()

        with redirect_stdout(out):
            machine.print_text("This is a deliberately long Zork line that should wrap on the PicoCalc screen.")

        lines = [
            line
            for line in out.getvalue().splitlines()
            if line and not line.startswith("\033")
        ]
        self.assertTrue(lines)
        self.assertTrue(all(len(line) <= 40 for line in lines))

    def test_console_status_uses_black_on_green_title_bar(self):
        machine = TerminalZMachine(
            story_dir=Path("."),
            columns=40,
            tty_path="/dev/tty1",
            font="none",
            color="always",
        )
        out = io.StringIO()

        with redirect_stdout(out):
            machine._ansi_status(" West of House S:  0 M:  1")

        text = out.getvalue()
        self.assertIn(ANSI_BLACK_ON_GREEN, text)
        self.assertIn("West of House", text)
        self.assertIn("\033[1;1H", text)

    def test_console_screen_sets_body_scroll_region_below_title_bar(self):
        machine = TerminalZMachine(
            story_dir=Path("."),
            columns=40,
            tty_path="/dev/tty1",
            font="none",
            color="never",
        )
        out = io.StringIO()

        with redirect_stdout(out):
            machine.setup_screen()
            machine.restore_screen()

        text = out.getvalue()
        self.assertIn("\033[3;20r", text)
        self.assertIn("\033[1;20r", text)

    def test_text_uses_green_theme_when_color_enabled(self):
        machine = TerminalZMachine(
            story_dir=Path("."),
            columns=40,
            tty_path="/dev/pts/0",
            font="none",
            color="always",
        )
        out = io.StringIO()

        with redirect_stdout(out):
            machine.print_text("green text")

        self.assertIn(ANSI_GREEN, out.getvalue())

    def test_frame_save_data_round_trips(self):
        frame = Frame()
        frame.return_pointer = 0x12345678
        frame.ctype = 0x1000
        frame.local_vars[0] = 42
        frame.data_stack = [1, 2, 65535]

        restored = Frame()
        restored.unserialize(frame.serialize(0), 0)

        self.assertEqual(restored.return_pointer, frame.return_pointer)
        self.assertEqual(restored.ctype, frame.ctype)
        self.assertEqual(restored.local_vars[0], 42)
        self.assertEqual(restored.data_stack, [1, 2, 65535])


if __name__ == "__main__":
    unittest.main()
