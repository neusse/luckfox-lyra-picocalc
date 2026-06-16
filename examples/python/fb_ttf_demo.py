from picofb import BLACK, CYAN, GREEN, WHITE, Display


def draw_demo(display: Display) -> None:
    display.fill(BLACK)
    display.text_ttf("PicoFB", 18, 24, WHITE, font="Decker", size=48)
    display.text_ttf("TrueType fonts", 18, 92, CYAN, font="Notepad", size=28)
    display.text_ttf("fontconfig + Pillow", 18, 134, GREEN, font="Morpheus", size=24)
    display.show()


if __name__ == "__main__":
    with Display("/dev/fb0") as display:
        draw_demo(display)
