import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MCU = ROOT / "scripts" / "device" / "picocalc-mcu"
SHUTDOWN = ROOT / "scripts" / "device" / "shutdown"


class PicoCalcShutdownScriptsTest(unittest.TestCase):
    def test_mcu_helper_exposes_poweroff_command(self):
        text = MCU.read_text(encoding="utf-8")

        self.assertIn("poweroff N", text)
        self.assertIn("next halt/poweroff", text)
        self.assertIn("write_delay poweroff_delay", text)
        self.assertIn("[ \"$value\" -gt 63 ]", text)

    def test_shutdown_script_is_real_poweroff_wrapper(self):
        text = SHUTDOWN.read_text(encoding="utf-8")

        self.assertIn("Usage: shutdown [delay-seconds]", text)
        self.assertIn("must run as root", text)
        self.assertIn("picocalc-mcu", text)
        self.assertIn("poweroff \"$delay\"", text)
        self.assertIn("exec \"$POWEROFF\"", text)
        self.assertIn("use poweroff for Linux-only halt", text)


if __name__ == "__main__":
    unittest.main()
