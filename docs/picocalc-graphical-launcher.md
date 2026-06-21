# PicoCalc Graphical Launcher

`picocalc_launcher.py` is the Luckfox Lyra console port of the old
CircuitPython `code.py` launcher from:

```text
/mnt/sdcard/backup_2026-02-01_181033
```

It keeps the original JSON-driven app list and reuses the legacy BMP icons.
The synced runtime copy lives at:

```text
/home/neusse/luckfox-dev/picocalc_launcher.py
/home/neusse/luckfox-dev/launcher/launcher_data.json
/home/neusse/luckfox-dev/launcher/bmp/
```

Run it from the PicoCalc console:

```sh
picocalc-app launcher
```

From SSH or ADB, `picocalc-app launcher` detaches to `/dev/tty1` like the
other graphical framebuffer apps. For a screenshot-friendly render:

```sh
picocalc-app launcher --once
picocalc-screenshot /home/neusse/screenshots/launcher-latest.png
```

Useful non-graphical check:

```sh
picocalc-app launcher --list
```

Controls:

- Arrows move between icons.
- Enter launches a ported app.
- `v` opens the source path in `picoedit.py` when the source exists.
- `s` saves a framebuffer screenshot.
- `Ctrl+F5`, `q`, Escape, or Backspace exits.

When a launched app exits, the launcher redraws and returns to the icon menu.
This is intentionally different from the old CircuitPython launcher, which
reloaded into the next program.

Currently mapped apps:

```text
weather        -> picocalc-app weather
sudoku         -> picocalc-app sudoku
bubble graphic -> picocalc-app bubble
breakout       -> picocalc-app breakout
email          -> picocalc-app alpine
zork           -> picocalc-app zork
doom           -> picocalc-app doom
```

Other legacy entries remain visible and show `not ported yet`. This keeps the
menu useful as a translation roadmap instead of hiding old apps.
