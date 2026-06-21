import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "python" / "picocalc_calculator.py"
sys.path.insert(0, str(ROOT / "python"))


class PicoCalcCalculatorTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_calculator", APP)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_render_draws_ios_style_buttons(self):
        module = self.load_module()
        from picofb import Canvas
        from picogames.calculator import CalculatorState

        module.FONT_UI = "DejaVuSans.ttf"
        canvas = Canvas(320, 320, module.BG)

        module.render_calculator(canvas, CalculatorState())

        self.assertEqual(canvas.pixel(0, 0), module.BG)
        self.assertNotEqual(canvas.pixel(module.GRID_X + 10, module.GRID_Y + 10), module.BG)

    def test_ctrl_f5_quits_calculator(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.F5, ctrl=True)), "quit")

    def test_button_labels_use_truetype_text(self):
        module = self.load_module()

        class FakeCanvas:
            width = 320
            height = 320

            def __init__(self):
                self.ttf_calls = []
                self.bitmap_calls = []

            def hline(self, *args):
                pass

            def vline(self, *args):
                pass

            def line(self, *args):
                pass

            def text(self, *args, **kwargs):
                self.bitmap_calls.append((args, kwargs))

            def text_ttf(self, value, x, y, color, *, font, size, background=None):
                self.ttf_calls.append((value, x, y, color, font, size, background))

        for label in ("8", "+", "=", "+/-"):
            canvas = FakeCanvas()
            module.FONT_UI = "DejaVuSansMono.ttf"
            module.render_button(canvas, label, 20, 20, 40, 40, module.BTN_DARK, module.TEXT_LIGHT)
            self.assertIn(label, [call[0] for call in canvas.ttf_calls])
            self.assertEqual(canvas.bitmap_calls, [])

    def test_calculator_uses_fixed_width_font(self):
        module = self.load_module()

        self.assertIn("Mono", module.FONT_UI)


if __name__ == "__main__":
    unittest.main()
