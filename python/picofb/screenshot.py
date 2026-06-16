"""Framebuffer screenshot helpers for PicoFB."""

from __future__ import annotations

import argparse
import binascii
import struct
import time
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Screenshot:
    width: int
    height: int
    rgb: bytes

    def to_png(self) -> bytes:
        return write_png(self.rgb, self.width, self.height)

    def save_png(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(self.to_png())
        return output


def rgb565_to_rgb888(value: int) -> tuple[int, int, int]:
    red = (value >> 11) & 0x1F
    green = (value >> 5) & 0x3F
    blue = value & 0x1F
    return (
        (red << 3) | (red >> 2),
        (green << 2) | (green >> 4),
        (blue << 3) | (blue >> 2),
    )


def write_png(rgb: bytes, width: int, height: int) -> bytes:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    expected = width * height * 3
    if len(rgb) != expected:
        raise ValueError(f"rgb buffer length must be {expected} bytes")

    rows = bytearray()
    row_size = width * 3
    for y in range(height):
        start = y * row_size
        rows.append(0)
        rows.extend(rgb[start : start + row_size])

    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=6)),
            _png_chunk(b"IEND", b""),
        ]
    )


def capture_framebuffer(
    framebuffer: str | Path = "/dev/fb0",
    *,
    sysfs_root: str | Path = "/sys/class/graphics",
    fb_name: str | None = None,
) -> Screenshot:
    fb_path = Path(framebuffer)
    name = fb_name if fb_name is not None else fb_path.name
    metadata_root = Path(sysfs_root) / name

    width, height = _read_virtual_size(metadata_root / "virtual_size")
    bpp = _read_int(metadata_root / "bits_per_pixel")
    stride = _read_int(metadata_root / "stride")

    if bpp != 16:
        raise ValueError(f"only 16-bpp RGB565 framebuffers are supported (got {bpp})")
    row_bytes = width * 2
    if stride < row_bytes:
        raise ValueError(f"framebuffer stride {stride} is smaller than row bytes {row_bytes}")

    raw = fb_path.read_bytes()
    required = ((height - 1) * stride) + row_bytes
    if len(raw) < required:
        raise ValueError(f"framebuffer data is too small: need {required}, got {len(raw)}")

    rgb = bytearray(width * height * 3)
    output_offset = 0
    for y in range(height):
        row_offset = y * stride
        for x in range(width):
            offset = row_offset + (x * 2)
            value = raw[offset] | (raw[offset + 1] << 8)
            red, green, blue = rgb565_to_rgb888(value)
            rgb[output_offset : output_offset + 3] = bytes([red, green, blue])
            output_offset += 3

    return Screenshot(width, height, bytes(rgb))


def save_screenshot(
    output: str | Path | None = None,
    *,
    framebuffer: str | Path = "/dev/fb0",
    sysfs_root: str | Path = "/sys/class/graphics",
    fb_name: str | None = None,
) -> Path:
    output_path = Path(output) if output is not None else _default_output_path()
    shot = capture_framebuffer(framebuffer, sysfs_root=sysfs_root, fb_name=fb_name)
    return shot.save_png(output_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture a Linux RGB565 framebuffer as PNG.")
    parser.add_argument("output", nargs="?", help="output PNG path")
    parser.add_argument("--fb", default="/dev/fb0", help="framebuffer device path")
    parser.add_argument(
        "--sysfs-root",
        default="/sys/class/graphics",
        help="graphics sysfs root",
    )
    parser.add_argument("--fb-name", default=None, help="framebuffer sysfs name")
    args = parser.parse_args(argv)

    output = save_screenshot(
        args.output,
        framebuffer=args.fb,
        sysfs_root=args.sysfs_root,
        fb_name=args.fb_name,
    )
    print(output)
    return 0


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = binascii.crc32(kind)
    checksum = binascii.crc32(payload, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def _default_output_path() -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return Path.home() / "screenshots" / f"picocalc-{timestamp}.png"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="ascii").strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"framebuffer metadata missing: {path}") from exc


def _read_int(path: Path) -> int:
    value = _read_text(path)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"invalid framebuffer metadata in {path}: {value!r}") from exc


def _read_virtual_size(path: Path) -> tuple[int, int]:
    value = _read_text(path)
    try:
        width_text, height_text = value.split(",", 1)
        width = int(width_text)
        height = int(height_text)
    except ValueError as exc:
        raise ValueError(f"invalid framebuffer virtual_size in {path}: {value!r}") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid framebuffer virtual_size in {path}: {value!r}")
    return width, height


if __name__ == "__main__":
    raise SystemExit(main())
