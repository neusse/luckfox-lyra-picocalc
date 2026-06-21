# PicoCalc Breakout

`picocalc_breakout.py` is the Luckfox Lyra framebuffer port of the CircuitPython
`picocalc_breakout.py` from:

```text
/mnt/sdcard/backup_2026-02-01_181033
```

This port keeps the original brick, paddle, score, lives, and restart behavior
but skips the CircuitPython PWM sound effects.

Run it:

```sh
picocalc-app breakout
breakout
picocalc-breakout
```

From SSH or ADB, `breakout` detaches to `/dev/tty1` and uses the physical
PicoCalc screen and keyboard. For screenshot workflows:

```sh
picocalc-app breakout --once
picocalc-screenshot /home/neusse/screenshots/breakout-latest.png
```

Controls:

- Left/Right or `a`/`d`: move paddle.
- Space or Enter: launch ball or restart after game over.
- Backspace, Escape, `q`, or `Ctrl+F5`: exit.
