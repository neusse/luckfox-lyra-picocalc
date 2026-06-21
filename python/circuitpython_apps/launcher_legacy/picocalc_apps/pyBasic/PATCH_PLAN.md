PyBasic PicoCalc Port Plan

Goal
- Run PyBasic on PicoCalc using the existing PicoCalc display/keyboard helpers and a Sudoku-style text UI.

Scope / Structure
- Copy or reference the existing app from `FJ_apps/PyBasic` into `picocalc_app/pyBasic` so it can be launched from the PicoCalc menu.
- Add a PicoCalc-specific entry point (e.g. `picocalc_pybasic.py` in the root or `picocalc_app/pyBasic/code.py`).

Porting Steps
1) Add a PicoCalc terminal layer
   - Create `picocalc_app/pyBasic/pcalc_terminal.py` that:
     - Sets up a `terminalio.Terminal` using `displayio.Bitmap` + `TileGrid` (see `picocalc_terminal_test.py`).
     - Exposes `write(text)` and `clear()` helpers.
     - Implements `readline(prompt)` using `PicoCalcInput.get_char()` with basic line editing:
       - ENTER submits, BACKSPACE deletes, printable ASCII appends, ESC/BACK exits to menu.
     - Uses XOR inversion to match PicoCalc display.

2) Replace stdin/stdout usage
   - Update `FJ_apps/PyBasic/interpreter.py` and `FJ_apps/PyBasic/basicparser.py`:
     - Replace `input(...)` with `pcalc_terminal.readline(...)`.
     - Replace `print(...)` calls with `pcalc_terminal.write(...)` (or a wrapper `io_print` function).
   - Option: in the PicoCalc entry point, monkeypatch `builtins.input` / `builtins.print` to route through `pcalc_terminal` to reduce edits.

3) Paths and sys.path
   - Change `EXTRA_LIB_DIR` in `interpreter.py` to `/picocalc_app/pyBasic` (or adjust the entry point to `sys.path.append(...)`).
   - Ensure SAVE/LOAD defaults to `/sd/pybasic/` or `/` so files are accessible on PicoCalc.
   - If `os.chdir` is unreliable in CircuitPython, remove it and keep full paths.

4) Entry point wiring
   - Add a PicoCalc launcher (e.g. `picocalc_pybasic.py`) that:
     - Calls `init_pcalc()`.
     - Initializes the terminal screen.
     - Calls `interpreter.main()`.
     - Handles exit by calling `inp.exit_to_menu()`.

5) UI polish (Sudoku-style)
   - Use the Sudoku palette for header/footer or add a simple header line in the terminal for app name + hints.
   - Optional: show a small overlay for errors instead of raw tracebacks.

6) Testing checklist on PicoCalc
   - Basic REPL: type lines, backspace edit, ENTER accepts.
   - Program entry + LIST/RUN.
   - INPUT statement (from `basicparser.py`) uses PicoCalc keyboard.
   - SAVE/LOAD works to `/sd/pybasic`.
   - Exit returns to menu without a black screen.

Files to edit/copy
- `FJ_apps/PyBasic/interpreter.py`
- `FJ_apps/PyBasic/basicparser.py`
- `FJ_apps/PyBasic/program.py` (paths / `os.chdir` if needed)
- New: `picocalc_app/pyBasic/pcalc_terminal.py`
- New: `picocalc_app/pyBasic/code.py` or `picocalc_pybasic.py`
