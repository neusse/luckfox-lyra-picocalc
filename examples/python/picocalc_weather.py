"""OpenWeather dashboard for the Luckfox Lyra PicoCalc framebuffer."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import importlib.util
import os
import json
import ssl
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import URLError

from picofb import BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW, Display, color565, load_bmp
from picoterm.appkeys import is_app_exit_key
from picoterm.evdev import EventKeyboard, find_picocalc_event
from picoterm.screen import RawTerminal


API_ROOT = "https://api.openweathermap.org/data/2.5"
DEFAULT_UNITS = "imperial"
DEFAULT_WEATHER_INTERVAL = 300
DEFAULT_CLOCK_INTERVAL = 30

DARK = color565(2, 7, 14)
PANEL = color565(11, 24, 34)
PANEL2 = color565(18, 38, 52)
INK = color565(234, 242, 248)
MUTED_RGB = (205, 218, 228)
MUTED = color565(*MUTED_RGB)
ORANGE = color565(255, 155, 35)
RAIN = color565(75, 190, 255)
SNOW = color565(210, 248, 255)
FOG = color565(170, 180, 185)
GOOD = color565(112, 245, 110)
BATTERY_PATH = "/sys/bus/i2c/devices/0-001f/battery_percent"
_ICON_CACHE = {}


@dataclass(frozen=True)
class Settings:
    key: str
    lat: float
    lon: float
    units: str = DEFAULT_UNITS


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_local_secrets() -> dict:
    for path in (Path.cwd() / "secrets.py", _script_dir() / "secrets.py"):
        if not path.exists():
            continue
        spec = importlib.util.spec_from_file_location("picocalc_weather_secrets", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return dict(getattr(module, "secrets", {}))
    return {}


def load_settings(args: argparse.Namespace) -> Settings:
    secrets = _load_local_secrets()
    key = args.key or os.environ.get("OPENWEATHER_KEY") or secrets.get("openweather_key")
    lat = args.lat if args.lat is not None else os.environ.get("OPENWEATHER_LAT", secrets.get("lat"))
    lon = args.lon if args.lon is not None else os.environ.get("OPENWEATHER_LON", secrets.get("lon"))
    units = args.units or os.environ.get("OPENWEATHER_UNITS") or secrets.get("units", DEFAULT_UNITS)

    if not key:
        raise SystemExit("missing OpenWeather key: use --key, OPENWEATHER_KEY, or secrets.py")
    if lat is None or lon is None:
        raise SystemExit("missing location: use --lat/--lon, env vars, or secrets.py")

    return Settings(key=str(key), lat=float(lat), lon=float(lon), units=str(units))


def read_battery_percent(path: str | Path = BATTERY_PATH) -> int | None:
    try:
        value = Path(path).read_text(encoding="ascii").strip()
        percent = int(float(value))
    except (OSError, ValueError):
        return None
    return max(0, min(100, percent))


def find_icon_dir(explicit: str | None = None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(
        [
            _script_dir() / "weather_icons",
            _script_dir() / "python" / "circuitpython_apps" / "weather_icons",
            _script_dir().parent.parent / "python" / "circuitpython_apps" / "weather_icons",
            Path.cwd() / "weather_icons",
            Path.cwd() / "python" / "circuitpython_apps" / "weather_icons",
        ]
    )
    for path in candidates:
        if path.exists() and path.is_dir():
            return path
    return None


def _url(path: str, settings: Settings) -> str:
    query = urlencode(
        {
            "lat": settings.lat,
            "lon": settings.lon,
            "appid": settings.key,
            "units": settings.units,
        }
    )
    return f"{API_ROOT}/{path}?{query}"


def current_url(settings: Settings) -> str:
    return _url("weather", settings)


def forecast_url(settings: Settings) -> str:
    return _url("forecast", settings)


def fetch_json(url: str) -> dict:
    try:
        import requests
    except ModuleNotFoundError:
        requests = None

    if requests is not None:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    from urllib.request import urlopen

    try:
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (ssl.SSLError, URLError) as exc:
        reason = getattr(exc, "reason", exc)
        if not isinstance(reason, ssl.SSLError):
            raise
        with urlopen(url, timeout=30, context=ssl._create_unverified_context()) as response:
            return json.loads(response.read().decode("utf-8"))


def fetch_weather(settings: Settings) -> tuple[dict, dict]:
    return fetch_json(current_url(settings)), fetch_json(forecast_url(settings))


def fmt_temp(value) -> str:
    if value is None:
        return "--F"
    return f"{int(round(float(value)))}F"


def fmt_speed(value, units: str = DEFAULT_UNITS) -> str:
    if value is None:
        return "--"
    suffix = "mph" if units == "imperial" else "m/s" if units == "standard" else "kph"
    return f"{float(value):.0f}{suffix}"


def fmt_wind_tile(speed, degrees) -> str:
    if speed is None:
        return f"-- {wind_dir_16pt(degrees)}"
    return f"{float(speed):.0f} {wind_dir_16pt(degrees)}"


def fmt_pressure(hpa) -> str:
    if hpa is None:
        return "--"
    return f"{float(hpa) * 0.0295299830714:.2f}"


def fmt_pop(value) -> str:
    return f"POP {int(round(float(value or 0) * 100))}%"


def wind_dir_16pt(degrees) -> str:
    if degrees is None:
        return "?"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[int((float(degrees) + 11.25) // 22.5) % 16]


def title_case(value: str) -> str:
    return " ".join(part[:1].upper() + part[1:] for part in str(value).split())


def local_day_name(epoch: int, offset: int = 0) -> str:
    dt = datetime.fromtimestamp(int(epoch) + int(offset), tz=timezone.utc)
    return dt.strftime("%a")


def local_datetime(value: datetime | None = None) -> datetime:
    if value is None:
        return datetime.now().astimezone()
    if value.tzinfo is None:
        return value
    return value.astimezone()


def aggregate_forecast_daily(forecast_json: dict, days: int = 5) -> list[dict]:
    items = forecast_json.get("list") or []
    offset = int((forecast_json.get("city") or {}).get("timezone") or 0)
    by_day: dict[str, dict] = {}

    for item in items:
        epoch = item.get("dt")
        if epoch is None:
            continue
        dt = datetime.fromtimestamp(int(epoch) + offset, tz=timezone.utc)
        key = dt.strftime("%Y-%m-%d")
        main = item.get("main") or {}
        weather = (item.get("weather") or [{}])[0] or {}
        pop = float(item.get("pop") or 0)

        rec = by_day.setdefault(
            key,
            {
                "day": dt.strftime("%a"),
                "tmin": main.get("temp_min"),
                "tmax": main.get("temp_max"),
                "pop": pop,
                "icon": weather.get("icon") or "01d",
                "desc": weather.get("description") or "",
                "_best_pop": -1.0,
            },
        )
        tmin = main.get("temp_min")
        tmax = main.get("temp_max")
        if tmin is not None and (rec["tmin"] is None or tmin < rec["tmin"]):
            rec["tmin"] = tmin
        if tmax is not None and (rec["tmax"] is None or tmax > rec["tmax"]):
            rec["tmax"] = tmax
        if pop >= rec["_best_pop"]:
            rec["pop"] = pop
            rec["icon"] = weather.get("icon") or rec["icon"]
            rec["desc"] = weather.get("description") or rec["desc"]
            rec["_best_pop"] = pop

    out = []
    for key in sorted(by_day)[:days]:
        rec = by_day[key]
        rec.pop("_best_pop", None)
        out.append(rec)
    return out


def _text_width(value: str, scale: int = 1) -> int:
    return max(0, len(str(value)) * 6 * scale - scale)


def _right_text(display, value: str, right: int, y: int, color: int, *, background=None, scale: int = 1) -> None:
    display.text(value, right - _text_width(value, scale), y, color, background=background, scale=scale)


def _text(display, value: str, x: int, y: int, color: int, *, size: int = 14, font: str = "Decker") -> None:
    try:
        display.text_ttf(value, x, y, color, font=font, size=size)
    except Exception:
        scale = 2 if size >= 18 else 1
        display.text(value, x, y, color, scale=scale)


def _accent(icon: str) -> int:
    fam = (icon or "01")[:2]
    if fam == "01":
        return YELLOW
    if fam == "02":
        return ORANGE
    if fam in ("03", "04"):
        return FOG
    if fam in ("09", "10"):
        return RAIN
    if fam == "11":
        return MAGENTA
    if fam == "13":
        return SNOW
    if fam == "50":
        return FOG
    return CYAN


def draw_bitmap_icon(display, icon: str, x: int, y: int, *, icon_dir: Path | None, suffix: str, tint: int) -> None:
    if icon_dir is None:
        raise FileNotFoundError("missing weather icon directory")
    path = icon_dir / f"{icon}{suffix}.bmp"
    if not path.exists():
        raise FileNotFoundError(f"missing weather icon: {path}")
    key = (str(path), tint)
    try:
        bitmap = _ICON_CACHE[key]
    except KeyError:
        try:
            bitmap = load_bmp(path, transparent_index=0, tint=tint)
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"failed to load weather icon: {path}: {exc}") from exc
        _ICON_CACHE[key] = bitmap
    display.blit(bitmap, x, y)


def draw_icon(
    display,
    icon: str,
    x: int,
    y: int,
    scale: int = 2,
    *,
    icon_dir: Path | None = None,
    suffix: str | None = None,
) -> None:
    color = _accent(icon)
    if not suffix:
        raise FileNotFoundError("missing weather icon suffix")
    draw_bitmap_icon(display, icon, x, y, icon_dir=icon_dir, suffix=suffix, tint=color)


def draw_panel(display, x: int, y: int, w: int, h: int, title: str, border: int = CYAN) -> None:
    display.fill_rect(x, y, w, h, PANEL)
    display.rect(x, y, w, h, border)
    display.text(title[:12].upper(), x + 5, y + 5, MUTED)


def draw_tile_value(display, value: str, x: int, y: int, width: int) -> None:
    value = str(value)[:8]
    size = 23 if len(value) <= 5 else 20 if len(value) <= 7 else 17
    try:
        display.text_ttf(value, x + 5, y - 3, WHITE, font="Decker", size=size)
    except Exception:
        scale = 2 if _text_width(value, scale=2) <= width - 10 else 1
        display.text(value, x + 5, y, WHITE, scale=scale)


def hide_console_cursor() -> None:
    for path in ("/dev/tty1", "/dev/console"):
        try:
            with open(path, "wb", buffering=0) as tty:
                tty.write(b"\033[?25l\033[40;50H")
            return
        except OSError:
            continue


def is_console_tty(path: str) -> bool:
    return path.startswith("/dev/tty") and not path.startswith("/dev/tty0")


def current_tty(ttyname=None) -> str:
    ttyname = getattr(os, "ttyname", None) if ttyname is None else ttyname
    if ttyname is None:
        return ""
    try:
        return ttyname(0)
    except OSError:
        return ""


def open_keyboard(path: str | None = None):
    return EventKeyboard(path or find_picocalc_event())


def draw_dashboard(
    display,
    current: dict,
    forecast: dict,
    settings: Settings,
    *,
    battery_percent: int | None = None,
    icon_dir: Path | None = None,
    now: datetime | None = None,
) -> None:
    width, height = display.width, display.height
    weather = (current.get("weather") or [{}])[0] or {}
    main = current.get("main") or {}
    wind = current.get("wind") or {}
    icon = weather.get("icon") or "01d"
    desc = title_case(weather.get("description") or "Weather")[:21]
    place = (current.get("name") or "PicoCalc")[:20]
    days = aggregate_forecast_daily(forecast, days=5)
    now = local_datetime(now)

    display.fill(DARK)
    display.fill_rect(0, 0, width, 34, PANEL2)
    display.rect(0, 0, width, height, CYAN)
    _text(display, "PicoCalc Weather", 8, 5, WHITE, size=22)
    header_right = f"BAT {battery_percent}%" if battery_percent is not None else time.strftime("%H:%M")
    _right_text(display, header_right, width - 8, 10, GOOD if battery_percent is not None else MUTED)

    display.fill_rect(8, 42, width - 16, 88, PANEL)
    display.rect(8, 42, width - 16, 88, _accent(icon))
    draw_icon(display, icon, 18, 50, scale=3, icon_dir=icon_dir, suffix="_big")
    _text(display, fmt_temp(main.get("temp")), 112, 48, WHITE, size=44, font="Decker")
    _text(display, now.strftime("%H:%M"), 218, 57, WHITE, size=24, font="Decker")
    _text(display, now.strftime("%a %b %d"), 218, 84, MUTED, size=14, font="Decker")
    _text(display, desc, 114, 93, GOOD, size=17)
    display.text(place.upper(), 115, 113, MUTED)

    tile_y = 138
    tile_w = 76
    tiles = [
        ("FEELS", fmt_temp(main.get("feels_like")), ORANGE),
        ("HUMID", f"{main.get('humidity', '--')}%", RAIN),
        ("WIND MPH" if settings.units == "imperial" else "WIND", fmt_wind_tile(wind.get("speed"), wind.get("deg")), GREEN),
        ("PRESS", fmt_pressure(main.get("pressure")), MAGENTA),
    ]
    for index, (title, value, border) in enumerate(tiles):
        x = 8 + index * tile_w
        draw_panel(display, x, tile_y, tile_w - 4, 54, title, border)
        draw_tile_value(display, value, x, tile_y + 28, tile_w - 4)

    display.text("5 DAY FORECAST", 10, 205, YELLOW)
    base_y = 222
    cell_w = width // 5
    for index in range(5):
        x = index * cell_w
        display.rect(x + 2, base_y, cell_w - 4, 88, BLUE)
        if index < len(days):
            day = days[index]
            display.text(day["day"].upper(), x + 8, base_y + 8, MUTED)
            draw_icon(display, day.get("icon", "01d"), x + 12, base_y + 23, scale=1, icon_dir=icon_dir, suffix="_small")
            hi_lo = f"{fmt_temp(day.get('tmax'))}/{fmt_temp(day.get('tmin'))}".replace("F", "")
            display.text(hi_lo[:9], x + 6, base_y + 61, WHITE)
            display.text(fmt_pop(day.get("pop", 0)), x + 4, base_y + 74, RAIN)
        else:
            display.text("---", x + 16, base_y + 40, MUTED)

    display.show()


def run_once(
    settings: Settings,
    framebuffer: str = "/dev/fb0",
    icon_dir: Path | None = None,
) -> None:
    current, forecast = fetch_weather(settings)
    battery_percent = read_battery_percent()
    hide_console_cursor()
    with Display(framebuffer) as display:
        draw_dashboard(
            display,
            current,
            forecast,
            settings,
            battery_percent=battery_percent,
            icon_dir=icon_dir,
        )


def run_loop(
    settings: Settings,
    framebuffer: str = "/dev/fb0",
    icon_dir: Path | None = None,
    *,
    weather_interval: float = DEFAULT_WEATHER_INTERVAL,
    clock_interval: float = DEFAULT_CLOCK_INTERVAL,
    max_cycles: int | None = None,
    display_factory=Display,
    fetcher=fetch_weather,
    drawer=draw_dashboard,
    battery_reader=read_battery_percent,
    monotonic=time.monotonic,
    sleeper=time.sleep,
    keyboard=None,
    keyboard_path: str | None = None,
) -> None:
    if weather_interval <= 0:
        raise ValueError("weather_interval must be positive")
    if clock_interval <= 0:
        raise ValueError("clock_interval must be positive")

    hide_console_cursor()

    current = None
    forecast = None
    next_weather = 0.0
    cycles = 0

    keyboard_context = nullcontext(keyboard)
    terminal_context = nullcontext()
    if keyboard is None and is_console_tty(current_tty()):
        keyboard_context = open_keyboard(keyboard_path)
        terminal_context = RawTerminal()

    with terminal_context, display_factory(framebuffer) as display, keyboard_context as active_keyboard:
        while True:
            now_mono = monotonic()
            if current is None or forecast is None or now_mono >= next_weather:
                current, forecast = fetcher(settings)
                next_weather = now_mono + weather_interval

            drawer(
                display,
                current,
                forecast,
                settings,
                battery_percent=battery_reader(),
                icon_dir=icon_dir,
            )

            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                return

            next_clock = now_mono + clock_interval
            wake_at = min(next_clock, next_weather)
            while True:
                if active_keyboard is not None and is_app_exit_key(active_keyboard.read_key(timeout=0.0)):
                    return
                remaining = wake_at - monotonic()
                if remaining <= 0:
                    break
                sleeper(min(1.0, remaining))


def main() -> int:
    parser = argparse.ArgumentParser(description="PicoCalc OpenWeather framebuffer dashboard")
    parser.add_argument("--key")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--units", choices=("imperial", "metric", "standard"))
    parser.add_argument("--fb", default="/dev/fb0")
    parser.add_argument("--icon-dir")
    parser.add_argument("--once", action="store_true", help="render once and exit")
    parser.add_argument("--weather-interval", type=float, default=DEFAULT_WEATHER_INTERVAL)
    parser.add_argument("--clock-interval", type=float, default=DEFAULT_CLOCK_INTERVAL)
    parser.add_argument("--keyboard", help="evdev keyboard path, default: auto-detect PicoCalc keyboard on console")
    args = parser.parse_args()

    settings = load_settings(args)
    icon_dir = find_icon_dir(args.icon_dir)
    if args.once:
        run_once(
            settings,
            framebuffer=args.fb,
            icon_dir=icon_dir,
        )
    else:
        run_loop(
            settings,
            framebuffer=args.fb,
            icon_dir=icon_dir,
            weather_interval=args.weather_interval,
            clock_interval=args.clock_interval,
            keyboard_path=args.keyboard,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
