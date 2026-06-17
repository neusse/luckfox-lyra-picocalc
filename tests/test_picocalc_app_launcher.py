import importlib.machinery
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "device" / "picocalc-app"


class PicoCalcAppLauncherTests(unittest.TestCase):
    def load_module(self):
        loader = importlib.machinery.SourceFileLoader("picocalc_app_launcher", str(LAUNCHER))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        loader.exec_module(module)
        return module

    def test_weather_command_dispatches_to_synced_weather_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["weather", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_weather.py")
        self.assertEqual(spec.args, ["--once"])

    def test_weather_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("weather", ["--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_weather.py")
        self.assertEqual(spec.args, ["--once"])

    def test_sudoku_command_dispatches_to_synced_sudoku_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["sudoku", "--demo", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_sudoku.py")
        self.assertEqual(spec.args, ["--demo", "--once"])

    def test_bubble_command_dispatches_to_synced_bubble_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["bubble", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_bubble.py")
        self.assertEqual(spec.args, ["--once"])

    def test_sudoku_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-sudoku", ["--demo", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_sudoku.py")
        self.assertEqual(spec.args, ["--demo", "--once"])

    def test_environment_adds_project_python_and_nonroot_venv(self):
        module = self.load_module()
        env = {"PATH": "/usr/bin", "PYTHONPATH": "/tmp/extra"}

        updated = module.build_environment(env)

        self.assertEqual(updated["PYTHONPATH"], "/home/neusse/luckfox-dev/python:/tmp/extra")
        self.assertTrue(updated["PATH"].startswith("/home/neusse/venvs/nonroot/bin:"))
        self.assertEqual(updated["VIRTUAL_ENV"], "/home/neusse/venvs/nonroot")

    def test_uses_venv_python_when_present(self):
        module = self.load_module()

        runner = module.runner_for("/home/neusse/luckfox-dev/picocalc_weather.py", ["--once"], exists=lambda path: True)

        self.assertEqual(runner[:2], ["/home/neusse/venvs/nonroot/bin/python", "/home/neusse/luckfox-dev/picocalc_weather.py"])
        self.assertEqual(runner[2:], ["--once"])

    def test_detects_running_app_process_from_proc_cmdline(self):
        module = self.load_module()
        proc = ROOT / "tests" / "proc.tmp"
        cmdline = proc / "3268" / "cmdline"
        cmdline.parent.mkdir(parents=True, exist_ok=True)
        cmdline.write_bytes(
            b"/home/neusse/venvs/nonroot/bin/python\0"
            b"/home/neusse/luckfox-dev/picocalc_weather.py\0"
        )
        try:
            running = module.running_processes_for(
                "/home/neusse/luckfox-dev/picocalc_weather.py",
                proc_root=proc,
                current_pid=9999,
            )
        finally:
            cmdline.unlink()
            cmdline.parent.rmdir()
            proc.rmdir()

        self.assertEqual(running, [(3268, "/home/neusse/venvs/nonroot/bin/python /home/neusse/luckfox-dev/picocalc_weather.py")])

    def test_running_app_message_tells_user_what_happened(self):
        module = self.load_module()
        spec = module.AppSpec("weather", "/home/neusse/luckfox-dev/picocalc_weather.py", [])

        message = module.running_app_message(spec, [(3268, "python /home/neusse/luckfox-dev/picocalc_weather.py")])

        self.assertIn("weather is already running", message)
        self.assertIn("PID 3268", message)
        self.assertIn("kill 3268", message)


if __name__ == "__main__":
    unittest.main()
