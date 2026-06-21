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

```text
fonts/DejaVuSansMono.ttf
```

Fixed-width TrueType font used by the calculator and installed by
`scripts/device/setup-picocalc-fonts`.

```text
python/picozork/
```

Terminal Z-machine host for Zork-compatible version 3 story files. It reuses
the CPZ Machine opcode processor and adds Linux stdin/stdout handling, save
files, SSH support, and PicoCalc 40-column console font support.

## Apps And Demos

```text
examples/python/picocalc_launcher.py
launcher/launcher_data.json
launcher/bmp/
```

Graphical icon launcher ported from the old CircuitPython `code.py` menu. It
keeps the legacy JSON and BMP assets while mapping currently ported apps to
`picocalc-app` commands. See `docs/picocalc-graphical-launcher.md`.

```text
examples/python/picocalc_weather.py
```

OpenWeather dashboard for the PicoCalc screen. It requires BMP icon assets and
fails loudly if they are missing.

```text
examples/python/picocalc_fancy_clock.py
```

Fancy analog clock ported from the CircuitPython PicoCalc app. It renders a
watch face, moon phase, date window, subdial seconds, and chime indicator on
the Linux framebuffer. See `docs/picocalc-fancy-clock.md`.

```text
examples/python/picocalc_minesweeper.py
python/picogames/minesweeper.py
```

Graphical Minesweeper port from the FJam PicoCalc CircuitPython app plus the
reusable game model. It supports first-click-safe mine placement, flags, flood
reveal, win/loss detection, and the `picocalc-minesweeper` command. See
`docs/picocalc-minesweeper.md`.

```text
examples/python/picocalc_bubble.py
python/picogames/bubble.py
```

Bubble Universe framebuffer animation and reusable model/renderer. See
`docs/picocalc-bubble.md`.

```text
examples/python/picocalc_calculator.py
python/picogames/calculator.py
```

iOS-style graphical calculator ported from the CircuitPython PicoCalc
calculator. It uses measured PicoFB TrueType text with fixed-width
`DejaVu Sans Mono` for the display and button labels. See
`docs/picocalc-calculator.md`.

```text
examples/python/picocalc_sudoku.py
python/picogames/sudoku.py
python/picoterm/evdev.py
```

Graphical framebuffer Sudoku app, shared Sudoku model, and PicoCalc keyboard
input-event reader. See `docs/picocalc-sudoku.md`.

```text
examples/python/picocalc_zork.py
python/picozork/
```

PicoZork terminal app for SSH or the physical PicoCalc console. Stories default
to `/mnt/sdcard/cpz/stories`, saves default to `/mnt/sdcard/cpz/saves`, and
console mode uses `picofont 40`.

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

## Migration Notes

```text
docs/buildroot-migration-change-map.md
```

Runtime grafts and local image changes made after the base Buildroot image
booted. Use this as the map for porting the current working setup to a newer
Buildroot image.

## Host Tools

```text
scripts/host/luckfox-dev.py
```

Windows/ADB helper for the Thonny-like edit-sync-run loop. See
`docs/dev-loop.md`.

```text
docs/images/sudoku-menu.png
docs/images/sudoku-board.png
docs/images/bubble-universe.png
```

Checked-in screenshots for the graphical app documentation.

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
Sudoku, PicoZork, input-event decoding, screenshots, TTF rendering, and the
keyboard patch.
