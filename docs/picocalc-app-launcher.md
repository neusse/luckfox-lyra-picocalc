# PicoCalc App Launcher

`picocalc-app` starts PicoCalc apps with the project Python path and non-root
Python environment configured. It fixes imports such as `picofb` when running
apps directly from a PicoCalc login shell.

Installed device commands:

```sh
picocalc-app weather --once
picocalc-app bubble --once
picocalc-app breakout
picocalc-app calculator
picocalc-app chess
picocalc-app clock
picocalc-app doom
picocalc-app alpine
picocalc-app launcher
picocalc-app minesweeper
picocalc-app launcher --list
picocalc-app sudoku --demo --once
picocalc-app zork --list
picocalc-bubble --once
picocalc-breakout
picocalc-calculator
picocalc-chess
picocalc-clock
picocalc-doom
picocalc-email
picocalc-launcher
picocalc-mail
picocalc-minesweeper
picocalc-weather --once
picocalc-sudoku --new medium
picozork zork1
bubble
breakout
calculator
chess
clock
doom
email
launcher
mail
minesweeper
sudoku
zork
weather --once
weather
```

The launcher expects the synced development tree at:

```text
/home/neusse/luckfox-dev
```

It sets:

```sh
PYTHONPATH=/home/neusse/luckfox-dev/python
VIRTUAL_ENV=/home/neusse/venvs/nonroot
PATH=/home/neusse/venvs/nonroot/bin:$PATH
```

`weather --once` renders one frame and exits. `weather` runs the live dashboard:

- Weather refresh: every 5 minutes.
- Clock redraw: every 30 seconds.
- Interactive weather runs on the physical PicoCalc console when launched from
  SSH or ADB.
- `Ctrl+F5` exits the live dashboard cleanly.

`launcher` starts the graphical icon menu ported from the old CircuitPython
`code.py` launcher:

- It uses `/home/neusse/luckfox-dev/launcher/launcher_data.json`.
- It reuses the legacy BMP icons under `/home/neusse/luckfox-dev/launcher/bmp`.
- From SSH or ADB, `launcher` detaches to `/dev/tty1`.
- `launcher --once` draws one menu frame to `/dev/fb0` and exits.
- `launcher --list` prints the mapped apps without touching the framebuffer.
- Controls: arrows move, Enter launches, `v` views source when available, `s`
  saves a screenshot, and `Ctrl+F5`, `q`, Escape, or Backspace exits.
- Apps started from the graphical launcher return to the launcher after they
  exit.

`alpine`, `mail`, or `email` starts Alpine mail:

- It runs inline in the current terminal, so it works from SSH and from the
  physical PicoCalc console.
- The graphical launcher starts it on the physical console and returns to the
  icon menu after Alpine exits.
- The local wrapper supplies the saved IMAP/SMTP password and sets the
  PicoCalc console font when needed.

`doom` or `puredoom` starts the native PureDOOM framebuffer port:

- It uses the existing `/usr/bin/puredoom` wrapper.
- From SSH or ADB, that wrapper starts DOOM on `/dev/tty1`.
- From the graphical launcher, DOOM runs on the physical PicoCalc screen and
  keyboard.

`clock` starts the fancy analog clock ported from the old CircuitPython app:

- It runs on `/dev/fb0` and uses the physical PicoCalc keyboard.
- From SSH or ADB, `clock` detaches to `/dev/tty1`.
- `clock --once` draws one clock frame and exits.
- Controls: `Ctrl+F5`, `q`, Escape, or Backspace exits; `c` toggles the chime
  indicator; `s` saves a screenshot.

`minesweeper` starts the graphical Minesweeper port from `fjam_minesweeper.py`:

- It runs on `/dev/fb0` and uses the physical PicoCalc keyboard.
- From SSH or ADB, `minesweeper` detaches to `/dev/tty1`.
- `picocalc-minesweeper --once` draws one menu frame and exits.
- Controls: Up/Down selects difficulty, Enter starts/reveals, Space reveals,
  `f` toggles a flag, Back returns to menu, and `Ctrl+F5` or `q` exits.

`bubble` starts the Bubble Universe framebuffer animation:

- `bubble` runs interactively from the physical PicoCalc console.
- From SSH or ADB, `bubble` detaches to `/dev/tty1`, returns a PID, and uses
  the physical PicoCalc keyboard/screen.
- `bubble --once` draws one deterministic demo frame to `/dev/fb0` and exits.
- Controls: arrows pan, Enter zooms in, Delete zooms out, `-`/`=` change speed,
  Space pauses, Escape resets, `Ctrl+F5`, `q`, or Backspace quits.

`breakout` starts the graphical Breakout port:

- It runs on `/dev/fb0` and uses the physical PicoCalc keyboard.
- From SSH or ADB, `breakout` detaches to `/dev/tty1`.
- `picocalc-app breakout --once` draws the start screen and exits.
- Controls: Left/Right or `a`/`d` moves the paddle, Space or Enter launches,
  and Backspace, Escape, `q`, or `Ctrl+F5` exits.

`calculator` starts the iOS-style graphical calculator port:

- It runs on `/dev/fb0` and uses the physical PicoCalc keyboard.
- From SSH or ADB, `calculator` detaches to `/dev/tty1`.
- `picocalc-calculator --once` draws one calculator frame and exits.
- It renders button labels and the display through PicoFB TrueType text using
  fixed-width `DejaVu Sans Mono`.
- Controls: digits and operators enter values, Enter or `=` evaluates, `c`
  clears, `s` toggles sign, `p` or `%` applies percent, Backspace deletes, and
  `Ctrl+F5`, Escape, or `q` exits.

`chess` starts the native SDL2 chessboard frontend:

- It runs on the physical PicoCalc framebuffer and keyboard.
- `chess` always starts as a managed `/dev/tty1` app, even when launched from
  the physical console, so SDL/DirectFB startup logs go to
  `/tmp/picocalc-app-chess.log` instead of painting over the screen.
- It launches `/usr/games/gnuchess --uci` as the chess engine.
- Runtime files are `/usr/libexec/picocalc/chess`, `/usr/games/gnuchess`,
  `/usr/lib/libyaml-cpp.so.0.8.0`, and `/usr/share/chess`.
- Controls: arrows select squares, Space selects a piece or setting, Enter
  moves, Escape deselects/exits a window, `s` opens settings, `i` toggles info,
  F1 shows help, F2 saves, F3 loads, F4 opens saved states, F5 opens about,
  `r` restarts, and `q` exits.

`sudoku` starts a playable graphical Sudoku game on the PicoCalc framebuffer:

- `sudoku` opens the graphical start menu on the physical PicoCalc console.
- From SSH or ADB, `sudoku` detaches to `/dev/tty1`, returns a PID, and uses
  the physical PicoCalc keyboard/screen.
- If a save exists, the menu offers `CONTINUE`; otherwise it offers `EASY`,
  `MEDIUM`, `HARD`, and `EXIT`.
- `sudoku --new easy`, `sudoku --new medium`, or `sudoku --new hard` starts a new game.
- `sudoku --demo --once` draws the built-in demo board to `/dev/fb0` and exits.
- Controls: arrows move, `1`-`9` set a value, `0`/Delete clears, `s` saves,
  `Ctrl+F5`, `q`, or Backspace saves and quits.

`zork` starts PicoZork, a terminal Z-machine runner:

- It runs inline from SSH and uses the SSH terminal width.
- On the physical PicoCalc console, it switches to `picofont 40` by default and
  wraps text to 40 columns.
- Stories are read from `/mnt/sdcard/cpz/stories` by default.
- Saves are written to `/mnt/sdcard/cpz/saves` by default.
- `zork --list` lists available stories.
- `zork --font original` switches back to the kernel 6x8 font before launching.

If a framebuffer app is already running on the physical console, remote
launcher commands refuse to start another framebuffer app on top of it. For
example:

```text
Cannot start clock; calculator is already using the PicoCalc console as PID 2579.
Not starting a second framebuffer app.
Stop it with: kill 2579
```

## Adding Apps

Add new app scripts to `/home/neusse/luckfox-dev`, then register a short name in
`scripts/device/picocalc-app`:

```python
APP_SCRIPTS = {
    "bubble": "picocalc_bubble.py",
    "breakout": "picocalc_breakout.py",
    "calculator": "picocalc_calculator.py",
    "clock": "picocalc_fancy_clock.py",
    "launcher": "picocalc_launcher.py",
    "minesweeper": "picocalc_minesweeper.py",
    "sudoku": "picocalc_sudoku.py",
    "weather": "picocalc_weather.py",
    "zork": "picocalc_zork.py",
}
```

If the app needs the physical PicoCalc console for raw terminal mode, add it to
`CONSOLE_APPS`. Interactive remote launches will be detached to `/dev/tty1`;
one-shot modes such as `--once` still run inline for screenshot workflows.

Native apps use `NATIVE_APP_COMMANDS` instead of `APP_SCRIPTS`:

```python
NATIVE_APP_COMMANDS = {
    "alpine": "/usr/bin/alpine",
    "chess": "/usr/libexec/picocalc/chess",
    "doom": "/usr/bin/puredoom",
}
```

If the app should also run from a direct command, add an alias:

```python
APP_ALIASES = {
    "bubble": "bubble",
    "breakout": "breakout",
    "calculator": "calculator",
    "chess": "chess",
    "clock": "clock",
    "doom": "doom",
    "email": "alpine",
    "launcher": "launcher",
    "mail": "alpine",
    "minesweeper": "minesweeper",
    "sudoku": "sudoku",
    "weather": "weather",
    "zork": "zork",
}
```

Install the launcher to the device:

```powershell
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
& $adb push .\scripts\device\picocalc-app /usr/local/bin/picocalc-app
& $adb shell 'chmod 755 /usr/local/bin/picocalc-app; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-app; ln -sf /usr/local/bin/picocalc-app /usr/bin/launcher; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-launcher; ln -sf /usr/local/bin/picocalc-app /usr/bin/weather; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-weather; ln -sf /usr/local/bin/picocalc-app /usr/bin/sudoku; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-sudoku; ln -sf /usr/local/bin/picocalc-app /usr/bin/bubble; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-bubble; ln -sf /usr/local/bin/picocalc-app /usr/bin/calculator; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-calculator; ln -sf /usr/local/bin/picocalc-app /usr/bin/chess; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-chess; ln -sf /usr/local/bin/picocalc-app /usr/bin/doom; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-doom; ln -sf /usr/local/bin/picocalc-app /usr/bin/mail; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-mail; ln -sf /usr/local/bin/picocalc-app /usr/bin/email; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-email; ln -sf /usr/local/bin/picocalc-app /usr/bin/zork; ln -sf /usr/local/bin/picocalc-app /usr/bin/picozork; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-zork'
```
