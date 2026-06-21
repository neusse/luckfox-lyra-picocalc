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

    def test_breakout_command_dispatches_to_synced_breakout_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["breakout", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_breakout.py")
        self.assertEqual(spec.args, ["--once"])

    def test_picocalc_breakout_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-breakout", [])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_breakout.py")
        self.assertEqual(spec.args, [])

    def test_chess_command_dispatches_to_native_chess_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["chess"])

        self.assertEqual(spec.script, "/usr/libexec/picocalc/chess")
        self.assertEqual(spec.args, [])
        self.assertTrue(spec.native)

    def test_alpine_command_dispatches_to_native_mail_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["alpine"])

        self.assertEqual(spec.script, "/usr/bin/alpine")
        self.assertEqual(spec.args, [])
        self.assertTrue(spec.native)

    def test_email_basename_is_an_alias_for_alpine(self):
        module = self.load_module()

        spec = module.resolve_invocation("email", [])

        self.assertEqual(spec.script, "/usr/bin/alpine")
        self.assertEqual(spec.args, [])
        self.assertTrue(spec.native)

    def test_doom_command_dispatches_to_native_puredoom_wrapper(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["doom"])

        self.assertEqual(spec.script, "/usr/bin/puredoom")
        self.assertEqual(spec.args, [])
        self.assertTrue(spec.native)

    def test_puredoom_basename_is_an_alias_for_doom(self):
        module = self.load_module()

        spec = module.resolve_invocation("puredoom", ["-iwad", "doom1.wad"])

        self.assertEqual(spec.script, "/usr/bin/puredoom")
        self.assertEqual(spec.args, ["-iwad", "doom1.wad"])
        self.assertTrue(spec.native)

    def test_chess_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-chess", ["--fen", "startpos"])

        self.assertEqual(spec.script, "/usr/libexec/picocalc/chess")
        self.assertEqual(spec.args, ["--fen", "startpos"])
        self.assertTrue(spec.native)

    def test_launcher_command_dispatches_to_synced_launcher_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["launcher", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_launcher.py")
        self.assertEqual(spec.args, ["--once"])

    def test_clock_command_dispatches_to_synced_clock_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["clock", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_fancy_clock.py")
        self.assertEqual(spec.args, ["--once"])

    def test_calculator_command_dispatches_to_synced_calculator_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["calculator", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_calculator.py")
        self.assertEqual(spec.args, ["--once"])

    def test_picocalc_calculator_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-calculator", ["--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_calculator.py")
        self.assertEqual(spec.args, ["--once"])

    def test_minesweeper_command_dispatches_to_synced_minesweeper_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["minesweeper", "--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_minesweeper.py")
        self.assertEqual(spec.args, ["--once"])

    def test_picocalc_minesweeper_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-minesweeper", ["--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_minesweeper.py")
        self.assertEqual(spec.args, ["--once"])

    def test_launcher_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-launcher", ["--once"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_launcher.py")
        self.assertEqual(spec.args, ["--once"])

    def test_native_chess_runner_executes_binary_directly(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["chess", "--help"])

        runner = module.runner_for_spec(spec)

        self.assertEqual(runner, ["/usr/libexec/picocalc/chess", "--help"])

    def test_zork_command_dispatches_to_synced_zork_app(self):
        module = self.load_module()

        spec = module.resolve_invocation("picocalc-app", ["zork", "--list"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_zork.py")
        self.assertEqual(spec.args, ["--list"])

    def test_zork_basename_is_an_alias(self):
        module = self.load_module()

        spec = module.resolve_invocation("picozork", ["zork1"])

        self.assertEqual(spec.script, "/home/neusse/luckfox-dev/picocalc_zork.py")
        self.assertEqual(spec.args, ["zork1"])

    def test_interactive_zork_from_remote_shell_runs_inline(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["zork"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertFalse(should_detach)

    def test_interactive_bubble_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["bubble"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_interactive_breakout_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["breakout"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_interactive_weather_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["weather"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_interactive_clock_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["clock"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_interactive_calculator_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["calculator"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_interactive_minesweeper_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["minesweeper"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_interactive_chess_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["chess"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_interactive_launcher_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["launcher"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_launcher_list_from_remote_shell_runs_inline(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["launcher", "--list"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertFalse(should_detach)

    def test_chess_help_from_remote_shell_runs_inline(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["chess", "--help"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertFalse(should_detach)

    def test_interactive_chess_from_physical_console_still_detaches(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["chess"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/tty1")

        self.assertTrue(should_detach)

    def test_chess_help_from_physical_console_runs_inline(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["chess", "--help"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/tty1")

        self.assertFalse(should_detach)

    def test_interactive_sudoku_from_remote_shell_detaches_to_physical_console(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["sudoku", "--new", "medium"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertTrue(should_detach)

    def test_one_shot_bubble_from_remote_shell_runs_inline(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["bubble", "--once"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/pts/0")

        self.assertFalse(should_detach)

    def test_interactive_bubble_from_physical_console_runs_inline(self):
        module = self.load_module()
        spec = module.resolve_invocation("picocalc-app", ["bubble"])

        should_detach = module.should_detach_to_console(spec, ttyname=lambda fd: "/dev/tty1")

        self.assertFalse(should_detach)

    def test_console_launch_message_tells_user_where_app_started(self):
        module = self.load_module()
        spec = module.AppSpec("bubble", "/home/neusse/luckfox-dev/picocalc_bubble.py", [])

        message = module.console_launch_message(spec, pid=1425)

        self.assertIn("bubble started on /dev/tty1", message)
        self.assertIn("PID 1425", message)
        self.assertIn("/tmp/picocalc-app-bubble.log", message)

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

    def test_running_native_app_message_does_not_suggest_one_shot_render(self):
        module = self.load_module()
        spec = module.AppSpec("chess", "/usr/libexec/picocalc/chess", [], native=True)

        message = module.running_app_message(spec, [(2162, "/usr/libexec/picocalc/chess")])

        self.assertIn("chess is already running", message)
        self.assertIn("kill 2162", message)
        self.assertNotIn("--once", message)

    def test_detects_any_running_framebuffer_app(self):
        module = self.load_module()
        proc = ROOT / "tests" / "proc-framebuffer.tmp"
        cmdline = proc / "2944" / "cmdline"
        cmdline.parent.mkdir(parents=True, exist_ok=True)
        cmdline.write_bytes(
            b"/home/neusse/venvs/nonroot/bin/python\0"
            b"/home/neusse/luckfox-dev/picocalc_fancy_clock.py\0"
        )
        try:
            running = module.running_framebuffer_processes(proc_root=proc)
        finally:
            cmdline.unlink()
            cmdline.parent.rmdir()
            proc.rmdir()

        self.assertEqual(
            running,
            [("clock", 2944, "/home/neusse/venvs/nonroot/bin/python /home/neusse/luckfox-dev/picocalc_fancy_clock.py")],
        )

    def test_framebuffer_busy_message_names_conflicting_app(self):
        module = self.load_module()
        spec = module.AppSpec("calculator", "/home/neusse/luckfox-dev/picocalc_calculator.py", [])

        message = module.framebuffer_busy_message(
            spec,
            [("clock", 2944, "python /home/neusse/luckfox-dev/picocalc_fancy_clock.py")],
        )

        self.assertIn("Cannot start calculator", message)
        self.assertIn("clock is already using", message)
        self.assertIn("kill 2944", message)


if __name__ == "__main__":
    unittest.main()
