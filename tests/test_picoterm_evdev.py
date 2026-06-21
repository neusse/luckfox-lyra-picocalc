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

    def test_decodes_function_keys_f1_through_f10(self):
        from picoterm.evdev import EV_KEY, KEY_F1, KEY_F10, KEY_F5, parse_input_event
        from picoterm.keys import Key

        f1 = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_F1, 1))
        f5 = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_F5, 1))
        f10 = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_F10, 1))

        self.assertEqual(f1.name, Key.F1)
        self.assertEqual(f5.name, Key.F5)
        self.assertEqual(f10.name, Key.F10)

    def test_ctrl_f5_is_standard_app_exit_key(self):
        from picoterm.appkeys import is_app_exit_key
        from picoterm.evdev import EV_KEY, KEY_F5, parse_input_event

        f5 = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_F5, 1), ctrl=True)

        self.assertTrue(is_app_exit_key(f5))

    def test_decodes_calculator_keys_and_shifted_operators(self):
        from picoterm.evdev import EV_KEY, KEY_5, KEY_8, KEY_C, KEY_DOT, KEY_EQUAL, KEY_P, KEY_SLASH, KEY_X, parse_input_event
        from picoterm.keys import Key

        dot = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_DOT, 1))
        slash = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_SLASH, 1))
        x_key = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_X, 1))
        c_key = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_C, 1))
        p_key = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_P, 1))
        plus = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_EQUAL, 1), shift=True)
        star = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_8, 1), shift=True)
        percent = parse_input_event(struct.pack("<llHHi", 0, 0, EV_KEY, KEY_5, 1), shift=True)

        self.assertEqual((dot.name, dot.value), (Key.CHAR, "."))
        self.assertEqual((slash.name, slash.value), (Key.CHAR, "/"))
        self.assertEqual((x_key.name, x_key.value), (Key.CHAR, "x"))
        self.assertEqual((c_key.name, c_key.value), (Key.CHAR, "c"))
        self.assertEqual((p_key.name, p_key.value), (Key.CHAR, "p"))
        self.assertEqual((plus.name, plus.value), (Key.CHAR, "+"))
        self.assertEqual((star.name, star.value), (Key.CHAR, "*"))
        self.assertEqual((percent.name, percent.value), (Key.CHAR, "%"))


if __name__ == "__main__":
    unittest.main()
