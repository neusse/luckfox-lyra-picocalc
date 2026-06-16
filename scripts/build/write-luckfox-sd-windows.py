#!/usr/bin/env python3
"""Write the Luckfox Lyra SD card layout to a Windows physical drive.

This is intentionally narrow and conservative:
- it only writes the GPT headers/partition table plus supplied filesystem images
- it verifies the expected Windows disk number, serial, USB bus, and approximate size
- it requires --yes-erase-disk
"""

from __future__ import annotations

import argparse
import binascii
import ctypes
import json
import os
import struct
import subprocess
import sys
import uuid
from pathlib import Path


SECTOR_SIZE = 512
ROOTFS_START = 65536
ROOTFS_SECTORS = 0x200000
ROOTFS_END = ROOTFS_START + ROOTFS_SECTORS - 1
OVERLAY_START = ROOTFS_END + 1
LINUX_FS_TYPE = uuid.UUID("0fc63daf-8483-4772-8e79-3d69d8477de4")


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ps_json(script: str) -> object:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def run_ps(script: str) -> None:
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True)


def gpt_guid_bytes(value: uuid.UUID) -> bytes:
    return value.bytes_le


def utf16le_name(name: str) -> bytes:
    raw = name.encode("utf-16le")
    return raw[:72].ljust(72, b"\0")


def protective_mbr(total_sectors: int) -> bytes:
    mbr = bytearray(SECTOR_SIZE)
    mbr[446] = 0x00
    mbr[447:450] = b"\x00\x02\x00"
    mbr[450] = 0xEE
    mbr[451:454] = b"\xff\xff\xff"
    mbr[454:458] = struct.pack("<I", 1)
    mbr[458:462] = struct.pack("<I", min(total_sectors - 1, 0xFFFFFFFF))
    mbr[510:512] = b"\x55\xaa"
    return bytes(mbr)


def partition_entry(type_guid: uuid.UUID, unique_guid: uuid.UUID, first: int, last: int, name: str) -> bytes:
    return b"".join(
        [
            gpt_guid_bytes(type_guid),
            gpt_guid_bytes(unique_guid),
            struct.pack("<Q", first),
            struct.pack("<Q", last),
            struct.pack("<Q", 0),
            utf16le_name(name),
        ]
    )


def make_partition_array(overlay_end: int) -> bytes:
    entries = bytearray(128 * 128)
    entries[0:128] = partition_entry(
        LINUX_FS_TYPE,
        uuid.uuid5(uuid.NAMESPACE_DNS, "luckfox-lyra-rootfs"),
        ROOTFS_START,
        ROOTFS_END,
        "rootfs",
    )
    entries[128:256] = partition_entry(
        LINUX_FS_TYPE,
        uuid.uuid5(uuid.NAMESPACE_DNS, "luckfox-lyra-overlay"),
        OVERLAY_START,
        overlay_end,
        "overlay",
    )
    return bytes(entries)


def gpt_header(
    current_lba: int,
    backup_lba: int,
    first_usable: int,
    last_usable: int,
    disk_guid: uuid.UUID,
    part_entries_lba: int,
    part_entries_crc: int,
) -> bytes:
    header = bytearray(SECTOR_SIZE)
    header[0:8] = b"EFI PART"
    header[8:12] = struct.pack("<I", 0x00010000)
    header[12:16] = struct.pack("<I", 92)
    header[24:32] = struct.pack("<Q", current_lba)
    header[32:40] = struct.pack("<Q", backup_lba)
    header[40:48] = struct.pack("<Q", first_usable)
    header[48:56] = struct.pack("<Q", last_usable)
    header[56:72] = gpt_guid_bytes(disk_guid)
    header[72:80] = struct.pack("<Q", part_entries_lba)
    header[80:84] = struct.pack("<I", 128)
    header[84:88] = struct.pack("<I", 128)
    header[88:92] = struct.pack("<I", part_entries_crc)
    crc = binascii.crc32(header[:92]) & 0xFFFFFFFF
    header[16:20] = struct.pack("<I", crc)
    return bytes(header)


def write_at(handle, offset: int, data: bytes) -> None:
    handle.seek(offset)
    handle.write(data)


def copy_image(handle, image_path: Path, offset: int, label: str) -> None:
    size = image_path.stat().st_size
    print(f"Writing {label}: {image_path} ({size:,} bytes) at offset {offset:,}")
    with image_path.open("rb") as src:
        handle.seek(offset)
        while True:
            chunk = src.read(8 * 1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--disk-number", type=int, required=True)
    parser.add_argument("--expected-serial", required=True)
    parser.add_argument("--expected-size-gb", type=float, required=True)
    parser.add_argument("--rootfs", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--yes-erase-disk", action="store_true")
    args = parser.parse_args()

    if os.name != "nt":
        print("This script must run on Windows.", file=sys.stderr)
        return 2
    if not args.yes_erase_disk:
        print("Refusing to run without --yes-erase-disk.", file=sys.stderr)
        return 2
    if not is_admin():
        print("Run this script from Administrator PowerShell.", file=sys.stderr)
        return 2
    if not args.rootfs.is_file():
        print(f"Missing rootfs image: {args.rootfs}", file=sys.stderr)
        return 2
    if not args.overlay.is_file():
        print(f"Missing overlay image: {args.overlay}", file=sys.stderr)
        return 2

    disk = ps_json(
        "$d = Get-Disk -Number %d; "
        "$d | Select-Object Number,FriendlyName,SerialNumber,BusType,PartitionStyle,"
        "OperationalStatus,IsOffline,IsReadOnly,Size,LogicalSectorSize | ConvertTo-Json"
        % args.disk_number
    )
    size_gb = round(int(disk["Size"]) / (1024**3), 2)
    print(json.dumps(disk, indent=2))

    if str(disk["SerialNumber"]).strip() != args.expected_serial:
        print("Refusing: disk serial does not match.", file=sys.stderr)
        return 2
    if str(disk["BusType"]) != "USB":
        print("Refusing: target disk is not USB.", file=sys.stderr)
        return 2
    if abs(size_gb - args.expected_size_gb) > 0.2:
        print(f"Refusing: disk size {size_gb} GiB does not match expected {args.expected_size_gb} GiB.", file=sys.stderr)
        return 2
    if int(disk.get("LogicalSectorSize") or SECTOR_SIZE) != SECTOR_SIZE:
        print("Refusing: only 512-byte logical sectors are supported.", file=sys.stderr)
        return 2

    total_sectors = int(disk["Size"]) // SECTOR_SIZE
    last_lba = total_sectors - 1
    first_usable = 34
    last_usable = last_lba - 33
    if OVERLAY_START > last_usable:
        print("Refusing: disk is too small for requested layout.", file=sys.stderr)
        return 2

    if args.rootfs.stat().st_size > ROOTFS_SECTORS * SECTOR_SIZE:
        print("Refusing: rootfs image is larger than the rootfs partition.", file=sys.stderr)
        return 2
    overlay_max = (last_usable - OVERLAY_START + 1) * SECTOR_SIZE
    if args.overlay.stat().st_size > overlay_max:
        print("Refusing: overlay image is larger than the overlay partition.", file=sys.stderr)
        return 2

    print("Taking disk offline for raw write...")
    run_ps(f"Set-Disk -Number {args.disk_number} -IsReadOnly $false; Set-Disk -Number {args.disk_number} -IsOffline $true")

    entries = make_partition_array(last_usable)
    entries_crc = binascii.crc32(entries) & 0xFFFFFFFF
    disk_guid = uuid.uuid5(uuid.NAMESPACE_DNS, "luckfox-lyra-sd-card")
    primary_header = gpt_header(1, last_lba, first_usable, last_usable, disk_guid, 2, entries_crc)
    backup_entries_lba = last_lba - 32
    backup_header = gpt_header(last_lba, 1, first_usable, last_usable, disk_guid, backup_entries_lba, entries_crc)

    drive_path = rf"\\.\PhysicalDrive{args.disk_number}"
    print(f"Opening {drive_path}")
    with open(drive_path, "r+b", buffering=0) as disk_handle:
        write_at(disk_handle, 0, protective_mbr(total_sectors))
        write_at(disk_handle, SECTOR_SIZE, primary_header)
        write_at(disk_handle, 2 * SECTOR_SIZE, entries)
        write_at(disk_handle, backup_entries_lba * SECTOR_SIZE, entries)
        write_at(disk_handle, last_lba * SECTOR_SIZE, backup_header)
        copy_image(disk_handle, args.rootfs, ROOTFS_START * SECTOR_SIZE, "rootfs")
        copy_image(disk_handle, args.overlay, OVERLAY_START * SECTOR_SIZE, "overlay")
        disk_handle.flush()

    print("Raw write completed.")
    print("Bringing disk online briefly so Windows refreshes the partition table...")
    run_ps(f"Set-Disk -Number {args.disk_number} -IsOffline $false")
    print("Done. Eject the SD card before inserting it into the Luckfox Lyra.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
