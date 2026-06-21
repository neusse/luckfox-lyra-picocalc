# PicoFB

PicoFB is a small Python RGB565 framebuffer library for the Luckfox Lyra Model B inside the ClockworkPi PicoCalc.

Current target facts:

- Device: `/dev/fb0`
- Driver: `ili9488drmfb`
- Resolution: `320x320`
- Format: 16 bpp RGB565
- Stride: 640 bytes

## Host Tests

```powershell
$env:PYTHONPATH = "$PWD\python"; python -m unittest discover -s tests -p "test_picofb*.py"
```

## Run On The PicoCalc

```powershell
python .\tools\luckfox-dev.py runpy .\examples\python\fb_demo.py
```

`tools/luckfox-dev.py runpy` syncs the local `python/` package tree to `/home/neusse/luckfox-dev/python` and sets `PYTHONPATH` before running the script as `neusse`.

## Permission Setup

`/dev/fb0` should be writable by users in the `video` group. Use the configured ADB path to install and run the device-side helper:

```powershell
$adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
& $adb push .\scripts\device\enable-framebuffer-user.sh /tmp/enable-framebuffer-user.sh
& $adb shell "sh /tmp/enable-framebuffer-user.sh neusse"
```

Log out and back in after changing groups. Existing sessions may not show the new `video` membership until they are restarted.

## Minimal Usage

```python
from picofb import Display, color565

with Display("/dev/fb0") as display:
    display.fill(color565(0, 0, 0))
    display.text("Hello", 8, 8, color565(255, 255, 255))
    display.rect(20, 40, 100, 50, color565(0, 255, 0))
    display.show()
```

## Bulk Pixel Drawing

Use `scatter_rgb565(xs, ys, colors)` when an app needs to draw many individual
pixels per frame. It clips out-of-bounds coordinates and writes RGB565 pixels in
bulk. If NumPy is installed, PicoFB uses a NumPy-backed fast path; otherwise it
falls back to ordinary `pixel()` writes.

```python
from picofb import Display, RED, GREEN, BLUE

with Display("/dev/fb0") as display:
    display.clear()
    display.scatter_rgb565(
        xs=[10, 20, 30],
        ys=[10, 20, 30],
        colors=[RED, GREEN, BLUE],
    )
    display.show()
```

## TrueType Fonts

PicoFB can draw scalable TrueType text with `text_ttf()`. It uses Pillow when Pillow is installed, and otherwise falls back to the system FreeType library through `ctypes`. The `font` argument can be a direct `.ttf` path or a fontconfig family/name.

```python
from picofb import Display, WHITE

with Display("/dev/fb0") as display:
    display.clear()
    display.text_ttf("Hello TTF", 12, 20, WHITE, font="Decker", size=24)
    display.show()
```

The current PicoCalc image includes a few small bundled TTF fonts outside the normal fontconfig search path. Install the device-side symlinks with:

```powershell
$adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
& $adb push .\scripts\device\setup-picocalc-fonts /usr/local/sbin/setup-picocalc-fonts
& $adb shell "chmod 755 /usr/local/sbin/setup-picocalc-fonts; /usr/local/sbin/setup-picocalc-fonts"
```

This registers these fontconfig families:

```text
Decker
Cinema
Grunge
Morpheus
Notepad
```

## BMP Icons

PicoFB can load simple uncompressed BMP icon assets with `load_bmp()`. This is intended for small PicoCalc assets such as the 8-bit paletted weather icons from the CircuitPython apps.

```python
from picofb import Display, YELLOW, load_bmp

icon = load_bmp("weather_icons/01d_small.bmp", transparent_index=0, tint=YELLOW)

with Display("/dev/fb0") as display:
    display.blit(icon, 12, 24)
    display.show()
```

The loader currently supports uncompressed 8-bit paletted BMPs and 24-bit BMPs. Palette index `0` is transparent by default.

## Screenshots

The device utility `picocalc-screenshot` captures `/dev/fb0` and writes a PNG without Pillow or external tools.

```sh
picocalc-screenshot
picocalc-screenshot /home/neusse/screenshots/latest.png
```

With no output path, it writes to:

```text
/home/neusse/screenshots/picocalc-YYYYMMDD-HHMMSS.png
```

From Windows, pull the latest image with ADB:

```powershell
$adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
& $adb pull /home/neusse/screenshots/latest.png .\artifacts\screenshots\picocalc-latest.png
```

## Notes

- `text()` uses a built-in 5x7 bitmap font and has no dependencies.
- `text_ttf()` renders scalable TrueType fonts using Pillow or system FreeType.
- `measure_ttf_text()` returns rendered text bounds for accurate centering and
  right alignment.
- `picocalc-screenshot` reads the RGB565 framebuffer and saves a PNG using only Python's standard library.
- Lowercase letters render through uppercase fallback.
- Drawing clips silently when coordinates are outside the screen.
- PicoFB does not restore the Linux console after drawing.
