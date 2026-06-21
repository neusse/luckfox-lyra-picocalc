#!/usr/bin/env python3
import struct
import sys
from pathlib import Path


FDT_MAGIC = 0xD00DFEED
FDT_HEADER = ">10I"
FDT_HEADER_SIZE = struct.calcsize(FDT_HEADER)


def normalize(path: Path) -> bool:
    blob = bytearray(path.read_bytes())
    if len(blob) < FDT_HEADER_SIZE:
        raise ValueError(f"{path} is too small to be an FDT/FIT image")

    (
        magic,
        totalsize,
        off_dt_struct,
        _off_dt_strings,
        off_mem_rsvmap,
        _version,
        _last_comp_version,
        _boot_cpuid_phys,
        _size_dt_strings,
        _size_dt_struct,
    ) = struct.unpack_from(FDT_HEADER, blob, 0)

    if magic != FDT_MAGIC:
        raise ValueError(f"{path} does not start with FDT magic")
    if totalsize > len(blob):
        raise ValueError(f"{path} FDT totalsize exceeds file size")
    if not (FDT_HEADER_SIZE <= off_mem_rsvmap <= off_dt_struct <= totalsize):
        raise ValueError(f"{path} has invalid FDT offsets")

    zeros = b"\0" * (off_dt_struct - off_mem_rsvmap)
    old = bytes(blob[off_mem_rsvmap:off_dt_struct])
    if old == zeros:
        return False

    # Rockchip mkimage can leave non-deterministic bytes in this reserve-map
    # span. This FIT does not declare memory reservations, so the canonical
    # reserve map is only the all-zero terminator.
    blob[off_mem_rsvmap:off_dt_struct] = zeros
    path.write_bytes(blob)
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {Path(argv[0]).name} IMAGE", file=sys.stderr)
        return 2

    path = Path(argv[1])
    changed = normalize(path)
    if changed:
        print(f"normalized FIT reserve map: {path}")
    else:
        print(f"FIT reserve map already normalized: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
