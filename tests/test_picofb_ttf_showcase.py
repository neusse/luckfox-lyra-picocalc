import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "python" / "fb_ttf_showcase.py"


class FakeDisplay:
    width = 320
    height = 320

    def __init__(self):
        self.ttf_calls = []
        self.shown = False

    def fill(self, color):
        return self

    def fill_rect(self, *args):
        return self

    def rect(self, *args):
        return self

    def line(self, *args):
        return self

    def text_ttf(self, value, x, y, color, *, font, size, background=None):
        self.ttf_calls.append(
            {
                "value": value,
                "font": font,
                "size": size,
                "background": background,
            }
        )
        return self

    def show(self):
        self.shown = True
        return self


class TrueTypeShowcaseTests(unittest.TestCase):
    def test_showcase_uses_multiple_truetype_fonts(self):
        spec = importlib.util.spec_from_file_location("fb_ttf_showcase", DEMO)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        display = FakeDisplay()
        module.draw_demo(display)

        fonts = {call["font"] for call in display.ttf_calls}
        self.assertGreaterEqual(len(display.ttf_calls), 5)
        self.assertGreaterEqual(len(fonts), 4)
        self.assertIn("Decker", fonts)
        self.assertIn("Notepad", fonts)
        self.assertTrue(display.shown)


if __name__ == "__main__":
    unittest.main()
