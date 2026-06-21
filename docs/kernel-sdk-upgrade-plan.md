# Kernel SDK Upgrade Plan

This is the safety plan before moving from the current Luckfox Lyra kernel SDK build to the latest official SDK.

## Current Checkpoint

Created before the latest-SDK upgrade work:

- Backup directory: `C:\Users\georg\Codex_Projects\luckfox-lyra\artifacts\backups\pre-latest-sdk-20260620-172959`
- Device boot/kernel partition backup on PicoCalc SD card: `/mnt/sdcard/backups/boot-kernel-pre-latest-sdk-20260620-172959.img`
- Host copy: `artifacts/backups/pre-latest-sdk-20260620-172959/boot-kernel-current-mmcblk0p2.img`
- Boot image SHA-256: `bcc7318cc9e19708a6de3a46f79332d8199070c54f42c677858d803043ed7844`
- Running kernel at checkpoint: `Linux picocalc 6.1.99 #1 SMP PREEMPT Thu Jan 1 00:00:00 UTC 2026 armv7l GNU/Linux`
- PicoCalc MCU poweroff delay at checkpoint: `8`

The active WSL build tree was moved, not copied:

- Old build tree: `/home/neusse/luckfox-lyra-archive/pre-latest-sdk-20260620-172959/luckfox-lyra-build`
- New staging path: `/home/neusse/luckfox-lyra-build`

A compressed full fallback archive also exists:

- `artifacts/backups/pre-latest-sdk-20260620-172959/wsl-luckfox-lyra-build-full.tar.zst`
- SHA-256: `5a5cbde50a0e19a3d2c186d2afcf9a3f7129585fb8ac406040fca56859b1beeb`

## Restore Current Boot Image

If the new kernel fails but ADB still works:

```powershell
$adb = 'C:\Users\georg\Codex_Projects\luckfox-lyra\downloads\tools\rockchip\RKDevTool\RKDevTool_Release\bin\adb.exe'
$image = 'C:\Users\georg\Codex_Projects\luckfox-lyra\artifacts\backups\pre-latest-sdk-20260620-172959\boot-kernel-current-mmcblk0p2.img'
& $adb push $image /tmp/boot-kernel-current-mmcblk0p2.img
& $adb shell "sha256sum /tmp/boot-kernel-current-mmcblk0p2.img"
& $adb shell "dd if=/tmp/boot-kernel-current-mmcblk0p2.img of=/dev/mmcblk0p2 bs=4M conv=fsync && sync"
& $adb reboot
```

Expected SHA-256:

```text
bcc7318cc9e19708a6de3a46f79332d8199070c54f42c677858d803043ed7844
```

This restores only the boot/kernel partition. It does not touch the root filesystem, home directory, SD card, apps, or user data.

## Restore Old WSL Build Tree

If the latest-SDK build path becomes unusable, move it aside and restore the archived build tree:

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc 'mv /home/neusse/luckfox-lyra-build /home/neusse/luckfox-lyra-build-failed-$(date +%Y%m%d-%H%M%S); mv /home/neusse/luckfox-lyra-archive/pre-latest-sdk-20260620-172959/luckfox-lyra-build /home/neusse/luckfox-lyra-build'
```

If the moved archive was damaged or already restored once, use the compressed fallback:

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc 'cd /home/neusse && tar --use-compress-program=unzstd -xpf /mnt/c/Users/georg/Codex_Projects/luckfox-lyra/artifacts/backups/pre-latest-sdk-20260620-172959/wsl-luckfox-lyra-build-full.tar.zst'
```

## Latest SDK Target

The public Luckfox release thread lists `Luckfox Lyra SDK Rev1.5` as the `202508` update. The forum post date is August 18, 2025.

Reference links:

- https://forums.luckfox.com/viewtopic.php?t=1420
- https://wiki.luckfox.com/Luckfox-Lyra/Download/

Our previous SDK tree used the manifest file `luckfox_linux6.1_rk3506_release_v1.4_20250620.xml`, but the kernel source commit inside it was from August 14, 2025.

## 2026-06-20 Staged Kernel Build

The local SDK tarball was staged into the clean build path:

- Tarball: `upstream/picocalc-luckfox-lyra/download/Luckfox_Lyra_SDK.tar.gz`
- Tarball SHA-256: `7d4ec6750d88635d7accc0f69ea9eb0f3c233f979c1cedb32b91709734fadecf`
- Staged SDK path: `/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK`
- Kernel source commit: `696a8549d1a582337c8032c02a2aea35790047a4`
- Kernel source commit date: `2025-08-14 20:45:57 +0800`
- Manifest file still reports: `luckfox_linux6.1_rk3506_release_v1.4_20250620.xml`

The SDK tarball contained the repo object store but not checked-out project worktrees. The bundled old `repo` tool needed a small Python 3 compatibility shim for the removed Python 2 `formatter` module before `repo sync -l` could materialize the worktree.

The PicoCalc wrapper `base/` overlay was applied directly from the local `upstream/picocalc-luckfox-lyra` mirror. The PicoCalc target selected successfully:

```bash
./build.sh picocalc_luckfox_lyra_buildroot_sdmmc_defconfig
```

The fresh SDK did not yet have a Buildroot host sysroot. Since WSL does not have passwordless sudo for installing `libgmp-dev`, `libmpc-dev`, and related host packages, the fresh SDK's host sysroot path was symlinked to the archived known-good host sysroot:

```text
/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK/buildroot/output/rockchip_rk3506_picocalc_luckfox/host
  -> /home/neusse/luckfox-lyra-archive/pre-latest-sdk-20260620-172959/luckfox-lyra-build/picocalc-luckfox-lyra/SDK/buildroot/output/rockchip_rk3506_picocalc_luckfox/host
```

This was used only for host build headers/libs during the kernel build.

Patches applied to the staged kernel:

- `patches/picocalc-keyboard-mcu-sysfs.patch`
- `patches/rockchip-resource-tool-zero-index-entry.patch` equivalent edit in `kernel-6.1/scripts/resource_tool.c`

Patched kernel artifact:

- Image: `artifacts/picocalc-keyboard-mcu-shutdown-hook-zboot.img`
- Size: `5,599,744` bytes
- SHA-256: `557d79674e2d4151bdbad13ed1c23da9e034583af541e8d716d178684b82315e`

Verification:

```powershell
python -m unittest tests.test_kernel_build_makefile tests.test_picocalc_keyboard_patch tests.test_picocalc_shutdown_scripts
```

Result: `8` tests passed.

## Upgrade Order

Use one variable at a time:

1. Download and unpack the latest official SDK into `/home/neusse/luckfox-lyra-build`.
2. Build the stock SDK first with its stock toolchain.
3. Confirm the stock build emits a boot image for the PicoCalc target.
4. Apply the PicoCalc-specific patches one group at a time.
5. Rebuild the boot image only.
6. Push and flash only `/dev/mmcblk0p2` for kernel testing.
7. Verify boot, ADB, SSH, Wi-Fi, `picocalc-mcu status`, framebuffer, keyboard, and launcher apps.

Do not flash rootfs or full update images during first kernel testing unless the new SDK requires a coordinated rootfs change.

## Patch Groups To Reapply

Expected local changes to carry forward:

- PicoCalc keyboard MCU sysfs and shutdown hook.
- PicoCalc display and keyboard device tree changes.
- Realtek Wi-Fi driver integration for the RTL8188FU dongle.
- Rockchip `resource_tool` zero-initialization fix.
- Deterministic kernel build wrapper and FIT normalizer if still needed.
- Buildroot rootfs additions we care about: Python fixes, curses module, OpenBLAS runtime, launcher scripts, fonts, cron, `picocalc-mcu`, `picofont`, and apps.
- BusyBox optional applet additions, especially `ntpd`, after the new SDK builds cleanly.

## Cross Compiler Rule

Do not upgrade the cross compiler during the SDK jump.

The new SDK should first build with the compiler and sysroot it ships with. Upgrading GCC at the same time can break:

- kernel warning behavior and older Rockchip build scripts,
- module vermagic and out-of-tree module builds,
- Buildroot sysroot/library assumptions,
- userland ABI compatibility if the runtime libraries do not match,
- repeatability when debugging a failed boot.

After the latest SDK is building and booting with the stock compiler, a compiler upgrade can be tested as a separate experiment in a separate build tree.
