# PicoCalc Keyboard MCU Power And Backlight Notes

The PicoCalc keyboard controller is an I2C device at address `0x1f`. On the current Luckfox Lyra image, Linux binds it with the `picocalc-keyboard` kernel driver, so direct userspace reads with `i2cget` are blocked while the keyboard is active.

## Current Image Status

The first probe of the unmodified image showed:

- `/dev/i2c-0` exists.
- `i2cdetect -y 0` shows `UU` at `0x1f`, which means the kernel owns the keyboard MCU address.
- `/sys/bus/i2c/devices/0-001f/name` reports `picocalc-keyboard`.
- `/sys/firmware/picocalc` is not present.
- `/sys/class/power_supply` has no PicoCalc battery device.

Kernel `6.1.99 #7` added local sysfs support to the active
`picocalc-keyboard` driver for battery and backlight controls. Kernel
`6.1.99 #1` from the deterministic shutdown-hook build stores the PicoCalc
power-off delay and sends the MCU power-off command from the kernel shutdown
path on Linux halt/poweroff. Reboot skips the MCU power-off command.

```text
/sys/bus/i2c/devices/0-001f/battery_raw
/sys/bus/i2c/devices/0-001f/battery_percent
/sys/bus/i2c/devices/0-001f/battery_status
/sys/bus/i2c/devices/0-001f/screen_backlight
/sys/bus/i2c/devices/0-001f/keyboard_backlight
/sys/bus/i2c/devices/0-001f/poweroff_delay
```

Verified values after booting the shutdown-hook kernel:

```text
uname=Linux picocalc 6.1.99 #1 SMP PREEMPT Thu Jan 1 00:00:00 UTC 2026 armv7l GNU/Linux
battery_raw=100
battery_percent=100
battery_status=Full
screen_backlight=32
keyboard_backlight=0
poweroff_delay=8
```

The helper script `/usr/local/sbin/picocalc-mcu` wraps those sysfs paths. SSH logins on the current image use `PATH=/usr/bin:/usr/sbin`, so the runtime install also creates:

```text
/usr/bin/picocalc-mcu -> /usr/local/sbin/picocalc-mcu
```

Useful commands:

```sh
picocalc-mcu status
picocalc-mcu battery
picocalc-mcu screen-backlight
picocalc-mcu keyboard-backlight
picocalc-mcu screen-backlight 92
picocalc-mcu keyboard-backlight 120
picocalc-mcu poweroff 8
shutdown
```

Battery reads work as the non-root `neusse` user from SSH. Backlight writes currently require root because the sysfs attributes are kernel-owned writable attributes.
The poweroff delay write also requires root. `picocalc-mcu poweroff N` sets the
delay used by the next Linux halt/poweroff. `shutdown` is the user-facing full
PicoCalc shutdown command; BusyBox `poweroff` remains the Linux-only halt path.

## Known Hardware Protocol

Community and upstream notes identify these keyboard MCU registers:

| Register | Name | Purpose |
| --- | --- | --- |
| `0x05` | `REG_ID_BKL` | Backlight control, used by sample code and forum driver notes |
| `0x09` | `REG_ID_FIF` | Keyboard FIFO/key event register |
| `0x0a` | `REG_ID_BK2` | Second backlight register, likely display/screen backlight |
| `0x0b` | `REG_ID_BAT` | Battery percent |
| `0x0e` | `REG_ID_OFF` | Power-off request register on newer keyboard firmware |
| `0x80` bit | `REG_WRITE` | Write flag used with writable commands |

The battery read protocol sends register `0x0b` to address `0x1f` and reads two bytes back. Upstream PicoCalc keyboard firmware code returns `[register, current_bat_pcnt]`, so byte 1 is the useful battery value.

The power-off protocol writes a delay value to register `0x0e`. The local
kernel patch uses the same write-flagged register helper as the backlight
controls, so the I2C command byte is `0x0e | 0x80` and the value byte is the
delay in seconds. Valid delay values are `0..63`. The sysfs attribute stores
that delay; the driver writes `REG_ID_OFF` during the kernel shutdown callback
for halt/poweroff and skips the write during reboot.

## Existing Community Work

There is already community work for this:

- The ClockworkPi forum says battery percent is readable from keyboard register `0x0b`, but older keyboard firmware could crash when queried.
- A later Luckfox Lyra PicoCalc driver/firmware update reportedly exposed battery percent and keyboard backlight through `/sys/firmware/picocalc/keyboard_backlight`.
- The newer `meta-picocalc`/Calculinux driver direction appears to model this as normal Linux devices: an MFD driver, a `power_supply` battery device, display backlight, and keyboard LED/backlight.

## Recommended Path

Do not make a standalone userspace I2C polling tool as the first implementation. The keyboard driver already owns the bus address, and unbinding it just to run `i2cget` risks losing keyboard input or hitting the old firmware crash path.

Use a kernel-side implementation instead:

1. Patch the current `picocalc-keyboard` driver to serialize I2C access with a mutex. Done in `patches/picocalc-keyboard-mcu-sysfs.patch`.
2. Add read-only sysfs attributes for battery, using register `0x0b`. Done.
3. Add read/write sysfs attributes for screen and keyboard backlight. Done.
4. Add a root-writable sysfs attribute for MCU power-off delay. Done.
5. Add a kernel shutdown callback that sends `REG_ID_OFF` during halt/poweroff, not reboot. Done.
6. Rebuild and boot the updated kernel through `scripts/build-kernel.ps1 kernel-stage`. Done with the deterministic shutdown-hook kernel.
7. Confirm the sysfs value works repeatedly without keyboard dropouts. Done for repeated battery reads and non-destructive `poweroff_delay` write/read/restore. Real power cut should be tested intentionally from the console.
7. Later, replace the local sysfs attributes with a cleaner upstream-style split using Linux `power_supply`, `backlight`, and LED interfaces.

## Power-Off Kernel Install

The kernel-only power-off image was built from the WSL ext4 SDK tree after
patching the actual compiled source at:

```text
/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK/kernel-6.1/drivers/input/keyboard/picocalc-keyboard.c
```

Build command:

```powershell
.\scripts\build-kernel.ps1 kernel-stage
```

Artifact:

```text
artifacts/picocalc-keyboard-mcu-shutdown-hook-zboot.img
sha256: c3a0bb3eda9a1cd8a090684fc6d044df68ddec4cdd40484d3b3d728720adba69
```

Boot partition backup before install:

```text
/mnt/sdcard/backups/boot-before-shutdown-hook-20260619-192731.img
sha256: 3860f65387ec2c8af7f61b2d225f98ce5a27eafc0a16cd5bc4091479d70878d3
```

Install wrote only `/dev/mmcblk0p2`; rootfs and overlay were not rewritten.
No PicoCalc BIOS/keyboard MCU firmware was flashed.

## Minimal Target

The immediate milestone exposes:

```text
/sys/bus/i2c/devices/0-001f/battery_percent
/sys/bus/i2c/devices/0-001f/battery_raw
/sys/bus/i2c/devices/0-001f/battery_status
```

`battery_percent` should decode normal values as `0..100`. If the firmware returns the common charging encoding above `100`, keep the undecoded value available as `battery_raw` and report `Charging` through `battery_status`.

## Sources

- ClockworkPi PicoCalc GitHub issue: battery register sample and keyboard MCU register IDs: <https://github.com/clockworkpi/PicoCalc/issues/20>
- ClockworkPi forum: battery command `0x0b`, older keyboard firmware crash warning, and Alt+B battery LED shortcut: <https://forum.clockworkpi.com/t/reading-battery-level-from-mmbasic/16433>
- ClockworkPi forum: Luckfox Lyra driver note exposing battery/backlight through sysfs: <https://forum.clockworkpi.com/t/luckfox-lyra-on-picocalc/16280/164>
- ClockworkPi forum Luckfox Lyra thread, later driver discussion: <https://forum.clockworkpi.com/t/luckfox-lyra-on-picocalc/16280?page=29>
