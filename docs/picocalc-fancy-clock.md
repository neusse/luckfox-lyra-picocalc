# PicoCalc Fancy Clock

`picocalc_fancy_clock.py` is the Luckfox Lyra framebuffer port of the old
CircuitPython `picocalc_fancy_clock.py` from:

```text
/mnt/sdcard/backup_2026-02-01_181033
```

The Luckfox version uses PicoFB drawing primitives instead of `displayio` and
uses the system clock maintained by BusyBox `ntpd`. It keeps the visual shape of
the original app:

- Analog watch face.
- Moon phase window.
- Date window.
- Subdial seconds hand.
- Chime enabled/disabled indicator.

Run it:

```sh
picocalc-app clock
```

From SSH or ADB, `picocalc-app clock` detaches to `/dev/tty1` and uses the
physical PicoCalc screen and keyboard. For screenshot workflows:

```sh
picocalc-app clock --once
picocalc-screenshot /home/neusse/screenshots/fancy-clock-latest.png
```

Controls:

- `Ctrl+F5`, `q`, Escape, or Backspace exits.
- `c` toggles the chime indicator.
- `s` saves a framebuffer screenshot.

The chime indicator is currently visual only. The CircuitPython audio/WAV stack
was not ported to the Luckfox Linux build.
