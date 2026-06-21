# PicoCalc Chessboard Port

This note records the native chess install for the Luckfox Lyra PicoCalc image.

## Components

- Frontend: `neusse/picocalc-chessboard` at commit `41eff5a`.
- Engine: GNU Chess `6.2.9`, launched as `/usr/games/gnuchess --uci`.
- Runtime library added: `yaml-cpp 0.8.0`.
- Display/input path: SDL2 over DirectFB on the PicoCalc framebuffer.

## Device Install Paths

```text
/usr/libexec/picocalc/chess
/usr/games/gnuchess
/usr/lib/libyaml-cpp.so.0.8.0
/usr/lib/libyaml-cpp.so.0.8 -> libyaml-cpp.so.0.8.0
/usr/lib/libyaml-cpp.so -> libyaml-cpp.so.0.8
/usr/share/chess
/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
```

`/usr/bin/chess` and `/usr/bin/picocalc-chess` are launcher aliases that point
to `/usr/local/bin/picocalc-app`. The launcher runs the real frontend from
`/usr/libexec/picocalc/chess`.

The frontend binary is installed setuid-root:

```sh
chown root:root /usr/libexec/picocalc/chess
chmod 4755 /usr/libexec/picocalc/chess
```

SDL2/DirectFB can open the framebuffer as `neusse`, but VT keyboard raw mode
needs privileges on this image. Without the setuid bit, restarting chess from
`picocalc-app chess` fails with `K_MEDIUMRAW failed`.

## Build Notes

GNU Chess was built directly from the GNU `gnuchess-6.2.9` release tarball using
the Buildroot ARM toolchain. The configure step needs cross-compile cache answers
for standard C headers and allocator behavior:

```sh
./configure \
  --host=arm-buildroot-linux-gnueabihf \
  --prefix=/usr \
  --disable-nls \
  --without-readline \
  ac_cv_header_stdc=yes \
  ac_cv_header_stdlib_h=yes \
  ac_cv_func_malloc_0_nonnull=yes \
  ac_cv_func_realloc_0_nonnull=yes \
  ac_cv_func_memcmp_working=yes
```

`yaml-cpp` was built with the existing Buildroot package target:

```sh
make O=output/rockchip_rk3506_picocalc_luckfox yaml-cpp
```

The chessboard frontend was built from the `neusse/picocalc-chessboard` fork
with the existing Buildroot generated CMake toolchain file. The WSL environment
needed the Buildroot host library path for `pkg-config`:

```sh
export LD_LIBRARY_PATH=/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK/buildroot/output/rockchip_rk3506_picocalc_luckfox/host/lib
cmake .. \
  -G "Unix Makefiles" \
  -DCMAKE_TOOLCHAIN_FILE=/home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK/buildroot/output/rockchip_rk3506_picocalc_luckfox/build/chessboard-789bc8ce7d704f3dee3067e6f425467eb7158c3d/toolchainfile.cmake \
  -DCMAKE_MAKE_PROGRAM=/usr/bin/make \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DCMAKE_BUILD_TYPE=Release
make -j2
```

## Run

From SSH or ADB:

```sh
picocalc-app chess
```

The app detaches to `/dev/tty1`, starts GNU Chess as the engine, and uses the
physical PicoCalc screen and keyboard. If chess is already running, the launcher
prints the active PID and exits instead of starting a second copy.

## PicoCalc Input Patch

The upstream key map uses Space to select a piece and Enter to move. The PicoCalc
build also lets Enter select a piece when no piece is currently selected, because
that is the natural first key to try on the built-in keyboard.
