# Luckfox Development Helper

`scripts/host/luckfox-dev.py` is a small host-side helper for a Thonny-like workflow:

- edit files on Windows
- run Python on the PicoCalc as `neusse`
- cross-compile simple C programs in WSL
- push and run binaries on the PicoCalc

## Status

```powershell
python .\scripts\host\luckfox-dev.py status
```

## Python

```powershell
python .\scripts\host\luckfox-dev.py runpy .\examples\python\hello_luckfox.py
```

The script is uploaded to:

```text
/home/neusse/luckfox-dev/
```

It runs as user `neusse` and activates `~/venvs/nonroot` when available.

## C

```powershell
python .\scripts\host\luckfox-dev.py runc .\examples\c\hello_luckfox.c
```

This cross-compiles in WSL using the Luckfox SDK toolchain:

```text
arm-none-linux-gnueabihf-gcc
```

Then it pushes and runs the binary on the PicoCalc as `neusse`.

## Shell

```powershell
python .\scripts\host\luckfox-dev.py shell
```

This opens an ADB shell as `neusse`.
