import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches" / "picocalc-keyboard-mcu-sysfs.patch"


class PicoCalcKeyboardPatchTest(unittest.TestCase):
    def test_patch_exposes_battery_and_backlight_controls(self):
        text = PATCH.read_text(encoding="utf-8")

        for expected in (
            "REG_ID_BAT",
            "battery_percent",
            "battery_raw",
            "battery_status",
            "keyboard_backlight",
            "screen_backlight",
            "PICOCALC_WRITE_MASK",
            "mutex_lock",
            "sysfs_create_group",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
