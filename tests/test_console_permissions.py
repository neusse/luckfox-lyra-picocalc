import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PERMISSIONS_SCRIPT = ROOT / "scripts" / "device" / "S56console_permissions"


class ConsolePermissionsTests(unittest.TestCase):
    def test_physical_console_is_read_write_for_tty_group(self):
        script = PERMISSIONS_SCRIPT.read_text()

        self.assertNotIn('chmod 0620 "$dev"', script)
        self.assertIn('chmod 0660 "$dev"', script)


if __name__ == "__main__":
    unittest.main()
