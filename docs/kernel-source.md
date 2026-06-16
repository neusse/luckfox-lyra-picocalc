# Kernel Source

The working kernel is the Luckfox Lyra SDK kernel tree used through the
PicoCalc-specific build flow:

```text
/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK/kernel-6.1
```

The active build baseline was:

```text
https://github.com/benklop/picocalc-luckfox-lyra
```

The reference integration was:

```text
https://github.com/nekocharm/picocalc-luckfox-lyra
```

The running kernel verified on the device was:

```text
Linux picocalc 6.1.99 #7 SMP PREEMPT Tue Jun 16 15:04:03 UTC 2026 armv7l
```

The keyboard MCU patch in this repository modifies:

```text
drivers/input/keyboard/picocalc-keyboard.c
```

Patch file:

```text
patches/picocalc-keyboard-mcu-sysfs.patch
```

That patch adds sysfs access for:

- `battery_raw`
- `battery_percent`
- `battery_status`
- `screen_backlight`
- `keyboard_backlight`

The build used the Luckfox SDK ARM GCC 10.3 toolchain, matching the running
kernel module build environment.
