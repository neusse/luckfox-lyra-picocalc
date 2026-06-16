"""Physical framebuffer demo for PicoFB on Luckfox Lyra."""

from __future__ import annotations

from picofb import BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW, Display, color565


NAVY = color565(8, 20, 44)
PANEL = color565(18, 46, 66)
ORANGE = color565(255, 150, 32)
GRAY = color565(78, 88, 100)


def _text_width(value: str, scale: int = 1) -> int:
    return max(0, len(value) * 6 * scale - scale)


def _center_text(
    display: Display,
    value: str,
    y: int,
    color: int,
    *,
    background: int | None = None,
    scale: int = 1,
) -> None:
    x = max(0, (display.width - _text_width(value, scale)) // 2)
    display.text(value, x, y, color, background=background, scale=scale)


def draw_demo(display: Display) -> None:
    """Draw the PicoFB framebuffer demo and flush it to the device."""
    width = display.width
    height = display.height
    display.fill(NAVY)

    bar_colors = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, MAGENTA, WHITE]
    bar_height = max(18, height // 9)
    bar_width = max(1, width // len(bar_colors))
    for index, color in enumerate(bar_colors):
        x = index * bar_width
        next_x = width if index == len(bar_colors) - 1 else (index + 1) * bar_width
        display.fill_rect(x, 0, next_x - x, bar_height, color)

    display.rect(0, 0, width, height, WHITE)
    display.rect(3, 3, max(1, width - 6), max(1, height - 6), CYAN)

    title_scale = 3 if width >= 220 and height >= 220 else 2
    subtitle_scale = 2 if width >= 180 else 1
    title_y = min(height - 64, bar_height + 14)
    _center_text(display, "PICOFB", title_y, WHITE, background=NAVY, scale=title_scale)
    _center_text(
        display,
        "LUCKFOX LYRA",
        title_y + (10 * title_scale) + 6,
        YELLOW,
        background=NAVY,
        scale=subtitle_scale,
    )
    _center_text(
        display,
        f"{width}X{height} RGB565",
        title_y + (10 * title_scale) + (10 * subtitle_scale) + 12,
        CYAN,
        background=NAVY,
    )

    frame_x = max(14, width // 12)
    frame_y = min(height - 90, max(bar_height + 82, height // 2 - 28))
    frame_w = max(80, width - (frame_x * 2))
    frame_h = min(62, max(36, height - frame_y - 44))
    display.fill_rect(frame_x, frame_y, frame_w, frame_h, PANEL)
    display.rect(frame_x, frame_y, frame_w, frame_h, ORANGE)
    display.rect(frame_x + 3, frame_y + 3, max(1, frame_w - 6), max(1, frame_h - 6), WHITE)
    _center_text(
        display,
        "FRAMEBUFFER",
        frame_y + max(8, (frame_h - 7) // 2),
        WHITE,
        background=PANEL,
    )

    display.line(8, bar_height + 8, width - 9, height - 9, GRAY)
    display.line(width - 9, bar_height + 8, 8, height - 9, GRAY)

    nested_x = max(12, width - 82)
    nested_y = max(bar_height + 10, height - 104)
    for offset, color in ((0, GREEN), (8, CYAN), (16, YELLOW), (24, MAGENTA)):
        rect_w = max(8, 70 - (offset * 2))
        rect_h = max(8, 70 - (offset * 2))
        display.rect(nested_x + offset, nested_y + offset, rect_w, rect_h, color)

    display.fill_rect(8, height - 24, width - 16, 16, BLACK)
    _center_text(display, "RUNNING AS USER", height - 20, GREEN, background=BLACK)

    display.show()


def main() -> int:
    with Display("/dev/fb0") as display:
        draw_demo(display)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
