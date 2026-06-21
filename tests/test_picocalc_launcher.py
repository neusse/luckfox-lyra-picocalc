import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "examples" / "python" / "picocalc_launcher.py"
LEGACY_DATA = ROOT / "python" / "circuitpython_apps" / "launcher_legacy" / "launcher_data.json"


class PicoCalcLauncherTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_launcher", LAUNCHER)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_legacy_json_maps_ported_apps_to_picocalc_app_commands(self):
        module = self.load_module()

        entries = module.load_launcher_entries(LEGACY_DATA)
        by_name = {entry.name: entry for entry in entries}

        self.assertEqual(len(entries), 22)
        self.assertEqual(by_name["weather"].command, ["picocalc-app", "weather"])
        self.assertEqual(by_name["breakout"].command, ["picocalc-app", "breakout"])
        self.assertEqual(by_name["minesweeper"].command, ["picocalc-app", "minesweeper"])
        self.assertEqual(by_name["clock"].command, ["picocalc-app", "clock"])
        self.assertEqual(by_name["sudoku"].command, ["picocalc-app", "sudoku"])
        self.assertEqual(by_name["bubble graphic"].command, ["picocalc-app", "bubble"])
        self.assertEqual(by_name["calculator"].command, ["picocalc-app", "calculator"])
        self.assertEqual(by_name["zork"].command, ["picocalc-app", "zork"])

    def test_icon_paths_are_resolved_relative_to_config_directory(self):
        module = self.load_module()

        entries = module.load_launcher_entries(LEGACY_DATA)
        weather = next(entry for entry in entries if entry.name == "weather")

        self.assertEqual(
            weather.icon_path,
            LEGACY_DATA.parent / "bmp" / "weather.bmp",
        )

    def test_missing_icon_uses_placeholder_metadata(self):
        module = self.load_module()
        temp_dir = ROOT / "tests" / "launcher-config.tmp"
        temp_dir.mkdir(exist_ok=True)
        config = temp_dir / "launcher_data.json"
        config.write_text(
            json.dumps(
                {
                    "icons": [
                        {
                            "name": "missing icon",
                            "app": "/picocalc_weather.py",
                            "bmp": "/bmp/nope.bmp",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        try:
            entries = module.load_launcher_entries(config)
        finally:
            config.unlink()
            temp_dir.rmdir()

        self.assertIsNone(entries[0].icon_path)
        self.assertEqual(entries[0].placeholder, "M")

    def test_explicit_launcher_command_overrides_legacy_app_mapping(self):
        module = self.load_module()
        temp_dir = ROOT / "tests" / "launcher-command.tmp"
        temp_dir.mkdir(exist_ok=True)
        config = temp_dir / "launcher_data.json"
        config.write_text(
            json.dumps(
                {
                    "icons": [
                        {
                            "name": "email",
                            "app": "/picocalc_email.py",
                            "bmp": "/bmp/email.bmp",
                            "command": ["picocalc-app", "alpine"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        try:
            entries = module.load_launcher_entries(config)
        finally:
            config.unlink()
            temp_dir.rmdir()

        self.assertEqual(entries[0].command, ["picocalc-app", "alpine"])
        self.assertTrue(entries[0].ported)

    def test_grid_geometry_matches_320_square_display(self):
        module = self.load_module()

        geometry = module.compute_grid_geometry(320, 320)

        self.assertEqual(geometry.columns, 4)
        self.assertEqual(geometry.rows, 3)
        self.assertEqual(geometry.per_page, 12)

    def test_move_selection_obeys_edges_and_columns(self):
        module = self.load_module()
        geometry = module.compute_grid_geometry(320, 320)

        self.assertEqual(module.move_selection(0, "left", 22, geometry), 0)
        self.assertEqual(module.move_selection(0, "right", 22, geometry), 1)
        self.assertEqual(module.move_selection(0, "down", 22, geometry), 4)
        self.assertEqual(module.move_selection(4, "up", 22, geometry), 0)
        self.assertEqual(module.move_selection(21, "right", 22, geometry), 21)

    def test_ctrl_f5_quits_launcher(self):
        module = self.load_module()
        from picoterm.keys import Key, KeyPress

        self.assertEqual(module.key_to_action(KeyPress(Key.F5, ctrl=True)), "quit")

    def test_launcher_session_returns_to_menu_after_child_exits(self):
        module = self.load_module()
        calls = {"interactive": 0, "runner": []}

        def interactive():
            calls["interactive"] += 1
            if calls["interactive"] == 1:
                return ["picocalc-app", "weather"]
            return None

        def runner(command):
            calls["runner"].append(command)
            return 0

        result = module.run_launcher_session(interactive, runner)

        self.assertEqual(result, 0)
        self.assertEqual(calls["runner"], [["picocalc-app", "weather"]])
        self.assertEqual(calls["interactive"], 2)


if __name__ == "__main__":
    unittest.main()
