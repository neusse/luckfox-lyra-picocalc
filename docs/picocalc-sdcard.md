# PicoCalc SD Card Slot

The PicoCalc removable SD slot is already visible to the Luckfox Lyra image.

Current live mapping:

- Boot/root card: `/dev/mmcblk0`
- Removable PicoCalc slot: `/dev/mmcblk1`
- Default removable partition: `/dev/mmcblk1p1`
- Default mountpoint: `/mnt/sdcard`
- Kernel path: SPI-backed MMC host at `spi1.0`

The image already supports useful removable-card filesystems:

- `vfat`
- `exfat`
- `ntfs3`
- `ext4`

## Helper

The device helper is:

```sh
/usr/local/sbin/picocalc-sdcard
```

Source copy in this repo:

```text
scripts/device/picocalc-sdcard
```

Commands:

```sh
/usr/local/sbin/picocalc-sdcard status
/usr/local/sbin/picocalc-sdcard mount
/usr/local/sbin/picocalc-sdcard umount
/usr/local/sbin/picocalc-sdcard eject
/usr/local/sbin/picocalc-sdcard rescan
```

`eject` means `sync`, unmount, and report that it is safe to physically remove the SD card. The slot does not expose a software tray or obvious MMC remove/rescan control, so this is not a powered eject.

## Install From Host

```powershell
$adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
& $adb push .\scripts\device\picocalc-sdcard /usr/local/sbin/picocalc-sdcard
& $adb shell "chmod 755 /usr/local/sbin/picocalc-sdcard"
& $adb shell "/usr/local/sbin/picocalc-sdcard status"
```

## Notes

- Do not use this helper on `/dev/mmcblk0`; that is the boot/root card.
- Run `/usr/local/sbin/picocalc-sdcard eject` before physically removing the card.
- After inserting a new card, run `/usr/local/sbin/picocalc-sdcard rescan` and then `/usr/local/sbin/picocalc-sdcard mount`.
