"""Linux framebuffer display wrapper."""

from __future__ import annotations

from pathlib import Path

from .canvas import Canvas


class Display:
    """Canvas-backed RGB565 Linux framebuffer display."""

    def __init__(
        self,
        path: str = "/dev/fb0",
        *,
        sysfs_root: str = "/sys/class/graphics",
        fb_name: str | None = None,
    ):
        self.path = path
        self.fb_name = fb_name if fb_name is not None else Path(path).name

        metadata_root = Path(sysfs_root) / self.fb_name
        width, height = self._read_virtual_size(metadata_root / "virtual_size")
        bpp = self._read_int(metadata_root / "bits_per_pixel")
        stride = self._read_int(metadata_root / "stride")

        if bpp != 16:
            raise ValueError(f"only 16-bpp framebuffers are supported (got {bpp})")

        row_bytes = width * 2
        if stride < row_bytes:
            raise ValueError(
                f"framebuffer stride {stride} is smaller than row bytes {row_bytes}"
            )

        self.width = width
        self.height = height
        self.bpp = bpp
        self.stride = stride
        self.canvas = Canvas(width, height)
        self.buffer = self.canvas.buffer
        self._fb = self._open_framebuffer(Path(path))

    @property
    def size(self) -> tuple[int, int]:
        return self.canvas.size

    @staticmethod
    def _read_text(path: Path) -> str:
        try:
            return path.read_text(encoding="ascii").strip()
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"framebuffer metadata missing: {path}") from exc

    @classmethod
    def _read_int(cls, path: Path) -> int:
        value = cls._read_text(path)
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"invalid framebuffer metadata in {path}: {value!r}") from exc

    @classmethod
    def _read_virtual_size(cls, path: Path) -> tuple[int, int]:
        value = cls._read_text(path)
        try:
            width_text, height_text = value.split(",", 1)
            width = int(width_text)
            height = int(height_text)
        except ValueError as exc:
            raise ValueError(f"invalid framebuffer virtual_size in {path}: {value!r}") from exc

        if width <= 0 or height <= 0:
            raise ValueError(f"invalid framebuffer virtual_size in {path}: {value!r}")
        return width, height

    @staticmethod
    def _open_framebuffer(path: Path):
        try:
            return open(path, "r+b", buffering=0)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"framebuffer device missing: {path}") from exc
        except PermissionError as exc:
            raise PermissionError(f"permission denied opening framebuffer: {path}") from exc

    def close(self):
        self._fb.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def show(self):
        row_bytes = self.width * 2
        if self.stride == row_bytes:
            self._fb.seek(0)
            self._fb.write(self.buffer)
        else:
            for y in range(self.height):
                start = y * row_bytes
                end = start + row_bytes
                self._fb.seek(y * self.stride)
                self._fb.write(self.buffer[start:end])

        self._fb.flush()
        return self

    def pixel(self, x: int, y: int, color: int | None = None):
        if color is None:
            return self.canvas.pixel(x, y)

        self.canvas.pixel(x, y, color)
        return self

    def fill(self, color: int):
        self.canvas.fill(color)
        return self

    def clear(self):
        self.canvas.clear()
        return self

    def hline(self, x: int, y: int, width: int, color: int):
        self.canvas.hline(x, y, width, color)
        return self

    def vline(self, x: int, y: int, height: int, color: int):
        self.canvas.vline(x, y, height, color)
        return self

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int):
        self.canvas.line(x0, y0, x1, y1, color)
        return self

    def rect(self, x: int, y: int, width: int, height: int, color: int):
        self.canvas.rect(x, y, width, height, color)
        return self

    def fill_rect(self, x: int, y: int, width: int, height: int, color: int):
        self.canvas.fill_rect(x, y, width, height, color)
        return self

    def text(self, value, x: int, y: int, color: int, background=None, scale: int = 1):
        self.canvas.text(value, x, y, color, background=background, scale=scale)
        return self

    def text_ttf(
        self,
        value,
        x: int,
        y: int,
        color: int,
        *,
        font: str = "sans",
        size: int = 16,
        background=None,
    ):
        self.canvas.text_ttf(
            value,
            x,
            y,
            color,
            font=font,
            size=size,
            background=background,
        )
        return self

    def blit(
        self,
        source,
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
        source_stride: int | None = None,
    ):
        self.canvas.blit(source, x, y, width, height, source_stride)
        return self

    def image(self, image, x: int = 0, y: int = 0):
        self.canvas.image(image, x, y)
        return self
