import importlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from picofb import (
    BLACK,
    BLUE,
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    WHITE,
    YELLOW,
    Canvas,
    Display,
    color565,
)
from picofb.canvas import Canvas as CanvasClass


class Color565Tests(unittest.TestCase):
    def test_primary_colors(self):
        self.assertEqual(color565(0, 0, 0), 0x0000)
        self.assertEqual(color565(255, 255, 255), 0xFFFF)
        self.assertEqual(color565(255, 0, 0), 0xF800)
        self.assertEqual(color565(0, 255, 0), 0x07E0)
        self.assertEqual(color565(0, 0, 255), 0x001F)

    def test_exported_constants(self):
        self.assertEqual(BLACK, 0x0000)
        self.assertEqual(WHITE, 0xFFFF)
        self.assertEqual(RED, 0xF800)
        self.assertEqual(GREEN, 0x07E0)
        self.assertEqual(BLUE, 0x001F)
        self.assertEqual(CYAN, 0x07FF)
        self.assertEqual(MAGENTA, 0xF81F)
        self.assertEqual(YELLOW, 0xFFE0)

    def test_canvas_and_display_are_exported(self):
        self.assertIs(Canvas, CanvasClass)
        self.assertIsNotNone(Display)
        self.assertEqual(Display.__name__, "Display")

    def test_canvas_import_errors_are_not_hidden_when_module_exists(self):
        source_package = Path(__file__).resolve().parents[1] / "python" / "picofb"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_package = Path(temp_dir) / "picofb"
            shutil.copytree(source_package, temp_package)
            (temp_package / "canvas.py").write_text(
                "raise ImportError('canvas dependency failed')\n",
                encoding="utf-8",
            )

            saved_modules = {
                name: sys.modules.pop(name)
                for name in list(sys.modules)
                if name == "picofb" or name.startswith("picofb.")
            }
            sys.path.insert(0, temp_dir)

            try:
                with self.assertRaisesRegex(ImportError, "canvas dependency failed"):
                    importlib.import_module("picofb")
            finally:
                sys.path.remove(temp_dir)
                for name in list(sys.modules):
                    if name == "picofb" or name.startswith("picofb."):
                        sys.modules.pop(name)
                sys.modules.update(saved_modules)

    def test_rejects_non_integer_components(self):
        with self.assertRaises(TypeError):
            color565("255", 0, 0)

    def test_rejects_out_of_range_components(self):
        with self.assertRaises(ValueError):
            color565(-1, 0, 0)
        with self.assertRaises(ValueError):
            color565(0, 256, 0)


if __name__ == "__main__":
    unittest.main()
