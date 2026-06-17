import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))


class EvdevKeyTests(unittest.TestCase):
    def test_decodes_linux_arrow_and_digit_events(self):
        from picoterm.evdev import EV_KEY, KEY_5, KEY_DOWN, parse_input_event
        from picoterm.keys import Key

        down = struct.pack("<llHHi", 0, 0, EV_KEY, KEY_DOWN, 1)
        five = struct.pack("<llHHi", 0, 0, EV_KEY, KEY_5, 1)

        self.assertEqual(parse_input_event(down).name, Key.DOWN)
        digit = parse_input_event(five)
        self.assertEqual(digit.name, Key.DIGIT)
        self.assertEqual(digit.value, 5)

    def test_ignores_key_release_events(self):
        from picoterm.evdev import EV_KEY, KEY_ENTER, parse_input_event

        release = struct.pack("<llHHi", 0, 0, EV_KEY, KEY_ENTER, 0)

        self.assertIsNone(parse_input_event(release))

    def test_decodes_64_bit_input_event_tail(self):
        from picoterm.evdev import EV_KEY, KEY_RIGHT, parse_input_event
        from picoterm.keys import Key

        event = struct.pack("<qqHHi", 0, 0, EV_KEY, KEY_RIGHT, 1)

        self.assertEqual(parse_input_event(event).name, Key.RIGHT)

    def test_decodes_bubble_control_keys(self):
        from picoterm.evdev import EV_KEY, KEY_EQUAL, KEY_MINUS, KEY_SPACE, parse_input_event
        from picoterm.keys import Key

        minus = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_MINUS, 1))
        equal = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_EQUAL, 1))
        space = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_SPACE, 1))

        self.assertEqual((minus.name, minus.value), (Key.CHAR, "-"))
        self.assertEqual((equal.name, equal.value), (Key.CHAR, "="))
        self.assertEqual((space.name, space.value), (Key.CHAR, " "))


if __name__ == "__main__":
    unittest.main()
