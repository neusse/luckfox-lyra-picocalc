# Bring-Up Journal

This is the cleaned version of the project journey. It intentionally omits API
keys, Wi-Fi passwords, and raw personal network details.

## 1. Baseline

The target was a Luckfox Lyra Model B installed in a ClockworkPi PicoCalc. The
useful upstream starting point was the PicoCalc-specific Luckfox Lyra build flow
rather than a generic Lyra image.

We kept two upstream references:

- `benklop/picocalc-luckfox-lyra` as the active build baseline.
- `nekocharm/picocalc-luckfox-lyra` as a reference integration.

The SDK would not build correctly from a Windows-mounted path, so the real build
workspace moved to WSL ext4:

```text
/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra
```

## 2. Firmware And Boot

The build produced a Luckfox SDMMC/TF-style firmware package from the SDK. The
Lyra B storage behavior was confusing because the board has SPI NAND support but
the successful bring-up used the removable microSD path.

The device eventually booted to a PicoCalc login prompt from the SD-rootfs
layout. ADB and SSH became available, giving us a reliable development loop.

## 3. Python Runtime

Python 3.11 was present, but several pieces needed repair:

- `pip` was installed through `ensurepip`.
- A non-root Python environment was created for the `neusse` user.
- PATH handling was fixed so `~/.local/bin` and `~/bin` are usable.
- Python curses support was repaired.
- Python package imports from the synced project tree were normalized with the
  `picocalc-app` launcher.

## 4. Wi-Fi

The connected USB Wi-Fi adapter did not work with the existing `rtl8xxxu` path.
The working module was `88XXau.ko`, built from the aircrack-ng `rtl8812au`
driver against the same SDK kernel source and compiler used by the running
kernel.

After installing the module and boot scripts, `wlan0` appeared and survived
reboot.

## 5. Keyboard MCU And Battery

The PicoCalc keyboard controller was owned by the kernel at I2C address `0x1f`,
so userspace reads were blocked. The kernel keyboard driver was patched instead.

The local patch exposes battery and backlight state through sysfs:

```text
battery_raw
battery_percent
battery_status
screen_backlight
keyboard_backlight
```

The corrected kernel booted as `6.1.99 #7`.

## 6. Framebuffer Graphics

PicoFB was written as a small Python RGB565 framebuffer library for `/dev/fb0`.
It supports primitives, bitmap text, BMP icons, screenshots, and TrueType text
through the available system font stack.

This made it possible to build demos and the weather dashboard without a window
system.

## 7. Weather Dashboard

The weather app became the main proof that the stack was usable:

- OpenWeather current conditions and forecast.
- BMP weather icons.
- Battery percent.
- Pacific clock and date.
- Five-minute weather refresh.
- Thirty-second clock redraw.
- Loud failure if required icons are missing.

The launcher prevents starting duplicate copies that would fight over the
PicoCalc console.

## 8. Utilities

Device utilities were added for:

- framebuffer permissions
- screenshots
- NTP clock sync
- SD-card mount/eject
- keyboard MCU status/control
- Wi-Fi module loading
- swap file setup
- boot/login banner IP display

Together these turned the board from a boot experiment into a usable handheld
Linux target.
