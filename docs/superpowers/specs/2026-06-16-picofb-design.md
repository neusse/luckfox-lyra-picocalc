# PicoFB Framebuffer Library Design

## Goal

Create a small Python graphics library for the Luckfox Lyra inside the ClockworkPi PicoCalc. The library should make the Linux framebuffer feel approachable in the same spirit as CircuitPython display/framebuffer libraries, while still fitting the current Buildroot image and small RAM budget.

The first target is the current PicoCalc framebuffer:

```text
Device: /dev/fb0
Driver: ili9488drmfb
Resolution: 320x320
Bits per pixel: 16
Stride: 640 bytes
Initial required format: RGB565
```

A full screen buffer is about 200 KiB, so double-buffered drawing in Python is acceptable.

## User Experience

The core API should be familiar to embedded Python users:

```python
from picofb import Display, color565

display = Display("/dev/fb0")
display.fill(color565(0, 0, 0))
display.text("Hello", 8, 8, color565(255, 255, 255))
display.rect(20, 40, 100, 50, color565(0, 255, 0))
display.show()
```

Optional Pillow integration should allow richer drawing when Pillow is available:

```python
from picofb import Display
from PIL import Image, ImageDraw

display = Display()
img = Image.new("RGB", display.size, "black")
draw = ImageDraw.Draw(img)
draw.text((10, 10), "Pillow works", fill="white")
display.image(img)
display.show()
```

## Scope

Version 1 should include:

- Pure Python implementation.
- No required PyPI dependencies.
- Direct `/dev/fb0` output.
- Runtime detection from `/sys/class/graphics/fb0`.
- RGB565 drawing buffer.
- Basic drawing primitives:
  - `pixel`
  - `fill`
  - `line`
  - `hline`
  - `vline`
  - `rect`
  - `fill_rect`
  - `text`
  - `blit`
  - `image`
  - `show`
  - `clear`
- Demo script that draws color bars, text, rectangles, and diagonal lines on the physical PicoCalc screen.

Out of scope for version 1:

- Hardware acceleration.
- X11, Wayland, Tkinter, pygame, or SDL dependencies.
- Touch/mouse input.
- Complex font rendering beyond a built-in bitmap font or minimal text path.
- Automatic console restoration after drawing.

## Architecture

### `Display`

`Display` is the main user-facing object. It owns the framebuffer path, screen metadata, and an in-memory `Canvas`.

Responsibilities:

- Read framebuffer metadata from `/sys/class/graphics/fb0`.
- Open `/dev/fb0` for binary writes.
- Expose `width`, `height`, `stride`, `bpp`, and `size`.
- Delegate drawing calls to its internal canvas.
- Flush canvas bytes to the framebuffer on `show()`.

### `Canvas`

`Canvas` is a bytearray-backed RGB565 drawing surface.

Responsibilities:

- Store pixels in RGB565 little-endian layout.
- Clip drawing operations to bounds.
- Implement basic primitives.
- Provide a way to copy raw RGB565 buffers in and out.

### Color Helpers

`color565(r, g, b)` converts 8-bit RGB components into a 16-bit RGB565 integer.

Additional helpers may be added later, such as named colors, but they are not required for version 1.

### Pillow Adapter

`Display.image(img, x=0, y=0)` should accept a Pillow image when Pillow is installed. The adapter converts `RGB` or `RGBA` pixels to RGB565 and writes into the canvas.

If Pillow is not installed and a non-supported image object is passed, the library should raise a clear `ImportError` or `TypeError`.

## Error Handling

The library should fail clearly when:

- `/dev/fb0` is missing.
- `/sys/class/graphics/fb0` metadata is missing or inconsistent.
- The framebuffer is not 16 bpp.
- The stride is smaller than `width * 2`.
- The process lacks permission to open `/dev/fb0`.

Drawing operations should clip silently rather than raise on out-of-bounds coordinates.

## Permissions

Current `/dev/fb0` is owned by `root:video` with mode `0660`. For `neusse` to draw directly, the user should be added to the `video` group or a startup script should adjust permissions intentionally.

The implementation should not require root if permissions are configured correctly.

## Testing

Initial verification should include:

- Unit-style host/device tests for `color565` and clipping behavior.
- Device smoke test that opens `/dev/fb0`, draws the demo, and flushes.
- A short command using `tools/luckfox-dev.py` to run the demo remotely.

Manual visual verification is acceptable for the first framebuffer demo because the output target is the physical PicoCalc screen.

## Packaging

Place version 1 under:

```text
python/picofb/
examples/python/fb_demo.py
```

Use `tools/luckfox-dev.py runpy` for initial execution. Later, if the library becomes stable, package it as an installable local Python package.

## Future Work

Potential next steps after version 1:

- Keyboard/input event helper for PicoCalc keys.
- Dirty rectangle flushing.
- Sprite support.
- Additional bitmap fonts.
- Higher-level widgets: labels, menus, dialogs, status bars.
- Compatibility shim for a subset of Adafruit `framebuf` naming.
