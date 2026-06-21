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
            "REG_ID_OFF",
            "poweroff_delay",
            "screen_backlight",
            "PICOCALC_WRITE_MASK",
            "mutex_lock",
            "sysfs_create_group",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_patch_sends_poweroff_from_kernel_shutdown_path(self):
        text = PATCH.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        for expected in (
            "#include <linux/reboot.h>",
            "poweroff_delay",
            "pckb->poweroff_delay = delay;",
            "static void pckb_shutdown(struct i2c_client *client)",
            "system_state == SYSTEM_RESTART",
            "pckb_write_u8(pckb, REG_ID_OFF, pckb->poweroff_delay)",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

        self.assertIn(".shutdown = pckb_shutdown", normalized)


if __name__ == "__main__":
    unittest.main()
