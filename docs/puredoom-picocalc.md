# PureDOOM PicoCalc Port

This note records the first native PureDOOM install for the Luckfox Lyra
PicoCalc.

## Upstream

Source:

```text
https://github.com/Daivuk/PureDOOM
```

The project is a single-header DOOM core. It does not provide a PicoCalc
frontend, so this tree adds a small SDL2/DirectFB frontend:

```text
examples/c/picocalc_puredoom_sdl.c
```

The first build intentionally disables audio. It renders video and handles the
PicoCalc keyboard through SDL2/DirectFB.

## Build

Clone/update upstream into:

```text
downloads/source/PureDOOM
```

Build from WSL:

```sh
make puredoom-build
```

Output:

```text
artifacts/puredoom/picocalc-puredoom
```

The Makefile uses the Buildroot ARM toolchain from:

```text
/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK
```

## Device Install

Installed files:

```text
/usr/libexec/picocalc/puredoom
/usr/bin/puredoom
/usr/share/puredoom/doom1.wad
```

The binary is installed setuid-root, matching the chess frontend pattern, so
SDL2/DirectFB can switch VT/input mode on this image:

```sh
chown root:root /usr/libexec/picocalc/puredoom
chmod 4755 /usr/libexec/picocalc/puredoom
```

The wrapper starts the game on `/dev/tty1` when launched from SSH or ADB:

```sh
puredoom
```

If it is already running, the wrapper prints the active PID instead of starting
a duplicate.

## Controls

- Up/Down arrows: forward/back.
- Left/Right arrows: turn.
- `w`/`s`: forward/back aliases.
- `a`/`d`: strafe left/right.
- `e`: use/open.
- Ctrl or Enter: fire.
- Shift: run.
- Escape: DOOM menu.
- `Ctrl+F5`: exit the PicoCalc frontend.

## Current Status

Verified on the PicoCalc framebuffer with the shareware `doom1.wad` included in
the upstream PureDOOM repository. The smoke test rendered live gameplay on the
320x320 display.

Runtime observed during the smoke test:

```text
VmRSS:   ~12 MB
Threads: 10
```

Known gaps:

- Audio is disabled.
- The app is registered in `picocalc-app` as `doom`/`puredoom` and in the
  graphical launcher as `doom`.
- The first frontend uses SDL2/DirectFB rather than a custom direct framebuffer
  path.
