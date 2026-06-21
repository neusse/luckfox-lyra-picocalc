# Buildroot Migration Change Map

Last audited: 2026-06-18

Target audited:

```text
Board:      Luckfox Lyra Model B in ClockworkPi PicoCalc
Rootfs:     Buildroot 2024.02
Kernel:     Linux 6.1.99 #1 armv7l
Toolchain:  arm-none-linux-gnueabihf-gcc 10.3-2021.07
User app:   /home/neusse/luckfox-dev
```

This document records runtime changes made after the base Luckfox/PicoCalc
Buildroot image booted. Its purpose is to make a future newer Buildroot image
rebuildable without rediscovering each fix.

Guiding rule for migration: Debian ARMHF grafts are temporary bring-up repairs.
In a clean image, prefer native Buildroot packages or recipes over copied Debian
files.

## 1. Debian ARMHF Runtime Grafts

These files were copied from Debian or Ubuntu ARMHF packages onto the Buildroot
image to unblock missing runtime features.

### Source Packages

Downloaded packages currently staged under `downloads/runtime-libs/armhf/`:

```text
40B3BD0D556EAEF042DB2BAD4D0E4FDE9BC552A1DD7F527D9E9EE41996C08F64  downloads/runtime-libs/armhf/htop/htop_3.2.2-2_armhf.deb
E5D36F7A39436FA94118617F8954FE0E43FF3B88EBA25209390E453868A38A06  downloads/runtime-libs/armhf/htop/libnl-3-200_3.7.0-0.2+b1_armhf.deb
97AD97C156EE41386183144F7B64BB02A62CEB15CE1175B6412BCCC054B9A56A  downloads/runtime-libs/armhf/htop/libnl-genl-3-200_3.7.0-0.2+b1_armhf.deb
BFD1D89F833C09A28B062EE916495CF69649CA2BF529532476C7B69D75D24909  downloads/runtime-libs/armhf/htop/ncurses-base_6.4-4_all.deb
5F8923D63456B4FA8FDD0FA5B24D9745A34C68D7D74E7A9BF4993F5E5DBC0749  downloads/runtime-libs/armhf/libgfortran5_12.3.0-1ubuntu1~22.04.3_armhf.deb
DED4916E2807B6F479C940FAAD42476AB4E101D16132A4B2C73F251F5288739F  downloads/runtime-libs/armhf/libncursesw6_6.4-4_armhf.deb
9A7CB9B6882877D056EFF6CA52FE7DB9FFD73158467DFC3F4A03F2479E04104D  downloads/runtime-libs/armhf/libopenblas0-pthread_0.3.20+ds-1_armhf.deb
55E47FF513894C8C562B41A306F32EFCF2B989BBCCF57A8BE5D4D66B1FA6AF2D  downloads/runtime-libs/armhf/libpython3.11-stdlib_3.11.2-6+deb12u7_armhf.deb
5990D010CC1F96D166C1FB1BCE06822F14665DC9D83E528B166E129982B09D7B  downloads/runtime-libs/armhf/libtinfo6_6.4-4_armhf.deb
```

### Python Curses Repair

Problem:

```text
import curses -> ModuleNotFoundError
```

Installed runtime files:

```text
/usr/lib/python3.11/curses/__init__.py
/usr/lib/python3.11/curses/panel.py
/usr/lib/python3.11/lib-dynload/_curses.cpython-311-arm-linux-gnueabihf.so
/usr/lib/python3.11/lib-dynload/_curses_panel.cpython-311-arm-linux-gnueabihf.so
/usr/local/lib/libtinfo.so.6.4
/usr/local/lib/libpanelw.so.6.4
/usr/lib/libtinfo.so.6 -> /usr/local/lib/libtinfo.so.6
/lib/libtinfo.so.6 -> /usr/local/lib/libtinfo.so.6
```

Source packages:

```text
libpython3.11-stdlib_3.11.2-6+deb12u7_armhf.deb
libtinfo6_6.4-4_armhf.deb
libncursesw6_6.4-4_armhf.deb
```

Verification:

```sh
python3 - <<'PY'
import curses
import curses.panel
print(curses.__file__)
print("panel ok")
PY
```

Migration target:

- Build Python 3 with curses support.
- Include ncurses wide-character and panel libraries natively.
- Probable Buildroot areas: Python 3 package options plus ncurses wide-char and
  panel support. Confirm exact symbols in the newer Buildroot tree.

### htop Repair

Installed runtime files:

```text
/usr/bin/htop
/usr/bin/htop.real
/usr/lib/libnl-3.so -> libnl-3.so.200.26.0
/usr/lib/libnl-3.so.200 -> libnl-3.so.200.26.0
/usr/lib/libnl-3.so.200.26.0
/usr/lib/libnl-genl-3.so -> libnl-genl-3.so.200.26.0
/usr/lib/libnl-genl-3.so.200 -> libnl-genl-3.so.200.26.0
/usr/lib/libnl-genl-3.so.200.26.0
/usr/local/lib/libncursesw.so -> libncursesw.so.6
/usr/local/lib/libncursesw.so.6 -> libncursesw.so.6.4
/usr/local/lib/libncursesw.so.6.4
/usr/local/lib/libtinfo.so -> libtinfo.so.6
/usr/local/lib/libtinfo.so.6 -> libtinfo.so.6.4
/usr/local/lib/libtinfo.so.6.4
/lib/terminfo/*
```

`/usr/bin/htop` is a wrapper from `scripts/device/htop`:

```sh
export LD_LIBRARY_PATH="/usr/local/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
[ -z "${TERM:-}" ] || [ "$TERM" = "dumb" ] && export TERM=linux
exec /usr/bin/htop.real "$@"
```

Source packages:

```text
htop_3.2.2-2_armhf.deb
libnl-3-200_3.7.0-0.2+b1_armhf.deb
libnl-genl-3-200_3.7.0-0.2+b1_armhf.deb
ncurses-base_6.4-4_all.deb
libncursesw6_6.4-4_armhf.deb
libtinfo6_6.4-4_armhf.deb
```

Verification:

```sh
htop --version
TERM=xterm-256color htop --help >/tmp/htop-help.out
```

Migration target:

- Build `htop` as a native Buildroot package.
- Include `libnl`, `ncursesw`, `tinfo`, and terminfo entries.
- Remove `/usr/bin/htop.real` and the wrapper once the native package works.

### NumPy / yfinance Runtime Repair

Problem:

```text
import yfinance
ImportError: libopenblas.so.0: cannot open shared object file
```

Installed runtime links observed:

```text
/usr/lib/libopenblas.so.0 -> /usr/local/lib/libopenblas.so.0
/usr/lib/libgfortran.so.5 -> /usr/local/lib/libgfortran.so.5
```

Source packages:

```text
libopenblas0-pthread_0.3.20+ds-1_armhf.deb
libgfortran5_12.3.0-1ubuntu1~22.04.3_armhf.deb
```

Verification:

```sh
su - neusse -c 'python3 - <<PY
import numpy
import yfinance
print(numpy.__version__)
print("yfinance ok")
PY'
```

Migration target:

- Prefer a native Buildroot Python numerical stack only if needed.
- If yfinance is still desired, include OpenBLAS and Fortran runtime cleanly or
  avoid pandas/numpy-heavy packages on the device.
- Probable Buildroot areas: OpenBLAS, Python NumPy, Python pandas if available.
  Confirm exact symbols in the newer Buildroot tree.

## 2. Kernel And Driver Additions

### Realtek Wi-Fi Module

Installed files:

```text
/lib/modules/6.1.99/extra/88XXau.ko
/lib/modules/6.1.99/extra/rtl8xxxu_git.ko
/etc/init.d/S04load_88xxau
/etc/udev/rules.d/70-persistent-net.rules
```

Loaded module:

```text
88XXau
```

Reason:

- The USB Wi-Fi adapter did not work through the base `rtl8xxxu` path.
- The working path was `88XXau.ko`, built against the same SDK kernel and
  compiler as the running kernel.

Verification:

```sh
lsmod | grep 88XXau
ip link show wlan0
wpa_cli -i wlan0 status
```

Migration target:

- Build the working Realtek driver in-tree or as an external Buildroot kernel
  module package.
- Keep `wlan0` naming stable.
- Decide whether `rtl8xxxu_git.ko` is still needed; if not, remove it from the
  clean image.

### PicoCalc Keyboard MCU Kernel Patch

Patch file:

```text
patches/picocalc-keyboard-mcu-sysfs.patch
```

Runtime sysfs attributes:

```text
/sys/bus/i2c/devices/0-001f/battery_raw
/sys/bus/i2c/devices/0-001f/battery_percent
/sys/bus/i2c/devices/0-001f/battery_status
/sys/bus/i2c/devices/0-001f/screen_backlight
/sys/bus/i2c/devices/0-001f/keyboard_backlight
/sys/bus/i2c/devices/0-001f/poweroff_delay
```

User command:

```text
/usr/local/sbin/picocalc-mcu
/usr/bin/picocalc-mcu -> /usr/local/sbin/picocalc-mcu
/usr/local/sbin/shutdown
/usr/bin/shutdown -> /usr/local/sbin/shutdown
```

`shutdown` is intentionally the full PicoCalc shutdown path: it stores the MCU
power-off delay through `picocalc-mcu poweroff`, syncs filesystems, then runs
BusyBox `poweroff`. The keyboard driver sends `REG_ID_OFF` from its kernel
shutdown callback during halt/poweroff and skips that command during reboot.
Use BusyBox `poweroff` directly for a Linux-only halt.

Kernel install note:

```text
Installed kernel: 6.1.99 #1 SMP PREEMPT Thu Jan 1 00:00:00 UTC 2026
Boot image: artifacts/picocalc-keyboard-mcu-shutdown-hook-zboot.img
Boot image sha256: c3a0bb3eda9a1cd8a090684fc6d044df68ddec4cdd40484d3b3d728720adba69
Boot backup: /mnt/sdcard/backups/boot-before-shutdown-hook-20260619-192731.img
Boot backup sha256: 3860f65387ec2c8af7f61b2d225f98ce5a27eafc0a16cd5bc4091479d70878d3
```

Build note:

- Use the checked-in build wrapper from Windows PowerShell:
  `.\scripts\build-kernel.ps1 kernel-stage`.
- The wrapper runs WSL `make kernel-stage`, sets the Buildroot host include/lib
  paths, fixes kernel build metadata, copies `zboot.img` into `artifacts/`, and
  writes a `.sha256` file.
- The known-good kernel build path is the WSL ext4 SDK tree at
  `/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK`.
- The Windows SDK copy under `upstream/picocalc-luckfox-lyra/SDK` can be useful
  for reference, but it hit CRLF/Kconfig failures when used as the active
  kernel build tree through Docker Desktop mounts.
- Direct WSL kernel builds may need the Buildroot host include/lib paths:
  `SDK/buildroot/output/rockchip_rk3506_picocalc_luckfox/host/include` and
  `.../host/lib` for `gmp.h` and `mpc.h`.

Migration target:

- Carry the kernel patch forward, or replace it with an upstream PicoCalc MCU
  driver if one exists in the newer tree.
- Include `picocalc-mcu` and `shutdown` as device utilities.

## 3. Boot And Init Scripts Added

Installed init scripts:

```text
/etc/init.d/S02swapfile
/etc/init.d/S04load_88xxau
/etc/init.d/S45wifi
/etc/init.d/S47ntpd
/etc/init.d/S55issue_ip
/etc/init.d/S56console_permissions
/etc/init.d/S57picofontd
/etc/init.d/S58crond
/usr/local/sbin/picocpu
/usr/bin/picocpu -> /usr/local/sbin/picocpu
```

Source copies in this repo:

```text
scripts/device/S02swapfile
scripts/device/S04load_88xxau
scripts/device/S45wifi
scripts/device/S47ntpd
scripts/device/S55issue_ip
scripts/device/S56console_permissions
scripts/device/S57picofontd
scripts/device/S58crond
scripts/device/picocpu
scripts/device/root-crontab
```

### Swap

Installed:

```text
/overlay/swapfile
/etc/init.d/S02swapfile
```

Reason:

- RAM is small.
- Root `/` is overlayfs, so `/swapfile` failed. The real ext4 overlay partition
  works.

Verification:

```sh
cat /proc/swaps
free -m
```

Migration target:

- Enable swap support.
- Prefer zram if the newer kernel/image supports it, or keep a real-partition
  swapfile strategy.

### Wi-Fi

Installed:

```text
/etc/init.d/S45wifi
/etc/wpa_supplicant.conf
/etc/wpa_supplicant.conf.bak-starlink-2g
```

Current behavior:

- Starts `wpa_supplicant` only.
- `dhcpcd` owns DHCP and routes.
- Current runtime config is local and contains network credentials; do not copy
  it into the public repo.
- Device is currently configured for `Starlink` on 2.4 GHz.

Verification:

```sh
wpa_cli -i wlan0 status
ip route
```

Migration target:

- Include `wpa_supplicant`, `wpa_cli`, and `dhcpcd`.
- Provide a credential-free template or first-boot provisioning method.
- Keep the duplicate-DHCP fix: do not run both `udhcpc` and `dhcpcd`.

### NTP

Active:

```text
/usr/local/sbin/busybox-ntpd
/usr/sbin/ntpd -> /usr/local/sbin/busybox-ntpd
/etc/ntp.conf
/etc/init.d/S47ntpd
```

Legacy fallback, disabled on the working device:

```text
/usr/local/sbin/picocalc_ntp.py
/etc/init.d/S46python_ntp.disabled
```

Reason:

- The device boots with a bad date when no RTC/network time is available.
- TLS and pip fail with a 1970 clock.
- The stock BusyBox image had `rdate` but not `ntpd`.
- A separate BusyBox 1.36.1 add-on now provides `ntpd` without replacing
  `/bin/busybox`.
- The old Python one-shot NTP init script is disabled so boot and app startup do
  not race separate time sync paths.

Verification:

```sh
date -u
ntpd --help
/etc/init.d/S47ntpd restart
ps w | grep '[n]tpd'
```

Migration target:

- Enable BusyBox `CONFIG_NTPD=y` in the native Buildroot BusyBox config.
- Keep `CONFIG_FEATURE_NTPD_CONF=y` so `/etc/ntp.conf` works.
- Remove the Python NTP helper from the clean image unless a fallback is still
  wanted for recovery images.

Artifact:

```text
artifacts/busybox-ntpd/busybox-ntpd-armhf
SHA256: 360785b50d9cb463abdf34ad7622241a5bd12f0c0d16e1510dd8045dcbd95ea6
```

### CPU Frequency Utility

Installed:

```text
/usr/local/sbin/picocpu
/usr/bin/picocpu -> /usr/local/sbin/picocpu
```

Reason:

- The kernel exposes cpufreq through `/sys/devices/system/cpu/cpufreq/policy0`.
- No `cpufreq-set` or `cpupower` utility is installed.
- Available governors are `ondemand`, `userspace`, and `performance`.
- Available frequencies are `600`, `800`, `1008`, `1200`, `1296`, `1416`,
  and `1512` MHz.

Usage:

```sh
picocpu status
picocpu performance
picocpu ondemand
picocpu set 800
```

Migration target:

- Keep the small `picocpu` utility, or add a standard cpufreq utility package.
- Default governor should remain `ondemand` unless thermal or battery testing
  proves another default is better.

### Login Banner

Installed:

```text
/etc/init.d/S55issue_ip
/etc/issue
```

Reason:

- Show current Wi-Fi and USB IP addresses on the PicoCalc login screen.

Migration target:

- Keep this script or replace with a more standard dynamic issue generator.

### Console Permissions

Installed:

```text
/etc/init.d/S56console_permissions
```

Reason:

- Allow non-root apps to use the framebuffer and input devices where needed.
- Sets group permissions for `/dev/tty0`, `/dev/tty1`, `/dev/console`, and
  `/dev/input/event*`. `/dev/tty0` is required by SDL2/DirectFB when native
  console apps restart from the launcher.

Migration target:

- Replace broad runtime permission fixes with stable groups, udev rules, or
  Buildroot device-table entries.
- Keep `/dev/tty0` readable/writable by the console app group, or native
  DirectFB apps can fail before the framebuffer appears.

### Cron

Installed:

```text
/etc/init.d/S58crond
/etc/crontabs/root
/var/spool/cron/crontabs -> /etc/crontabs
```

Reason:

- Enable scheduled PicoCalc maintenance tasks.
- BusyBox `crond` is already present and costs roughly 270 KB PSS when idle.
- The default cron spool is under `/var`, which is temporary on this image.
  The service runs `crond -c /etc/crontabs` so jobs persist across reboot.

Verification:

```sh
ps | grep '[c]rond'
crontab -l
```

Migration target:

- Keep a persistent crontab directory, or move to the standard cron package
  location if the next image has persistent `/var`.

## 4. Console Font System

Installed utilities:

```text
/usr/bin/picofont
/usr/sbin/picofontd
/etc/init.d/S57picofontd
/home/neusse/bin/picofont
```

Installed fonts:

```text
/usr/share/kbd/consolefonts/kernel-6x8.psf
/usr/share/kbd/consolefonts/ter-v12n.psf.gz
/usr/share/kbd/consolefonts/ter-v14b.psf.gz
/usr/share/kbd/consolefonts/ter-v14n.psf.gz
/usr/share/kbd/consolefonts/ter-v16b.psf.gz
/usr/share/kbd/consolefonts/ter-v16n.psf.gz
/usr/share/kbd/consolefonts/ter-v18b.psf.gz
/usr/share/kbd/consolefonts/ter-v18n.psf.gz
/usr/share/kbd/consolefonts/ter-v20b.psf.gz
/usr/share/kbd/consolefonts/ter-v20n.psf.gz
/usr/share/consolefonts/kernel-6x8.psf
/usr/share/consolefonts/ter-v12n.psf.gz
/usr/share/consolefonts/ter-v14b.psf.gz
/usr/share/consolefonts/ter-v14n.psf.gz
/usr/share/consolefonts/ter-v16b.psf.gz
/usr/share/consolefonts/ter-v16n.psf.gz
/usr/share/consolefonts/ter-v18b.psf.gz
/usr/share/consolefonts/ter-v18n.psf.gz
/usr/share/consolefonts/ter-v20b.psf.gz
/usr/share/consolefonts/ter-v20n.psf.gz
```

Font sources:

```text
downloads/fonts/terminus-font.pkg.tar.zst
downloads/fonts/generated/kernel-6x8.psf
```

Reason:

- The physical PicoCalc console defaults to Terminus 6x12 (`picofont small`),
  which gives a readable 53x26 console and matches Alpine mail.
- A readable 40-column Terminus mode is still available with `picofont 40`.
- Non-root cannot run `loadfont`, so `picofontd` loads fonts through a root FIFO.

Verification:

```sh
picofont small
stty size
picofont 40
stty size
picofont original
stty size
```

Migration target:

- Include `kbd` or equivalent console-font tooling.
- Package Terminus console fonts or choose a native font package.
- Keep `kernel-6x8.psf` if the original tiny font is desired.
- Replace `picofontd` with a safer helper only if non-root font switching remains
  required.

## 5. Device Utilities And Apps

Installed launcher:

```text
/usr/local/bin/picocalc-app
/usr/bin/picocalc-app -> /usr/local/bin/picocalc-app
/usr/bin/weather -> /usr/local/bin/picocalc-app
/usr/bin/picocalc-weather -> /usr/local/bin/picocalc-app
/usr/bin/sudoku -> /usr/local/bin/picocalc-app
/usr/bin/picocalc-sudoku -> /usr/local/bin/picocalc-app
/usr/bin/bubble -> /usr/local/bin/picocalc-app
/usr/bin/picocalc-bubble -> /usr/local/bin/picocalc-app
/usr/bin/chess -> /usr/local/bin/picocalc-app
/usr/bin/picocalc-chess -> /usr/local/bin/picocalc-app
/usr/bin/zork -> /usr/local/bin/picocalc-app
/usr/bin/picozork -> /usr/local/bin/picocalc-app
/usr/bin/picocalc-zork -> /usr/local/bin/picocalc-app
```

Installed app tree:

```text
/home/neusse/luckfox-dev/
/home/neusse/luckfox-dev/python/
```

Important apps:

```text
picocalc_weather.py
picocalc_sudoku.py
picocalc_bubble.py
picocalc_zork.py
rich_picocalc_demo.py
fb_demo.py
fb_ttf_demo.py
fb_ttf_showcase.py
```

Native chess runtime:

```text
/usr/libexec/picocalc/chess
/usr/games/gnuchess
/usr/lib/libyaml-cpp.so.0.8.0
/usr/share/chess
```

`/usr/libexec/picocalc/chess` must be installed as `root:root` with mode
`4755`. SDL2/DirectFB needs privileges for VT keyboard raw mode on this image.
Without that, `picocalc-app chess` can fail with `K_MEDIUMRAW failed`.

Other utilities:

```text
/usr/local/sbin/picocalc-screenshot
/usr/bin/picocalc-screenshot -> /usr/local/sbin/picocalc-screenshot
/usr/local/sbin/picocalc-sdcard
```

Migration target:

- Install project Python packages under `/usr/lib/python3.11/site-packages` or
  `/opt/luckfox-picocalc` instead of syncing a dev tree into a home directory.
- Keep `picocalc-app` or replace it with separate app entry points after the app
  APIs stabilize.
- Include framebuffer screenshot and SD-card helpers as normal packages.

## 6. User And Python Environment Changes

User:

```text
neusse
home: /home/neusse
uid/gid: 1000/1000
shell: /bin/bash
```

PATH/profile additions:

```text
/etc/profile.d/neusse-local-bin.sh
/home/neusse/bin
/home/neusse/.local/bin
```

Python:

```text
Python 3.11.8
pip 24.0
/home/neusse/venvs/nonroot
```

Selected non-root Python packages currently installed:

```text
numpy==2.4.6
pandas==3.0.3
requests==2.34.2
rich==15.0.0
pillow==10.2.0
yfinance==1.4.1
```

Full package list should be regenerated before migration:

```sh
su - neusse -c 'python3 -m pip list --format=freeze | sort'
```

Migration target:

- Decide whether PyPI packages are part of the image or user-managed state.
- Prefer Buildroot packages for compiled extensions.
- Keep a venv only for user experimentation.
- Add real `sudo` if needed; current image does not include it.

## 7. Storage And SD Card

User-facing helper:

```text
/usr/local/sbin/picocalc-sdcard
```

Default paths:

```text
device:     /dev/mmcblk1
partition:  /dev/mmcblk1p1
mountpoint: /mnt/sdcard
```

PicoZork story path:

```text
/mnt/sdcard/cpz/stories
/mnt/sdcard/cpz/saves
```

Migration target:

- Include filesystem support for intended removable-card formats.
- Add mount/eject handling in a normal init/udev path.

## 8. Buildroot Migration Checklist

Use this as the first pass for a newer Buildroot image:

- [ ] Boot Lyra/PicoCalc kernel and device tree.
- [ ] Carry PicoCalc keyboard MCU sysfs patch or equivalent upstream driver.
- [ ] Build and autoload working Realtek Wi-Fi driver.
- [ ] Include `wpa_supplicant`, `wpa_cli`, and `dhcpcd`; avoid duplicate DHCP.
- [ ] Include Python 3.11 or newer with SSL, SQLite, venv, ensurepip or pip, and
      curses.
- [ ] Include ncurses wide-char, panel, tinfo, and terminfo entries.
- [ ] Include `htop` and `libnl`.
- [ ] Decide whether OpenBLAS/gfortran/numpy/pandas are image features or user
      extras.
- [ ] Include console font tooling and the selected 40-column font.
- [ ] Include framebuffer/input permissions via groups or device table.
- [ ] Include swap or zram.
- [ ] Include NTP at boot.
- [ ] Include dynamic login banner or equivalent.
- [ ] Package `picofb`, `picoterm`, `picogames`, `picozork`, and examples.
- [ ] Install `picocalc-app` or final per-app commands.
- [ ] Keep all network credentials out of the image and public repo.

## 9. Re-Audit Commands

Run these before starting a new image migration:

```sh
cat /etc/os-release
uname -a
find /etc/init.d -maxdepth 1 -type f | sort
find /usr/bin /usr/local/bin /usr/local/sbin /usr/sbin -maxdepth 1 -type f | sort
find /usr/lib /usr/local/lib /lib -maxdepth 1 -type f -o -type l | sort
find /usr/lib/python3.11 -path '*curses*' -o -path '*lib-dynload*_curses*'
find /usr/share/kbd/consolefonts /usr/share/consolefonts -maxdepth 1 -type f
find /lib/terminfo -type f | sort
lsmod
cat /proc/swaps
su - neusse -c 'python3 -m pip list --format=freeze | sort'
```
