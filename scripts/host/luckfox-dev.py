#!/usr/bin/env python3
"""Small host-side development helper for the Luckfox PicoCalc.

The goal is a Thonny-like loop from Windows:
- edit files locally
- run Python on the PicoCalc as user `neusse`
- build simple C programs in WSL with the Luckfox cross compiler
- push and run binaries on the PicoCalc
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_ADB = Path(r"C:\Users\georg\AppData\Local\Android\Sdk\platform-tools\adb.exe")
DEFAULT_REMOTE_DIR = "/home/neusse/luckfox-dev"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_PYTHON_DIR = PROJECT_ROOT / "python"
REMOTE_PYTHON_DIR = f"{DEFAULT_REMOTE_DIR}/python"
WSL_PROJECT = "/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra"
TOOLCHAIN_BIN = (
    WSL_PROJECT
    + "/SDK/prebuilts/gcc/linux-x86/arm/"
    + "gcc-arm-10.3-2021.07-x86_64-arm-none-linux-gnueabihf/bin"
)
CC = "arm-none-linux-gnueabihf-gcc"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True)


def say(message: object) -> None:
    print(message, flush=True)


def capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True)


def adb_path() -> str:
    override = os.environ.get("ADB")
    if override:
        return override
    if DEFAULT_ADB.exists():
        return str(DEFAULT_ADB)
    return "adb"


def adb(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return run([adb_path(), *args], check=check)


def adb_shell(script: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return adb(["shell", script], check=check)


def q(value: str) -> str:
    return shlex.quote(value)


def sync_python_tree() -> None:
    if not LOCAL_PYTHON_DIR.exists():
        return

    say(f"Syncing {LOCAL_PYTHON_DIR} -> {REMOTE_PYTHON_DIR}")
    adb_shell(f"mkdir -p {q(DEFAULT_REMOTE_DIR)}")
    adb_shell(f"rm -rf {q(REMOTE_PYTHON_DIR)}")
    adb(["push", str(LOCAL_PYTHON_DIR), REMOTE_PYTHON_DIR])
    adb_shell(f"chown -R neusse:neusse {q(REMOTE_PYTHON_DIR)}")


def remote_python_command(remote_path: str, argv: list[str]) -> str:
    args = " ".join(q(arg) for arg in argv)
    return (
        "su - neusse -c "
        + q(
            "cd "
            + q(DEFAULT_REMOTE_DIR)
            + " && "
            + ". ~/venvs/nonroot/bin/activate 2>/dev/null || true; "
            + f"PYTHONPATH={REMOTE_PYTHON_DIR}${{PYTHONPATH:+:$PYTHONPATH}} "
            + "python "
            + q(remote_path)
            + (" " + args if args else "")
        )
    )


def cmd_status(_: argparse.Namespace) -> None:
    adb(["devices", "-l"])
    adb_shell(
        "echo ---device---; hostname; uname -a; "
        "echo ---network---; ip -4 addr show wlan0 2>/dev/null; "
        "echo ---python---; su - neusse -c 'python3 --version; "
        ". ~/venvs/nonroot/bin/activate 2>/dev/null && python -m pip --version || true'; "
        "echo ---swap---; cat /proc/swaps"
    )


def cmd_shell(_: argparse.Namespace) -> None:
    adb(["shell", "su - neusse"])


def cmd_push(args: argparse.Namespace) -> None:
    local = Path(args.local)
    remote = args.remote or f"{DEFAULT_REMOTE_DIR}/{local.name}"
    adb_shell(f"mkdir -p {q(str(Path(remote).parent))}; chown -R neusse:neusse {q(DEFAULT_REMOTE_DIR)}")
    adb(["push", str(local), remote])
    adb_shell(f"chown neusse:neusse {q(remote)}")


def cmd_runpy(args: argparse.Namespace) -> None:
    local = Path(args.file)
    remote = f"{DEFAULT_REMOTE_DIR}/{local.name}"
    sync_python_tree()
    say(f"Uploading {local} -> {remote}")
    adb_shell(f"mkdir -p {q(DEFAULT_REMOTE_DIR)}; chown -R neusse:neusse {q(DEFAULT_REMOTE_DIR)}")
    adb(["push", str(local), remote])
    adb_shell(f"chown neusse:neusse {q(remote)}")
    adb_shell(remote_python_command(remote, args.args))


def wsl_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    tail = str(resolved)[3:].replace("\\", "/")
    return f"/mnt/{drive}/{tail}"


def cmd_build_c(args: argparse.Namespace) -> None:
    src = Path(args.source)
    out = Path(args.output) if args.output else src.with_suffix("")
    src_wsl = wsl_path(src)
    out_wsl = wsl_path(out)
    extra = " ".join(shlex.quote(flag) for flag in args.cflags)
    script = (
        "set -euo pipefail; "
        f"export PATH={shlex.quote(TOOLCHAIN_BIN)}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; "
        f"{CC} {extra} {shlex.quote(src_wsl)} -o {shlex.quote(out_wsl)}"
    )
    say(f"Building {src} -> {out}")
    run(["wsl", "-d", "Ubuntu-22.04", "--", "bash", "-lc", script])
    say(out)


def cmd_runc(args: argparse.Namespace) -> None:
    src = Path(args.source)
    out = Path(args.output) if args.output else src.with_suffix("")
    cmd_build_c(argparse.Namespace(source=str(src), output=str(out), cflags=args.cflags))
    remote = f"{DEFAULT_REMOTE_DIR}/{out.name}"
    adb_shell(f"mkdir -p {q(DEFAULT_REMOTE_DIR)}; chown -R neusse:neusse {q(DEFAULT_REMOTE_DIR)}")
    adb(["push", str(out), remote])
    adb_shell(f"chown neusse:neusse {q(remote)}; chmod 755 {q(remote)}")
    program_args = ""
    say(f"Running {remote}")
    adb_shell("su - neusse -c " + q(f"cd {q(DEFAULT_REMOTE_DIR)} && ./{q(out.name)} {program_args}".strip()))


def cmd_runbin(args: argparse.Namespace) -> None:
    binary = Path(args.binary)
    remote = f"{DEFAULT_REMOTE_DIR}/{binary.name}"
    adb_shell(f"mkdir -p {q(DEFAULT_REMOTE_DIR)}; chown -R neusse:neusse {q(DEFAULT_REMOTE_DIR)}")
    say(f"Uploading {binary} -> {remote}")
    adb(["push", str(binary), remote])
    adb_shell(f"chown neusse:neusse {q(remote)}; chmod 755 {q(remote)}")
    program_args = " ".join(q(arg) for arg in args.args)
    say(f"Running {remote}")
    adb_shell("su - neusse -c " + q(f"cd {q(DEFAULT_REMOTE_DIR)} && ./{q(binary.name)} {program_args}".strip()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Luckfox PicoCalc development helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="show device status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("shell", help="open an adb shell as neusse")
    p.set_defaults(func=cmd_shell)

    p = sub.add_parser("push", help="push a file to the PicoCalc")
    p.add_argument("local")
    p.add_argument("remote", nargs="?")
    p.set_defaults(func=cmd_push)

    p = sub.add_parser("runpy", help="push and run a Python file as neusse")
    p.add_argument("file")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_runpy)

    p = sub.add_parser("build-c", help="cross-compile a C file in WSL")
    p.add_argument("source")
    p.add_argument("-o", "--output")
    p.add_argument("cflags", nargs=argparse.REMAINDER, help="extra compiler/linker flags")
    p.set_defaults(func=cmd_build_c)

    p = sub.add_parser("runc", help="cross-compile, push, and run a C file")
    p.add_argument("source")
    p.add_argument("-o", "--output")
    p.add_argument("cflags", nargs=argparse.REMAINDER, help="extra compiler/linker flags")
    p.set_defaults(func=cmd_runc)

    p = sub.add_parser("runbin", help="push and run an existing binary")
    p.add_argument("binary")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_runbin)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
