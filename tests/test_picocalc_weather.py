import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "python" / "picocalc_weather.py"


class PicoCalcWeatherTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("picocalc_weather", DEMO)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_formats_weather_values_for_display(self):
        module = self.load_module()

        self.assertEqual(module.fmt_temp(52.6), "53F")
        self.assertEqual(module.fmt_temp(-2.2), "-2F")
        self.assertEqual(module.wind_dir_16pt(271), "W")
        self.assertEqual(module.fmt_pressure(1013), "29.91")
        self.assertEqual(module.fmt_wind_tile(2.4, 91), "2 E")

    def test_aggregates_forecast_by_local_day(self):
        module = self.load_module()
        forecast = {
            "city": {"timezone": 0},
            "list": [
                {
                    "dt": 1_700_000_000,
                    "main": {"temp_min": 42, "temp_max": 50},
                    "pop": 0.1,
                    "weather": [{"icon": "01d", "description": "clear sky"}],
                },
                {
                    "dt": 1_700_003_600,
                    "main": {"temp_min": 39, "temp_max": 56},
                    "pop": 0.7,
                    "weather": [{"icon": "10d", "description": "light rain"}],
                },
            ],
        }

        days = module.aggregate_forecast_daily(forecast, days=1)

        self.assertEqual(len(days), 1)
        self.assertEqual(days[0]["tmin"], 39)
        self.assertEqual(days[0]["tmax"], 56)
        self.assertEqual(days[0]["pop"], 0.7)
        self.assertEqual(days[0]["icon"], "10d")

    def test_builds_openweather_urls_without_printing_key(self):
        module = self.load_module()
        settings = module.Settings(key="secret", lat=47.51, lon=-122.51, units="imperial")

        current = module.current_url(settings)
        forecast = module.forecast_url(settings)

        self.assertIn("appid=secret", current)
        self.assertIn("lat=47.51", current)
        self.assertIn("forecast", forecast)

    def test_reads_battery_percent_from_sysfs(self):
        module = self.load_module()
        path = ROOT / "tests" / "battery_percent.tmp"
        path.write_text("87\n", encoding="ascii")
        try:
            self.assertEqual(module.read_battery_percent(path), 87)
        finally:
            path.unlink()

    def test_muted_text_is_bright_enough_for_picocalc(self):
        module = self.load_module()
        self.assertGreaterEqual(module.MUTED_RGB[0], 180)
        self.assertGreaterEqual(module.MUTED_RGB[1], 190)
        self.assertGreaterEqual(module.MUTED_RGB[2], 200)

    def test_forecast_pop_label_is_reader_friendly(self):
        module = self.load_module()

        self.assertEqual(module.fmt_pop(0), "POP 0%")
        self.assertEqual(module.fmt_pop(0.42), "POP 42%")

    def test_tile_values_use_truetype_for_readability(self):
        module = self.load_module()

        class FakeDisplay:
            def __init__(self):
                self.ttf_calls = []
                self.bitmap_calls = []

            def text_ttf(self, value, x, y, color, *, font, size, background=None):
                self.ttf_calls.append({"value": value, "size": size})

            def text(self, value, x, y, color, background=None, scale=1):
                self.bitmap_calls.append({"value": value, "scale": scale})

        display = FakeDisplay()

        module.draw_tile_value(display, "2MPH E", 0, 0, 72)

        self.assertEqual(display.ttf_calls[0]["value"], "2MPH E")
        self.assertGreaterEqual(display.ttf_calls[0]["size"], 20)
        self.assertEqual(display.bitmap_calls, [])

    def test_dashboard_draws_clock_and_date_beside_temperature(self):
        module = self.load_module()

        class FakeDisplay:
            width = 320
            height = 320

            def __init__(self):
                self.ttf_calls = []

            def fill(self, color):
                pass

            def fill_rect(self, x, y, w, h, color):
                pass

            def rect(self, x, y, w, h, color):
                pass

            def text_ttf(self, value, x, y, color, *, font, size, background=None):
                self.ttf_calls.append({"value": value, "x": x, "y": y, "size": size})

            def text(self, value, x, y, color, background=None, scale=1):
                pass

            def show(self):
                pass

        current = {
            "name": "PicoTown",
            "main": {"temp": 66, "feels_like": 65, "humidity": 57, "pressure": 1017},
            "wind": {"speed": 2.4, "deg": 91},
            "weather": [{"icon": "01d", "description": "clear sky"}],
        }
        forecast = {"list": []}
        now = module.datetime(2026, 6, 16, 10, 24)
        display = FakeDisplay()
        original_draw_icon = module.draw_icon

        try:
            module.draw_icon = lambda *args, **kwargs: None
            module.draw_dashboard(display, current, forecast, module.Settings("key", 0, 0), now=now)
        finally:
            module.draw_icon = original_draw_icon

        by_value = {call["value"]: call for call in display.ttf_calls}
        self.assertGreaterEqual(by_value["10:24"]["x"], 205)
        self.assertGreaterEqual(by_value["Tue Jun 16"]["x"], 205)

    def test_dashboard_clock_uses_pacific_time(self):
        module = self.load_module()

        class FakeDisplay:
            width = 320
            height = 320

            def __init__(self):
                self.ttf_calls = []

            def fill(self, color):
                pass

            def fill_rect(self, x, y, w, h, color):
                pass

            def rect(self, x, y, w, h, color):
                pass

            def text_ttf(self, value, x, y, color, *, font, size, background=None):
                self.ttf_calls.append(value)

            def text(self, value, x, y, color, background=None, scale=1):
                pass

            def show(self):
                pass

        current = {
            "name": "PicoTown",
            "main": {"temp": 66, "feels_like": 65, "humidity": 57, "pressure": 1017},
            "wind": {"speed": 2.4, "deg": 91},
            "weather": [{"icon": "01d", "description": "clear sky"}],
        }
        display = FakeDisplay()
        utc_now = module.datetime(2026, 6, 16, 17, 34, tzinfo=module.timezone.utc)
        original_draw_icon = module.draw_icon

        try:
            module.draw_icon = lambda *args, **kwargs: None
            module.draw_dashboard(display, current, {"list": []}, module.Settings("key", 0, 0), now=utc_now)
        finally:
            module.draw_icon = original_draw_icon

        self.assertIn("10:34", display.ttf_calls)

    def test_loop_refreshes_weather_every_5min_and_clock_every_30sec(self):
        module = self.load_module()
        fake_now = {"value": 0.0}
        fetch_times = []
        draw_times = []

        class FakeDisplay:
            width = 320
            height = 320

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def monotonic():
            return fake_now["value"]

        def sleeper(seconds):
            fake_now["value"] += seconds

        def fetcher(settings):
            fetch_times.append(fake_now["value"])
            return (
                {
                    "name": "PicoTown",
                    "main": {"temp": 66},
                    "wind": {},
                    "weather": [{"icon": "01d", "description": "clear sky"}],
                },
                {"list": []},
            )

        def drawer(display, current, forecast, settings, **kwargs):
            draw_times.append(fake_now["value"])

        module.run_loop(
            module.Settings("key", 0, 0),
            weather_interval=300,
            clock_interval=30,
            sync_clock=False,
            max_cycles=12,
            display_factory=lambda fb: FakeDisplay(),
            fetcher=fetcher,
            drawer=drawer,
            battery_reader=lambda: None,
            monotonic=monotonic,
            sleeper=sleeper,
        )

        self.assertEqual(fetch_times, [0.0, 300.0])
        self.assertEqual(draw_times[:3], [0.0, 30.0, 60.0])
        self.assertEqual(draw_times[10], 300.0)

    def test_startup_ntp_runs_installed_utility(self):
        module = self.load_module()
        calls = []

        def runner(command, timeout):
            calls.append((command, timeout))
            return 0

        ok = module.sync_time_on_start(command="/usr/local/sbin/picocalc_ntp.py", runner=runner)

        self.assertTrue(ok)
        self.assertEqual(calls, [(["/usr/local/sbin/picocalc_ntp.py"], 20)])

    def test_finds_synced_launcher_icon_directory(self):
        module = self.load_module()
        original_script_dir = module._script_dir
        root = ROOT / "tests" / "launcher-root.tmp"
        icon_dir = root / "python" / "circuitpython_apps" / "weather_icons"
        icon_dir.mkdir(parents=True, exist_ok=True)
        try:
            module._script_dir = lambda: root
            self.assertEqual(module.find_icon_dir(), icon_dir)
        finally:
            module._script_dir = original_script_dir
            icon_dir.rmdir()
            (root / "python" / "circuitpython_apps").rmdir()
            (root / "python").rmdir()
            root.rmdir()

    def test_missing_icons_fail_loud_instead_of_drawing_fallback(self):
        module = self.load_module()

        class FakeDisplay:
            def __init__(self):
                self.fallback_draws = []

            def fill_rect(self, *args):
                self.fallback_draws.append(args)

        display = FakeDisplay()

        with self.assertRaisesRegex(FileNotFoundError, "missing weather icon"):
            module.draw_icon(display, "01d", 0, 0, icon_dir=None, suffix="_big")

        self.assertEqual(display.fallback_draws, [])


if __name__ == "__main__":
    unittest.main()
