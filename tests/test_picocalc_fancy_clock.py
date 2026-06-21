import importlib.util
import sys
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "python" / "picocalc_fancy_clock.py"
sys.path.insert(0, str(ROOT / "python"))


class PicoCalcFancyClockTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_fancy_clock", APP)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_polar_to_xy_places_noon_above_center(self):
        module = self.load_module()

        x, y = module.polar_to_xy(160, 160, 0, 50)

        self.assertAlmostEqual(x, 160)
        self.assertAlmostEqual(y, 110)

    def test_moon_phase_fraction_is_normalized(self):
        module = self.load_module()
        tt = time.struct_time((2026, 6, 21, 12, 0, 0, 6, 172, -1))

        phase = module.moon_phase_fraction(tt)

        self.assertGreaterEqual(phase, 0.0)
        self.assertLess(phase, 1.0)

    def test_ctrl_f5_quits_clock(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.F5, ctrl=True)), "quit")

    def test_render_once_draws_watch_face(self):
        module = self.load_module()
        from picofb import Canvas

        canvas = Canvas(320, 320, module.BG)
        tt = time.struct_time((2026, 6, 21, 10, 9, 30, 6, 172, -1))

        module.render_clock(canvas, tt, chimes_enabled=False)

        lit = sum(
            1
            for y in range(canvas.height)
            for x in range(canvas.width)
            if canvas.pixel(x, y) != module.BG
        )
        self.assertGreater(lit, 10000)
        self.assertNotEqual(canvas.pixel(160, 160), module.BG)


if __name__ == "__main__":
    unittest.main()
