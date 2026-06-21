import importlib.machinery
import importlib.util
import io
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "device" / "picocpu"


class PicoCpuTests(unittest.TestCase):
    def load_module(self):
        loader = importlib.machinery.SourceFileLoader("picocpu", str(SCRIPT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        loader.exec_module(module)
        return module

    def make_policy(self, root):
        policy = root / "devices" / "system" / "cpu" / "cpufreq" / "policy0"
        policy.mkdir(parents=True)
        values = {
            "scaling_governor": "ondemand\n",
            "scaling_available_governors": "ondemand userspace performance\n",
            "scaling_cur_freq": "1416000\n",
            "scaling_min_freq": "600000\n",
            "scaling_max_freq": "1512000\n",
            "scaling_available_frequencies": "600000 800000 1008000 1200000 1296000 1416000 1512000\n",
            "scaling_setspeed": "1416000\n",
        }
        for name, value in values.items():
            (policy / name).write_text(value, encoding="utf-8")
        return policy

    def run_picocpu(self, args, sysfs_root):
        module = self.load_module()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = module.main(args, sysfs_root=sysfs_root, require_root=False)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_status_reports_governor_and_frequency_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_policy(pathlib.Path(tmp))

            code, out, err = self.run_picocpu(["status"], pathlib.Path(tmp))

        self.assertEqual(code, 0, err)
        self.assertIn("governor: ondemand", out)
        self.assertIn("current: 1416 MHz", out)
        self.assertIn("range: 600-1512 MHz", out)
        self.assertIn("available: 600 800 1008 1200 1296 1416 1512 MHz", out)

    def test_performance_and_ondemand_write_governor(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = self.make_policy(pathlib.Path(tmp))

            self.assertEqual(self.run_picocpu(["performance"], pathlib.Path(tmp))[0], 0)
            self.assertEqual((policy / "scaling_governor").read_text(encoding="utf-8"), "performance\n")

            self.assertEqual(self.run_picocpu(["ondemand"], pathlib.Path(tmp))[0], 0)
            self.assertEqual((policy / "scaling_governor").read_text(encoding="utf-8"), "ondemand\n")

    def test_set_writes_userspace_and_requested_frequency(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = self.make_policy(pathlib.Path(tmp))

            code, out, err = self.run_picocpu(["set", "800"], pathlib.Path(tmp))

            self.assertEqual(code, 0, err)
            self.assertIn("fixed frequency: 800 MHz", out)
            self.assertEqual((policy / "scaling_governor").read_text(encoding="utf-8"), "userspace\n")
            self.assertEqual((policy / "scaling_setspeed").read_text(encoding="utf-8"), "800000\n")

    def test_set_rejects_unavailable_frequency(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_policy(pathlib.Path(tmp))

            code, out, err = self.run_picocpu(["set", "999"], pathlib.Path(tmp))

        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("not an available frequency", err)


if __name__ == "__main__":
    unittest.main()
