# PicoCalc App Launcher

`picocalc-app` starts PicoCalc apps with the project Python path and non-root
Python environment configured. It fixes imports such as `picofb` when running
apps directly from a PicoCalc login shell.

Installed device commands:

```sh
picocalc-app weather --once
picocalc-app bubble --once
picocalc-app sudoku --demo --once
picocalc-bubble --once
picocalc-weather --once
picocalc-sudoku --new medium
bubble
sudoku
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

`bubble` starts the Bubble Universe framebuffer animation:

- `bubble` runs interactively from the physical PicoCalc console.
- `bubble --once` draws one deterministic demo frame to `/dev/fb0` and exits.
- Interactive Bubble intentionally fails from SSH/ADB shells because input comes
  from the PicoCalc `/dev/input/event*` device.
- Controls: arrows pan, Enter zooms in, Delete zooms out, `-`/`=` change speed,
  Space pauses, Escape resets, `q` or Backspace quits.

`sudoku` starts a playable graphical Sudoku game on the PicoCalc framebuffer:

- `sudoku` opens the graphical start menu on the physical PicoCalc console.
- The interactive app intentionally fails from SSH/ADB shells because keyboard
  input comes from the PicoCalc `/dev/input/event*` device, not SSH stdin.
- If a save exists, the menu offers `CONTINUE`; otherwise it offers `EASY`,
  `MEDIUM`, `HARD`, and `EXIT`.
- `sudoku --new easy`, `sudoku --new medium`, or `sudoku --new hard` starts a new game.
- `sudoku --demo --once` draws the built-in demo board to `/dev/fb0` and exits.
- Controls: arrows move, `1`-`9` set a value, `0`/Delete clears, `s` saves, `q` or Backspace saves and quits.

If an app is already running, the launcher exits instead of starting a second
copy. For example:

```text
weather is already running on the PicoCalc console as PID 3268.
Not starting a second copy.
Stop it with: kill 3268
For a one-shot render after stopping it: picocalc-app weather --once
```

## Adding Apps

Add new app scripts to `/home/neusse/luckfox-dev`, then register a short name in
`scripts/device/picocalc-app`:

```python
APP_SCRIPTS = {
    "bubble": "picocalc_bubble.py",
    "sudoku": "picocalc_sudoku.py",
    "weather": "picocalc_weather.py",
}
```

If the app should also run from a direct command, add an alias:

```python
APP_ALIASES = {
    "bubble": "bubble",
    "sudoku": "sudoku",
    "weather": "weather",
}
```

Install the launcher to the device:

```powershell
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
& $adb push .\scripts\device\picocalc-app /usr/local/bin/picocalc-app
& $adb shell 'chmod 755 /usr/local/bin/picocalc-app; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-app; ln -sf /usr/local/bin/picocalc-app /usr/bin/weather; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-weather; ln -sf /usr/local/bin/picocalc-app /usr/bin/sudoku; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-sudoku; ln -sf /usr/local/bin/picocalc-app /usr/bin/bubble; ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-bubble'
```
