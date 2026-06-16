#!/usr/bin/env python3
"""Set system time from NTP without external Python packages."""

import socket
import struct
import subprocess
import sys
import time


NTP_DELTA = 2_208_988_800
SERVERS = (
    "time.cloudflare.com",
    "pool.ntp.org",
    "time.google.com",
)


def ntp_time(server: str, timeout: float = 5.0) -> float:
    packet = b"\x1b" + 47 * b"\0"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(packet, (server, 123))
        data, _ = sock.recvfrom(48)

    if len(data) < 48:
        raise RuntimeError("short NTP response")

    seconds, fraction = struct.unpack("!II", data[40:48])
    return seconds - NTP_DELTA + fraction / 2**32


def set_time(unix_time: float) -> None:
    if hasattr(time, "clock_settime"):
        time.clock_settime(time.CLOCK_REALTIME, unix_time)
        return

    stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(unix_time))
    subprocess.check_call(["date", "-u", "-s", stamp])


def main() -> int:
    last_error = None
    for server in SERVERS:
        try:
            value = ntp_time(server)
            set_time(value)
            print(time.strftime("time set from " + server + ": %Y-%m-%d %H:%M:%S UTC", time.gmtime(value)))
            return 0
        except Exception as exc:
            last_error = exc
            print(f"{server}: {exc}", file=sys.stderr)

    print(f"failed to set time: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
