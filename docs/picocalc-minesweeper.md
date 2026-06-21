# PicoCalc Minesweeper

`picocalc_minesweeper.py` is the Luckfox Lyra framebuffer port of
`fjam_minesweeper.py` from:

```text
/mnt/sdcard/backup_2026-02-01_181033
```

The port keeps the FJam-style PicoCalc layout:

- 16x16 board.
- 16-pixel cells.
- Easy, Medium, and Hard mine counts.
- First reveal is safe.
- Flags, flood reveal, win/loss detection, and timer.

Run it:

```sh
picocalc-minesweeper
```

It is also available through:

```sh
picocalc-app minesweeper
minesweeper
```

From SSH or ADB, the app detaches to `/dev/tty1` and uses the physical
PicoCalc screen and keyboard. For screenshot workflows:

```sh
picocalc-minesweeper --once
picocalc-screenshot /home/neusse/screenshots/minesweeper-latest.png
```

Controls:

- Menu: Up/Down selects difficulty, Enter starts, Back exits.
- Game: arrows move, Enter or Space reveals, `f` toggles a flag.
- Back returns to the menu.
- `Ctrl+F5` or `q` exits cleanly.
