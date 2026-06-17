# Thonny-Like Development Loop

This project uses `scripts/host/luckfox-dev.py` as a small host-side development
loop for the Luckfox Lyra PicoCalc. It is not an IDE, but it covers the useful
parts of a Thonny-style workflow:

1. Edit code on Windows.
2. Sync the shared Python library tree to the PicoCalc.
3. Upload the app script being tested.
4. Run it on the PicoCalc as the non-root user `neusse`.
5. Repeat quickly.

The helper talks to the device over ADB. The PicoCalc does not need SSH for this
loop.

## Files

```text
scripts/host/luckfox-dev.py          Host-side helper run from Windows
python/                              Shared Python packages synced to device
examples/python/                     App and demo entry points
examples/c/                          C cross-compile smoke tests
```

The remote development directory is:

```text
/home/neusse/luckfox-dev
```

The synced Python package directory is:

```text
/home/neusse/luckfox-dev/python
```

When available, the helper activates:

```text
/home/neusse/venvs/nonroot
```

## Check Device Status

Run this from the repository root on Windows:

```powershell
python .\scripts\host\luckfox-dev.py status
```

This prints ADB device state, kernel info, network info, Python version, pip
state, and swap state.

## Run Python Apps

Run a simple Python example:

```powershell
python .\scripts\host\luckfox-dev.py runpy .\examples\python\hello_luckfox.py
```

Run the weather dashboard once:

```powershell
python .\scripts\host\luckfox-dev.py runpy .\examples\python\picocalc_weather.py --once
```

Render the Sudoku menu for screenshots:

```powershell
python .\scripts\host\luckfox-dev.py runpy .\examples\python\picocalc_sudoku.py --menu-once
```

Render the Sudoku board for screenshots:

```powershell
python .\scripts\host\luckfox-dev.py runpy .\examples\python\picocalc_sudoku.py --demo --once
```

`runpy` always syncs the local `python/` tree first. That means changes to
`picofb`, `picoterm`, or `picogames` are available to the uploaded script right
away.

## Interactive Console Apps

Some apps are physical-console apps. Sudoku is one of them.

The graphical Sudoku app reads the PicoCalc keyboard from `/dev/input/event*`.
That is the right input path for a framebuffer app, but it also means the
interactive command should be launched from the PicoCalc itself:

```sh
sudoku
```

Launching interactive Sudoku from SSH or ADB fails intentionally. Use
`--menu-once` or `--demo --once` from the host loop when you only need to render
screenshots.

## Push One File

Use `push` when you only need to copy a file:

```powershell
python .\scripts\host\luckfox-dev.py push .\scripts\device\picocalc-app /usr/local/bin/picocalc-app
```

## Open A Shell

```powershell
python .\scripts\host\luckfox-dev.py shell
```

This opens an ADB shell as `neusse`.

## Build And Run C

The helper can cross-compile simple C programs through WSL using the Luckfox SDK
toolchain:

```powershell
python .\scripts\host\luckfox-dev.py runc .\examples\c\hello_luckfox.c
```

This builds with:

```text
arm-none-linux-gnueabihf-gcc
```

Then it pushes the binary to `/home/neusse/luckfox-dev` and runs it.

## Environment Overrides

If ADB is not at the default path, set `ADB` before running the helper:

```powershell
$env:ADB = 'C:\path\to\adb.exe'
python .\scripts\host\luckfox-dev.py status
```

