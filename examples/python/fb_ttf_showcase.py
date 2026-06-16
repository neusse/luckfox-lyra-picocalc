"""TrueType font showcase for PicoFB on the PicoCalc."""

from __future__ import annotations

from picofb import BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW, Display, color565


DARK = color565(7, 12, 20)
PANEL = color565(18, 28, 40)
INK = color565(230, 238, 246)
MUTED = color565(132, 150, 164)
ORANGE = color565(255, 155, 44)
LIME = color565(124, 255, 74)


def draw_demo(display: Display) -> None:
    """Draw a font-focused 320x320 PicoCalc demo and flush it."""
    width = display.width
    height = display.height

    display.fill(DARK)
    display.fill_rect(0, 0, width, 54, PANEL)
    display.fill_rect(0, height - 35, width, 35, BLACK)
    display.rect(0, 0, width, height, CYAN)
    display.rect(3, 3, max(1, width - 6), max(1, height - 6), BLUE)

    display.text_ttf("PicoFB", 14, 8, WHITE, font="Decker", size=38)
    display.text_ttf("TrueType", 151, 17, CYAN, font="Notepad", size=28)

    display.text_ttf("Decker Bold", 18, 72, ORANGE, font="Decker", size=25)
    display.text_ttf("Notepad script", 18, 107, CYAN, font="Notepad", size=25)
    display.text_ttf("Morpheus", 18, 142, LIME, font="Morpheus", size=25)
    display.text_ttf("Cinema", 18, 178, YELLOW, font="Cinema", size=20)
    display.text_ttf("Grunge", 18, 213, MAGENTA, font="Grunge", size=20)

    display.line(14, 63, width - 15, 63, MUTED)
    display.line(14, 248, width - 15, 248, MUTED)

    display.fill_rect(18, 259, width - 36, 1, GREEN)
    display.text_ttf("fontconfig + freetype", 20, 270, INK, font="Decker", size=18)
    display.text_ttf("scalable TTF text", 20, 294, MUTED, font="Notepad", size=16)

    display.show()


def main() -> int:
    with Display("/dev/fb0") as display:
        draw_demo(display)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
