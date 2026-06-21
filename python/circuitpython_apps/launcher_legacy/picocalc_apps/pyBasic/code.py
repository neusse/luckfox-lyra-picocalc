import builtins
import os
import sys
import time
import traceback

# Prefer /lib so picocalc_app.py wins over the /picocalc_app folder.
if "/lib" not in sys.path:
    sys.path.insert(0, "/lib")

from picocalc_app import init_pcalc

# Allow pcalc_terminal to live in this folder or /lib.
try:
    from pcalc_terminal import PicoCalcTerminal, io_print
except Exception:
    from pcalc_terminal import PicoCalcTerminal, io_print


inp, pcd, display = init_pcalc(__file__, rotation=0, debug=False)

# Ensure local modules are found (support /picocalc_app and /picocalc_apps).
for p in ("/picocalc_apps/pyBasic", "/picocalc_app/pyBasic"):
    try:
        os.stat(p)
        if p not in sys.path:
            sys.path.append(p)
    except OSError:
        pass

term = PicoCalcTerminal(display, inp, invert=True)
term.clear()

# Monkeypatch builtins for PyBasic IO
builtins_input = builtins.input
builtins_print = builtins.print


def _input(prompt="> "):
    line = term.readline(prompt)
    if line is None:
        inp.exit_to_menu()
    return line


def _print(*args, sep=" ", end="\n", file=None, flush=False):
    io_print(term, *args, sep=sep, end=end, file=file, flush=flush)


builtins.input = _input
builtins.print = _print

try:
    import interpreter
    interpreter.main()
except Exception as e:
    io_print(term, "PyBasic error:", e)
    traceback.print_exception(e, e, e.__traceback__)
    term.write("\\nPress any key to exit...")
    while inp.get_char() is None:
        time.sleep(0.02)
finally:
    builtins.input = builtins_input
    builtins.print = builtins_print
    inp.exit_to_menu()
