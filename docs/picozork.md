# PicoZork

`examples/python/picocalc_zork.py` runs Z-machine version 3 story files on the
Luckfox Lyra PicoCalc terminal. It is a Linux terminal port of the
CircuitPython CPZ Machine shell, using the existing `zmachine_opcodes.py`
interpreter logic with a new stdin/stdout host layer.

The default story path is:

```sh
/mnt/sdcard/cpz/stories
```

The default save path is:

```sh
/mnt/sdcard/cpz/saves
```

The launcher supports both SSH and the physical PicoCalc console:

```sh
picocalc-app zork --list
picocalc-app zork
picocalc-app zork zork1
```

On SSH, Zork runs in the SSH terminal and uses the terminal width. On the
physical PicoCalc console, it switches to the installed `picofont 40` font by
default, wraps text to 40 columns, and uses a CPZ-style green theme: a
black-on-green status/title bar at the top, a blank spacer row, and bright green
game text below. Use `--font none` to skip the font switch, or `--font original`
to return to the kernel 6x8 font before running.

Color can be controlled explicitly:

```sh
zork --color auto
zork --color always
zork --color never
```

Story filenames ending in `.z3`, `.z5`, `.z8`, `.dat`, or `.zip` are listed.
The historical Zork repositories use `.zip` for Z-machine story files, not
necessarily compressed archives.

## Installation

Sync the project Python tree and app script to the device:

```powershell
python .\tools\luckfox-dev.py runpy .\examples\python\picocalc_zork.py --list
```

Install or refresh the launcher:

```sh
cp scripts/device/picocalc-app /usr/local/bin/picocalc-app
chmod 755 /usr/local/bin/picocalc-app
ln -sf /usr/local/bin/picocalc-app /usr/bin/zork
ln -sf /usr/local/bin/picocalc-app /usr/bin/picozork
ln -sf /usr/local/bin/picocalc-app /usr/bin/picocalc-zork
```

## Sources

Zork I, II, and III source repositories are maintained under
`historicalsource` on GitHub, with Microsoft announcing the MIT release in
November 2025. The game source is open; packaging, marketing assets, and
trademarks are separate.
