SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

SDK_DIR ?= /home/neusse/luckfox-lyra-build/picocalc-luckfox-lyra/SDK
HOST_DIR ?= $(SDK_DIR)/buildroot/output/rockchip_rk3506_picocalc_luckfox/host
KERNEL_DIR ?= $(SDK_DIR)/kernel-6.1
ARTIFACT_DIR ?= $(CURDIR)/artifacts
KERNEL_IMAGE_NAME ?= picocalc-keyboard-mcu-shutdown-hook-zboot.img
KERNEL_IMAGE ?= $(ARTIFACT_DIR)/$(KERNEL_IMAGE_NAME)
KERNEL_HASH ?= $(KERNEL_IMAGE).sha256
PUREDOOM_DIR ?= $(CURDIR)/downloads/source/PureDOOM
PUREDOOM_BINARY ?= $(ARTIFACT_DIR)/puredoom/picocalc-puredoom
PUREDOOM_CC ?= $(HOST_DIR)/bin/arm-buildroot-linux-gnueabihf-gcc
PUREDOOM_SYSROOT ?= $(HOST_DIR)/arm-buildroot-linux-gnueabihf/sysroot

SOURCE_DATE_EPOCH ?= 1767225600
KBUILD_BUILD_TIMESTAMP ?= Thu Jan 1 00:00:00 UTC 2026
KBUILD_BUILD_USER ?= codex
KBUILD_BUILD_HOST ?= luckfox-lyra-picocalc
KBUILD_BUILD_VERSION ?= 1

.PHONY: help kernel-preflight kernel-build kernel-stage kernel-hash puredoom-preflight puredoom-build

help:
	@printf '%s\n' \
		'Luckfox Lyra PicoCalc kernel build targets:' \
		'  kernel-preflight  Check the expected SDK and host tool paths' \
		'  kernel-build      Rebuild the vendor kernel with fixed build metadata' \
		'  kernel-stage      Build, copy zboot.img to artifacts, and write sha256' \
		'  kernel-hash       Recompute the staged image sha256' \
		'  puredoom-build    Cross-compile the PicoCalc PureDOOM SDL frontend'

kernel-preflight:
	test -d "$(SDK_DIR)"
	test -d "$(HOST_DIR)/include"
	test -d "$(HOST_DIR)/lib"
	test -f "$(KERNEL_DIR)/drivers/input/keyboard/picocalc-keyboard.c"

kernel-build: kernel-preflight
	rm -f "$(KERNEL_DIR)/scripts/resource_tool"
	cd "$(SDK_DIR)" && env \
		CPATH="$(HOST_DIR)/include" \
		LIBRARY_PATH="$(HOST_DIR)/lib" \
		LD_LIBRARY_PATH="$(HOST_DIR)/lib" \
		SOURCE_DATE_EPOCH="$(SOURCE_DATE_EPOCH)" \
		KBUILD_BUILD_TIMESTAMP="$(KBUILD_BUILD_TIMESTAMP)" \
		KBUILD_BUILD_USER="$(KBUILD_BUILD_USER)" \
		KBUILD_BUILD_HOST="$(KBUILD_BUILD_HOST)" \
		KBUILD_BUILD_VERSION="$(KBUILD_BUILD_VERSION)" \
		./build.sh kernel

kernel-stage: kernel-build
	mkdir -p "$(ARTIFACT_DIR)"
	cp -f "$(KERNEL_DIR)/zboot.img" "$(KERNEL_IMAGE)"
	python3 "$(CURDIR)/scripts/normalize-fit-image.py" "$(KERNEL_IMAGE)"
	sha256sum "$(KERNEL_IMAGE)" > "$(KERNEL_HASH)"
	ls -lh "$(KERNEL_IMAGE)" "$(KERNEL_HASH)"
	cat "$(KERNEL_HASH)"

kernel-hash:
	test -f "$(KERNEL_IMAGE)"
	sha256sum "$(KERNEL_IMAGE)" > "$(KERNEL_HASH)"
	cat "$(KERNEL_HASH)"

puredoom-preflight:
	test -f "$(PUREDOOM_CC)"
	test -d "$(PUREDOOM_SYSROOT)"
	test -f "$(PUREDOOM_SYSROOT)/usr/include/SDL2/SDL.h"
	test -f "$(PUREDOOM_SYSROOT)/usr/lib/libSDL2.so"
	test -f "$(PUREDOOM_DIR)/PureDOOM.h"
	test -f "$(PUREDOOM_DIR)/doom1.wad"

puredoom-build: puredoom-preflight
	mkdir -p "$(dir $(PUREDOOM_BINARY))"
	"$(PUREDOOM_CC)" --sysroot="$(PUREDOOM_SYSROOT)" -O2 -DNDEBUG \
		-I"$(PUREDOOM_SYSROOT)/usr/include/SDL2" \
		-I"$(PUREDOOM_DIR)" \
		"$(CURDIR)/examples/c/picocalc_puredoom_sdl.c" \
		-o "$(PUREDOOM_BINARY)" \
		-L"$(PUREDOOM_SYSROOT)/usr/lib" -lSDL2 -lm -ldl -lpthread
	file "$(PUREDOOM_BINARY)"
