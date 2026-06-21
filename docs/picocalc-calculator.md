# PicoCalc Calculator

`picocalc_calculator.py` is the Luckfox Lyra framebuffer port of the old
CircuitPython `picocalc_ios_calculator.py` from:

```text
/mnt/sdcard/backup_2026-02-01_181033
```

It keeps the original iOS-style four-function layout and keyboard behavior:

- Digits and decimal entry.
- `+`, `-`, `*`/`x`, and `/`.
- Enter or `=` evaluates.
- `c` clears the current entry, then clears all.
- `s` toggles sign.
- `p` or `%` applies percent.
- Backspace deletes the current entry.

The display and button labels render through PicoFB TrueType text using the
device font manager. The default calculator font is fixed-width
`DejaVu Sans Mono`. Static buttons are drawn once at startup; key presses only
redraw the display area so input stays responsive on the Lyra.

The mono font is shipped in the project as:

```text
fonts/DejaVuSansMono.ttf
```

Install/register it on the PicoCalc with:

```sh
PICOCALC_DEV_ROOT=/home/neusse/luckfox-dev setup-picocalc-fonts
```

Run it:

```sh
picocalc-calculator
```

It is also available through:

```sh
picocalc-app calculator
calculator
```

From SSH or ADB, the app detaches to `/dev/tty1` and uses the physical
PicoCalc screen and keyboard. For screenshot workflows:

```sh
picocalc-calculator --once
picocalc-screenshot /home/neusse/screenshots/calculator-latest.png
```

Exit with `Ctrl+F5`, Escape, or `q`.
