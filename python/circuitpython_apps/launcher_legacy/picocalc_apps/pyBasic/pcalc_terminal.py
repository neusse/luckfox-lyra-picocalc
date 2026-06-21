import time
import displayio
import terminalio
from terminalio import Terminal


class PicoCalcTerminal:
    def __init__(self, display, inp, invert=True):
        self.display = display
        self.inp = inp

        font = terminalio.FONT
        font_bb = font.get_bounding_box()
        screen_size = (display.width // font_bb[0], display.height // font_bb[1])
        char_size = font_bb

        palette = displayio.Palette(2)
        if invert:
            palette[0] = 0x000000 ^ 0xFFFFFF
            palette[1] = 0xFFFFFF ^ 0xFFFFFF
        else:
            palette[0] = 0x000000
            palette[1] = 0xFFFFFF

        tilegrid = displayio.TileGrid(
            bitmap=font.bitmap,
            width=screen_size[0],
            height=screen_size[1],
            tile_width=char_size[0],
            tile_height=char_size[1],
            pixel_shader=palette,
        )

        self.terminal = Terminal(tilegrid, font)
        root = displayio.Group()
        root.append(tilegrid)
        display.root_group = root
        self.root = root

    def write(self, text):
        if text is None:
            return
        try:
            s = str(text)
            s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
            self.terminal.write(s)
        except Exception:
            pass

    def clear(self):
        self.write(chr(27) + "[2J")
        self.write(chr(27) + "[H")

    def readline(self, prompt="> "):
        if prompt:
            self.write("\r" + prompt)

        buf = []
        while True:
            ch = self.inp.get_char()
            if ch is None:
                time.sleep(0.02)
                continue

            if ch in (10, 13):
                self.write("\r\n")
                return "".join(buf)

            if ch in (8, 127):
                if buf:
                    buf.pop()
                    self.write("\b \b")
                continue

            if ch in (27,):
                return None

            if 32 <= ch <= 126:
                c = chr(ch)
                buf.append(c)
                self.write(c)


def io_print(term, *args, sep=" ", end="\n", file=None, flush=False):
    out = sep.join(str(a) for a in args) + end
    term.write(out)
