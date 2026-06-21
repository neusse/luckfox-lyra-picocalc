"""Optional TrueType text helpers for PicoFB."""

from __future__ import annotations

import shutil
import subprocess
from ctypes import (
    CDLL,
    POINTER,
    Structure,
    byref,
    c_char_p,
    c_int,
    c_long,
    c_short,
    c_ubyte,
    c_uint,
    c_ulong,
    c_ushort,
    c_void_p,
    cast,
)
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .colors import BLACK


@dataclass(frozen=True)
class TtfTextBounds:
    width: int
    height: int
    x_offset: int = 0
    y_offset: int = 0


def rgb565_to_rgb(color: int) -> tuple[int, int, int]:
    """Convert an RGB565 integer to an 8-bit RGB tuple."""
    red = (color >> 11) & 0x1F
    green = (color >> 5) & 0x3F
    blue = color & 0x1F
    return (
        (red << 3) | (red >> 2),
        (green << 2) | (green >> 4),
        (blue << 3) | (blue >> 2),
    )


def resolve_font(font: str | Path) -> str:
    """Resolve a font path or fontconfig family name for Pillow."""
    font_text = str(font)
    font_path = Path(font_text).expanduser()
    if font_path.exists():
        return str(font_path)

    if shutil.which("fc-match"):
        try:
            result = subprocess.run(
                ["fc-match", "-f", "%{file}", font_text],
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except (OSError, subprocess.SubprocessError):
            result = None
        if result is not None and result.returncode == 0:
            candidate = result.stdout.strip()
            if candidate and Path(candidate).exists():
                return candidate

    return font_text


def measure_ttf_text(value: object, *, font: str | Path, size: int = 16) -> TtfTextBounds:
    """Measure the rendered bounds for TrueType text."""
    size = max(1, int(size))
    text = str(value)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        return _measure_ttf_text_freetype(text, font=font, size=size, import_error=exc)

    pil_font = ImageFont.truetype(resolve_font(font), size)
    measure = Image.new("L", (1, 1), 0)
    measure_draw = ImageDraw.Draw(measure)
    bbox = measure_draw.multiline_textbbox((0, 0), text, font=pil_font)
    return TtfTextBounds(
        width=max(1, bbox[2] - bbox[0]),
        height=max(1, bbox[3] - bbox[1]),
        x_offset=bbox[0],
        y_offset=bbox[1],
    )


def draw_ttf_text(
    canvas: Any,
    value: object,
    x: int,
    y: int,
    color: int,
    *,
    font: str | Path,
    size: int = 16,
    background: int | None = None,
):
    """Draw antialiased TrueType text on a PicoFB canvas using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        return _draw_ttf_text_freetype(
            canvas,
            value,
            x,
            y,
            color,
            font=font,
            size=size,
            background=background,
            import_error=exc,
        )

    size = max(1, int(size))
    text = str(value)
    pil_font = ImageFont.truetype(resolve_font(font), size)

    measure = Image.new("L", (1, 1), 0)
    measure_draw = ImageDraw.Draw(measure)
    bbox = measure_draw.multiline_textbbox((0, 0), text, font=pil_font)
    width = max(1, bbox[2] - bbox[0])
    height = max(1, bbox[3] - bbox[1])

    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.multiline_text((-bbox[0], -bbox[1]), text, font=pil_font, fill=255)

    foreground = rgb565_to_rgb(color)
    background_rgb = rgb565_to_rgb(background) if background is not None else None
    alphas = mask.getdata()

    index = 0
    for source_y in range(height):
        for source_x in range(width):
            alpha = alphas[index]
            index += 1
            target_x = x + source_x
            target_y = y + source_y
            if not canvas._contains(target_x, target_y):
                continue

            if alpha == 0:
                if background is not None:
                    canvas.pixel(target_x, target_y, background)
                continue

            base_rgb = (
                background_rgb
                if background_rgb is not None
                else rgb565_to_rgb(canvas.pixel(target_x, target_y))
            )
            blended = tuple(
                ((foreground[channel] * alpha) + (base_rgb[channel] * (255 - alpha))) // 255
                for channel in range(3)
            )
            canvas.pixel(target_x, target_y, _rgb_to_rgb565(*blended))

    return canvas


def _rgb_to_rgb565(red: int, green: int, blue: int) -> int:
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


class _FT_Generic(Structure):
    _fields_ = [("data", c_void_p), ("finalizer", c_void_p)]


class _FT_BBox(Structure):
    _fields_ = [
        ("xMin", c_long),
        ("yMin", c_long),
        ("xMax", c_long),
        ("yMax", c_long),
    ]


class _FT_Vector(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class _FT_Glyph_Metrics(Structure):
    _fields_ = [
        ("width", c_long),
        ("height", c_long),
        ("horiBearingX", c_long),
        ("horiBearingY", c_long),
        ("horiAdvance", c_long),
        ("vertBearingX", c_long),
        ("vertBearingY", c_long),
        ("vertAdvance", c_long),
    ]


class _FT_Bitmap(Structure):
    _fields_ = [
        ("rows", c_uint),
        ("width", c_uint),
        ("pitch", c_int),
        ("buffer", POINTER(c_ubyte)),
        ("num_grays", c_ushort),
        ("pixel_mode", c_ubyte),
        ("palette_mode", c_ubyte),
        ("palette", c_void_p),
    ]


class _FT_GlyphSlotRec(Structure):
    pass


_FT_GlyphSlotRec._fields_ = [
    ("library", c_void_p),
    ("face", c_void_p),
    ("next", c_void_p),
    ("glyph_index", c_uint),
    ("generic", _FT_Generic),
    ("metrics", _FT_Glyph_Metrics),
    ("linearHoriAdvance", c_long),
    ("linearVertAdvance", c_long),
    ("advance", _FT_Vector),
    ("format", c_uint),
    ("bitmap", _FT_Bitmap),
    ("bitmap_left", c_int),
    ("bitmap_top", c_int),
]


class _FT_FaceRec(Structure):
    _fields_ = [
        ("num_faces", c_long),
        ("face_index", c_long),
        ("face_flags", c_long),
        ("style_flags", c_long),
        ("num_glyphs", c_long),
        ("family_name", c_char_p),
        ("style_name", c_char_p),
        ("num_fixed_sizes", c_int),
        ("available_sizes", c_void_p),
        ("num_charmaps", c_int),
        ("charmaps", c_void_p),
        ("generic", _FT_Generic),
        ("bbox", _FT_BBox),
        ("units_per_EM", c_ushort),
        ("ascender", c_short),
        ("descender", c_short),
        ("height", c_short),
        ("max_advance_width", c_short),
        ("max_advance_height", c_short),
        ("underline_position", c_short),
        ("underline_thickness", c_short),
        ("glyph", POINTER(_FT_GlyphSlotRec)),
    ]


def _load_freetype():
    for library_name in ("libfreetype.so.6", "libfreetype.so"):
        try:
            freetype = CDLL(library_name)
            break
        except OSError:
            freetype = None
    if freetype is None:
        raise ImportError("PicoFB TrueType text requires Pillow or libfreetype")

    freetype.FT_Init_FreeType.argtypes = [POINTER(c_void_p)]
    freetype.FT_Init_FreeType.restype = c_int
    freetype.FT_New_Face.argtypes = [c_void_p, c_char_p, c_long, POINTER(c_void_p)]
    freetype.FT_New_Face.restype = c_int
    freetype.FT_Set_Pixel_Sizes.argtypes = [c_void_p, c_uint, c_uint]
    freetype.FT_Set_Pixel_Sizes.restype = c_int
    freetype.FT_Load_Char.argtypes = [c_void_p, c_ulong, c_int]
    freetype.FT_Load_Char.restype = c_int
    freetype.FT_Done_Face.argtypes = [c_void_p]
    freetype.FT_Done_Face.restype = c_int
    freetype.FT_Done_FreeType.argtypes = [c_void_p]
    freetype.FT_Done_FreeType.restype = c_int
    return freetype


def _draw_ttf_text_freetype(
    canvas: Any,
    value: object,
    x: int,
    y: int,
    color: int,
    *,
    font: str | Path,
    size: int,
    background: int | None,
    import_error: ImportError,
):
    try:
        freetype = _load_freetype()
    except ImportError as exc:
        raise ImportError("PicoFB TrueType text requires Pillow or libfreetype") from import_error or exc

    font_path = resolve_font(font)
    if not Path(font_path).exists():
        raise FileNotFoundError(f"TrueType font not found: {font}")

    library = c_void_p()
    if freetype.FT_Init_FreeType(byref(library)):
        raise RuntimeError("failed to initialize FreeType")

    face = c_void_p()
    try:
        if freetype.FT_New_Face(library, font_path.encode(), 0, byref(face)):
            raise RuntimeError(f"failed to load TrueType font: {font_path}")
        if freetype.FT_Set_Pixel_Sizes(face, 0, max(1, int(size))):
            raise RuntimeError(f"failed to set TrueType font size: {size}")

        face_rec = cast(face, POINTER(_FT_FaceRec)).contents
        line_height = max(1, int(size))
        baseline = y + line_height
        pen_x = x
        origin_x = x

        if background is not None:
            text_width = _measure_freetype_text(freetype, face, value, line_height)
            text_height = line_height * len(str(value).splitlines() or [""])
            canvas.fill_rect(x, y, text_width, text_height, background)

        for char in str(value):
            if char == "\n":
                pen_x = origin_x
                baseline += line_height
                continue

            if freetype.FT_Load_Char(face, ord(char), 4):
                continue

            slot = face_rec.glyph.contents
            bitmap = slot.bitmap
            _draw_freetype_bitmap(
                canvas,
                bitmap,
                pen_x + slot.bitmap_left,
                baseline - slot.bitmap_top,
                color,
                background,
            )
            pen_x += slot.advance.x >> 6
    finally:
        if face:
            freetype.FT_Done_Face(face)
        freetype.FT_Done_FreeType(library)

    return canvas


def _measure_ttf_text_freetype(
    value: object,
    *,
    font: str | Path,
    size: int,
    import_error: ImportError,
) -> TtfTextBounds:
    try:
        freetype = _load_freetype()
    except ImportError as exc:
        raise ImportError("PicoFB TrueType text requires Pillow or libfreetype") from import_error or exc

    font_path = resolve_font(font)
    if not Path(font_path).exists():
        raise FileNotFoundError(f"TrueType font not found: {font}")

    library = c_void_p()
    if freetype.FT_Init_FreeType(byref(library)):
        raise RuntimeError("failed to initialize FreeType")

    face = c_void_p()
    try:
        if freetype.FT_New_Face(library, font_path.encode(), 0, byref(face)):
            raise RuntimeError(f"failed to load TrueType font: {font_path}")
        line_height = max(1, int(size))
        if freetype.FT_Set_Pixel_Sizes(face, 0, line_height):
            raise RuntimeError(f"failed to set TrueType font size: {size}")

        lines = str(value).splitlines() or [""]
        width = _measure_freetype_text(freetype, face, value, line_height)
        return TtfTextBounds(width=max(1, width), height=max(1, line_height * len(lines)))
    finally:
        if face:
            freetype.FT_Done_Face(face)
        freetype.FT_Done_FreeType(library)


def _measure_freetype_text(freetype, face, value: object, line_height: int) -> int:
    max_width = 0
    current_width = 0
    for char in str(value):
        if char == "\n":
            max_width = max(max_width, current_width)
            current_width = 0
            continue
        if freetype.FT_Load_Char(face, ord(char), 4):
            continue
        face_rec = cast(face, POINTER(_FT_FaceRec)).contents
        current_width += face_rec.glyph.contents.advance.x >> 6
    return max(line_height, max(max_width, current_width))


def _draw_freetype_bitmap(canvas, bitmap, x: int, y: int, color: int, background: int | None):
    foreground = rgb565_to_rgb(color)
    background_rgb = rgb565_to_rgb(background) if background is not None else None

    for row in range(bitmap.rows):
        for column in range(bitmap.width):
            offset = (row * abs(bitmap.pitch)) + column
            alpha = bitmap.buffer[offset]
            if alpha == 0:
                continue

            target_x = x + column
            target_y = y + row
            if not canvas._contains(target_x, target_y):
                continue

            base_rgb = (
                background_rgb
                if background_rgb is not None
                else rgb565_to_rgb(canvas.pixel(target_x, target_y))
            )
            blended = tuple(
                ((foreground[channel] * alpha) + (base_rgb[channel] * (255 - alpha))) // 255
                for channel in range(3)
            )
            canvas.pixel(target_x, target_y, _rgb_to_rgb565(*blended))
