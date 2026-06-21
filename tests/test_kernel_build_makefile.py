import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"
PS_WRAPPER = ROOT / "scripts" / "build-kernel.ps1"
FIT_NORMALIZER = ROOT / "scripts" / "normalize-fit-image.py"
RESOURCE_TOOL_PATCH = ROOT / "patches" / "rockchip-resource-tool-zero-index-entry.patch"


class KernelBuildMakefileTest(unittest.TestCase):
    def test_makefile_defines_repeatable_kernel_stage_target(self):
        text = MAKEFILE.read_text(encoding="utf-8")

        for expected in (
            "kernel-stage:",
            'rm -f "$(KERNEL_DIR)/scripts/resource_tool"',
            'cd "$(SDK_DIR)" && env',
            "./build.sh kernel",
            'python3 "$(CURDIR)/scripts/normalize-fit-image.py" "$(KERNEL_IMAGE)"',
            'CPATH="$(HOST_DIR)/include"',
            "SOURCE_DATE_EPOCH",
            "KBUILD_BUILD_TIMESTAMP",
            "KBUILD_BUILD_USER",
            "KBUILD_BUILD_HOST",
            "KBUILD_BUILD_VERSION",
            "KERNEL_IMAGE_NAME ?= picocalc-keyboard-mcu-shutdown-hook-zboot.img",
            'sha256sum "$(KERNEL_IMAGE)" > "$(KERNEL_HASH)"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_powershell_wrapper_runs_make_inside_wsl(self):
        text = PS_WRAPPER.read_text(encoding="utf-8")

        self.assertIn("wslpath", text)
        self.assertIn("wsl.exe", text)
        self.assertIn("make", text)
        self.assertIn("kernel-stage", text)

    def test_resource_tool_patch_zeroes_index_entries(self):
        text = RESOURCE_TOOL_PATCH.read_text(encoding="utf-8")

        self.assertIn("scripts/resource_tool.c", text)
        self.assertIn("memset(&entry, 0, sizeof(entry));", text)
        self.assertIn("memcpy(entry.tag, INDEX_TBL_ENTR_TAG, sizeof(entry.tag));", text)

    def test_fit_normalizer_zeroes_reserve_map(self):
        text = FIT_NORMALIZER.read_text(encoding="utf-8")

        self.assertIn("FDT_MAGIC", text)
        self.assertIn("off_mem_rsvmap", text)
        self.assertIn("off_dt_struct", text)
        self.assertIn("blob[off_mem_rsvmap:off_dt_struct] = zeros", text)


if __name__ == "__main__":
    unittest.main()
