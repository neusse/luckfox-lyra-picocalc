import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))


class CalculatorModelTests(unittest.TestCase):
    def test_adds_two_numbers(self):
        from picogames.calculator import CalculatorState

        calc = CalculatorState()
        for key in "12+7=":
            calc.press(key)

        self.assertEqual(calc.display, "19")

    def test_repeated_equals_reuses_last_operator(self):
        from picogames.calculator import CalculatorState

        calc = CalculatorState()
        for key in "5+2==":
            calc.press(key)

        self.assertEqual(calc.display, "9")

    def test_percent_and_sign_match_original_behavior(self):
        from picogames.calculator import CalculatorState

        calc = CalculatorState()
        for key in "50p":
            calc.press(key)
        self.assertEqual(calc.display, "0.5")

        calc.press("s")
        self.assertEqual(calc.display, "-0.5")

    def test_clear_first_clears_entry_then_all_clear_resets_expression(self):
        from picogames.calculator import CalculatorState

        calc = CalculatorState()
        for key in "12+3":
            calc.press(key)
        calc.press("c")
        self.assertEqual(calc.display, "0")
        self.assertEqual(calc.expression, "12 +")

        calc.press("c")
        self.assertEqual(calc.display, "0")
        self.assertEqual(calc.expression, "")

    def test_divide_by_zero_formats_error(self):
        from picogames.calculator import CalculatorState

        calc = CalculatorState()
        for key in "8/0=":
            calc.press(key)

        self.assertEqual(calc.display, "Error")


if __name__ == "__main__":
    unittest.main()
