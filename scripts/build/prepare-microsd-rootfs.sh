#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  sudo ./scripts/prepare-microsd-rootfs.sh /dev/sdX /path/to/rootfs.ext2 --yes-erase-disk

This destroys all data on /dev/sdX.

Layout created:
  GPT
  partition 1: PARTLABEL=rootfs, starts at sector 65536, size 0x200000 sectors (1 GiB)
  partition 2: PARTLABEL=overlay, uses the rest of the card

The rootfs image is written to partition 1.
Partition 2 is formatted ext4 with label "overlay".
EOF
}

if [[ $# -ne 3 || "${3:-}" != "--yes-erase-disk" ]]; then
  usage >&2
  exit 2
fi

disk="$1"
rootfs_img="$2"

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run this script with sudo." >&2
  exit 1
fi

if [[ ! -b "$disk" ]]; then
  echo "ERROR: disk is not a block device: $disk" >&2
  exit 1
fi

if [[ ! -r "$rootfs_img" ]]; then
  echo "ERROR: rootfs image is not readable: $rootfs_img" >&2
  exit 1
fi

case "$disk" in
  /dev/sd[a-z]|/dev/vd[a-z]|/dev/xvd[a-z]) ;;
  *)
    echo "ERROR: refusing unexpected disk path: $disk" >&2
    echo "Pass a whole disk like /dev/sdX, not a partition." >&2
    exit 1
    ;;
esac

if mount | grep -q "^$disk"; then
  echo "ERROR: one or more partitions from $disk are mounted. Unmount them first." >&2
  mount | grep "^$disk" >&2 || true
  exit 1
fi

echo "About to erase and repartition:"
lsblk -o NAME,SIZE,MODEL,TRAN,TYPE,MOUNTPOINTS "$disk"
echo
echo "Rootfs image:"
ls -lh "$rootfs_img"
echo

rootfs_start=65536
rootfs_size=2097152
rootfs_end=$((rootfs_start + rootfs_size - 1))
overlay_start=$((rootfs_end + 1))

sgdisk --zap-all "$disk"
sgdisk \
  --new=1:${rootfs_start}:${rootfs_end} --typecode=1:8300 --change-name=1:rootfs \
  --new=2:${overlay_start}:0 --typecode=2:8300 --change-name=2:overlay \
  "$disk"
partprobe "$disk" || true
udevadm settle || true
sleep 2

rootfs_part="${disk}1"
overlay_part="${disk}2"

if [[ ! -b "$rootfs_part" || ! -b "$overlay_part" ]]; then
  echo "ERROR: expected partitions were not found: $rootfs_part $overlay_part" >&2
  lsblk "$disk" >&2
  exit 1
fi

dd if="$rootfs_img" of="$rootfs_part" bs=4M conv=fsync status=progress
e2fsck -fy "$rootfs_part"
mkfs.ext4 -F -L overlay "$overlay_part"
sync

echo
echo "Final layout:"
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTLABEL,UUID,MOUNTPOINTS "$disk"
