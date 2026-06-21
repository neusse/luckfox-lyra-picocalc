import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))


class PicoTermKeyTests(unittest.TestCase):
    def test_decodes_arrow_escape_sequences(self):
        from picoterm.keys import Key, parse_key

        self.assertEqual(parse_key(b"\x1b[A").name, Key.UP)
        self.assertEqual(parse_key(b"\x1b[B").name, Key.DOWN)
        self.assertEqual(parse_key(b"\x1b[C").name, Key.RIGHT)
        self.assertEqual(parse_key(b"\x1b[D").name, Key.LEFT)

    def test_decodes_editing_and_command_keys(self):
        from picoterm.keys import Key, parse_key

        self.assertEqual(parse_key(b"\r").name, Key.ENTER)
        self.assertEqual(parse_key(b"\n").name, Key.ENTER)
        self.assertEqual(parse_key(b"\x7f").name, Key.BACKSPACE)
        self.assertEqual(parse_key(b"\b").name, Key.BACKSPACE)
        self.assertEqual(parse_key(b"\x1b[3~").name, Key.DELETE)
        self.assertEqual(parse_key(b"\x1b").name, Key.ESCAPE)

    def test_decodes_digits_and_letters(self):
        from picoterm.keys import Key, parse_key

        digit = parse_key(b"5")
        self.assertEqual(digit.name, Key.DIGIT)
        self.assertEqual(digit.value, 5)

        letter = parse_key(b"q")
        self.assertEqual(letter.name, Key.CHAR)
        self.assertEqual(letter.value, "q")

    def test_decodes_terminal_function_keys(self):
        from picoterm.keys import Key, parse_key

        self.assertEqual(parse_key(b"\x1bOP").name, Key.F1)
        self.assertEqual(parse_key(b"\x1b[15~").name, Key.F5)
        self.assertEqual(parse_key(b"\x1b[21~").name, Key.F10)

    def test_decodes_ctrl_modified_terminal_function_key(self):
        from picoterm.appkeys import is_app_exit_key
        from picoterm.keys import parse_key

        self.assertTrue(is_app_exit_key(parse_key(b"\x1b[15;5~")))


if __name__ == "__main__":
    unittest.main()
