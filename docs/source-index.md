# Source Index

This file maps the published tree to the work it enables.

## Runtime Python

```text
python/picofb/
```

Small RGB565 framebuffer library for `/dev/fb0`.

Important modules:

- `canvas.py`: drawing primitives, text, blitting, BMP support.
- `display.py`: framebuffer device wrapper.
- `bmp.py`: uncompressed BMP loader used by the weather icons.
- `screenshot.py`: framebuffer-to-PNG capture utility.
- `ttf.py`: TrueType rendering path.

## Apps And Demos

```text
examples/python/picocalc_weather.py
```

OpenWeather dashboard for the PicoCalc screen. It requires BMP icon assets and
fails loudly if they are missing.

```text
examples/python/picocalc_sudoku.py
python/picogames/sudoku.py
python/picoterm/evdev.py
```

Graphical framebuffer Sudoku app, shared Sudoku model, and PicoCalc keyboard
input-event reader. See `docs/picocalc-sudoku.md`.

```text
examples/python/fb_demo.py
examples/python/fb_ttf_demo.py
examples/python/fb_ttf_showcase.py
examples/python/rich_picocalc_demo.py
```

Framebuffer, TrueType, and Rich terminal demos.

## Device Utilities

```text
scripts/device/picocalc-app
scripts/device/picocalc-screenshot
scripts/device/picocalc-mcu
scripts/device/picocalc-sdcard
scripts/device/picocalc_ntp.py
```

User-facing device commands for app launching, screenshots, MCU state, SD-card
handling, and NTP.

Boot/startup helpers:

```text
scripts/device/S02swapfile
scripts/device/S04load_88xxau
scripts/device/S45wifi
scripts/device/S46python_ntp
scripts/device/S55issue_ip
scripts/device/S56console_permissions
```

## Host Tools

```text
scripts/host/luckfox-dev.py
```

Windows/ADB helper for the Thonny-like edit-sync-run loop. See
`docs/dev-loop.md`.

```text
docs/images/sudoku-menu.png
docs/images/sudoku-board.png
```

Checked-in screenshots for the graphical Sudoku documentation.

## Kernel And Build Patches

```text
patches/picocalc-keyboard-mcu-sysfs.patch
patches/picocalc-luckfox-lyra-codex-wsl.patch
```

The first patch adds keyboard MCU battery/backlight sysfs attributes. The second
records local build compatibility changes used during the WSL/Docker build flow.

## Tests

```text
tests/
```

Host-side regression tests for PicoFB, the weather app, launcher behavior,
Sudoku, input-event decoding, screenshots, TTF rendering, and the keyboard patch.
