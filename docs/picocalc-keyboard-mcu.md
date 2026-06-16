# PicoCalc Keyboard MCU Power And Backlight Notes

The PicoCalc keyboard controller is an I2C device at address `0x1f`. On the current Luckfox Lyra image, Linux binds it with the `picocalc-keyboard` kernel driver, so direct userspace reads with `i2cget` are blocked while the keyboard is active.

## Current Image Status

The first probe of the unmodified image showed:

- `/dev/i2c-0` exists.
- `i2cdetect -y 0` shows `UU` at `0x1f`, which means the kernel owns the keyboard MCU address.
- `/sys/bus/i2c/devices/0-001f/name` reports `picocalc-keyboard`.
- `/sys/firmware/picocalc` is not present.
- `/sys/class/power_supply` has no PicoCalc battery device.

Kernel `6.1.99 #7` adds local sysfs support to the active `picocalc-keyboard` driver:

```text
/sys/bus/i2c/devices/0-001f/battery_raw
/sys/bus/i2c/devices/0-001f/battery_percent
/sys/bus/i2c/devices/0-001f/battery_status
/sys/bus/i2c/devices/0-001f/screen_backlight
/sys/bus/i2c/devices/0-001f/keyboard_backlight
```

Verified values after booting kernel `#7`:

```text
battery_raw=100
battery_percent=100
battery_status=Full
screen_backlight=92
keyboard_backlight=120
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
```

Battery reads work as the non-root `neusse` user from SSH. Backlight writes currently require root because the sysfs attributes are kernel-owned writable attributes.

## Known Hardware Protocol

Community and upstream notes identify these keyboard MCU registers:

| Register | Name | Purpose |
| --- | --- | --- |
| `0x05` | `REG_ID_BKL` | Backlight control, used by sample code and forum driver notes |
| `0x09` | `REG_ID_FIF` | Keyboard FIFO/key event register |
| `0x0a` | `REG_ID_BK2` | Second backlight register, likely display/screen backlight |
| `0x0b` | `REG_ID_BAT` | Battery percent |
| `0x80` bit | `REG_WRITE` | Write flag used with writable commands |

The battery read protocol sends register `0x0b` to address `0x1f` and reads two bytes back. Upstream PicoCalc keyboard firmware code returns `[register, current_bat_pcnt]`, so byte 1 is the useful battery value.

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
4. Rebuild and boot the updated kernel. Done with kernel `6.1.99 #7`.
5. Confirm the sysfs value works repeatedly without keyboard dropouts. Done for repeated battery reads.
6. Later, replace the local sysfs attributes with a cleaner upstream-style split using Linux `power_supply`, `backlight`, and LED interfaces.

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
