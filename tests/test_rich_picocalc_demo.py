import importlib.util
from io import BytesIO, StringIO
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "python" / "rich_picocalc_demo.py"


class RichPicoCalcDemoTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("rich_picocalc_demo", DEMO)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_demo_renders_inside_picocalc_console_width(self):
        module = self.load_module()

        output = module.render_demo(width=40)
        lines = output.rstrip().splitlines()

        self.assertGreaterEqual(len(lines), 28)
        self.assertLessEqual(len(lines), 34)
        self.assertTrue(lines)
        for line in lines:
            self.assertLessEqual(len(line), 40)

        self.assertIn("Luckfox Lyra", output)
        self.assertIn("PicoCalc", output)
        self.assertIn("Rich", output)

    def test_default_demo_fits_picocalc_tty(self):
        module = self.load_module()

        output = module.render_demo()
        lines = output.rstrip().splitlines()

        self.assertEqual(module.PICO_WIDTH, 50)
        self.assertGreaterEqual(len(lines), 28)
        self.assertLessEqual(len(lines), 32)
        for line in lines:
            self.assertLessEqual(len(line), module.PICO_WIDTH)

    def test_demo_shows_flashy_rich_features(self):
        module = self.load_module()

        output = module.render_demo()

        self.assertIn("Color", output)
        self.assertIn("Style", output)
        self.assertIn("Markdown", output)
        self.assertIn("Progress", output)
        self.assertIn("Log", output)
        self.assertIn("Table", output)
        self.assertIn("Columns", output)

    def test_demo_can_emit_crlf_for_direct_tty_writes(self):
        module = self.load_module()
        output = StringIO()

        module.write_demo(output, width=40, clear=False, crlf=True)

        self.assertIn("\r\n", output.getvalue())
        self.assertNotIn("\n+", output.getvalue())

    def test_demo_can_write_to_binary_tty_stream(self):
        module = self.load_module()
        output = BytesIO()

        module.write_demo_bytes(output, width=40, clear=False)

        self.assertIn(b"\r\n", output.getvalue())


if __name__ == "__main__":
    unittest.main()
