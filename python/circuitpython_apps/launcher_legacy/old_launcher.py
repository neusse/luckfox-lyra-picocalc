# code.py - PicoCalc Main Menu (CircuitPython)

import time
import os
import sys
import struct
import board
import displayio
import terminalio
import supervisor # pyright: ignore[reportMissingImports]
import microcontroller # pyright: ignore[reportMissingImports]
import gc

from adafruit_display_text import label

# --- PicoCalc INIT imports and setup ---
from picocalc_app import init_pcalc, load_secrets, build_ntp_sync # pyright: ignore[reportMissingImports]

inp, pcd, display = init_pcalc(__file__, rotation=0, debug=False)

secrets = load_secrets({"ssid": "", "password": ""})
ts = build_ntp_sync(secrets)
ts.sync_now()

WIDTH = pcd.width
HEIGHT = pcd.height

from picocalc_sd import PicoCalcSD # pyright: ignore[reportMissingImports]

# sd = PicoCalcSD()
# try:
#     sd.mount(wait_for_card=0.5)
# except Exception as e:
#     print("SD mount failed:", repr(e))
# inp = PicoCalcInput(debug=False)


# Your panel is clipped at the very top. Skip the first "text line".
TOP_OFFSET = 16   # increase to 18/20 if still clipped

# ============================================================
# Colors
# ============================================================

COLOR_BG = 0x000000
COLOR_TEXT = 0xFFFFFF
COLOR_TIME = 0x00FF00  # GREEN

COLOR_BANNER_BG = 0x0000FF # ^ 0xFFFFFF
COLOR_BANNER_TEXT = 0xFFFFFF# ^ 0xFFFFFF

COLOR_ROW_BG = COLOR_BG
COLOR_ROW_TEXT = COLOR_TEXT
COLOR_HILITE_BG = 0xFFFF00    # Yellow
COLOR_HILITE_TEXT = 0x000000  # black

# ============================================================
# Layout
# ============================================================

PAD_X = 6
TIME_H = 16
BANNER_H = 22
ROW_H = 16
GAP_Y = 2

# ============================================================
# Keys (from your template)
# ============================================================

KEY_UP    = 181
KEY_DOWN  = 182
KEY_CR    = 13

# Added: run + view keys (PicoCalcInput.get_char() typically returns ASCII for letters)
KEY_R_UPPER = ord("R")  # R for Run the program
KEY_R_LOWER = ord("r")
KEY_V_UPPER = ord("V")  # V for View the code
KEY_V_LOWER = ord("v")

VIEWER_FILE = "picocalc_py_view.py"   # what you want to run for viewing


def set_root_group(disp, group):
    # Prefer root_group because that’s what you’re using
    try:
        disp.root_group = group
        return
    except Exception:
        pass
    try:
        disp.show(group)
        return
    except Exception:
        pass
    raise RuntimeError("Cannot set display root group")




# ============================================================
# NVM helpers (1-byte length prefix: nvm[0]=len, nvm[1:]=utf-8 bytes)
# ============================================================

def nvm_write_str(s: str):
    b = s.encode("utf-8")
    nvm = microcontroller.nvm
    if len(b) > (len(nvm) - 1):
        raise ValueError("Path too long for NVM")
    nvm[0] = len(b)
    nvm[1:1+len(b)] = b


# ============================================================
# Program scanning (root flash only, per your requirement)
# ============================================================

def list_programs_root():
    ignore = {
        "code.py",
        "boot.py",
        "secrets.py",
        "picocalc_menu.py",
        VIEWER_FILE,              # <-- ADDED so viewer isn't shown in menu
    }
    out = []
    for name in sorted(os.listdir("/")):
        if not name.lower().endswith(".py"):
            continue
        if name in ignore:
            continue
        try:
            mode = os.stat("/" + name)[0]
            if (mode & 0x4000) != 0:
                continue
        except Exception:
            pass
        out.append("/" + name)

#     for name in sorted(os.listdir("/sd/picocalc_code/")):
#         if not name.lower().endswith(".py"):
#             continue
#         if name in ignore:
#             continue
#         try:
#             mode = os.stat("/sd/picocalc_code/" + name)[0]
#             if (mode & 0x4000) != 0:
#                 continue
#         except Exception:
#             pass
#         out.append("/sd/picocalc_code/" + name)
# 
#     print(out)

    return out

# ============================================================
# UI build
# ============================================================

root = displayio.Group()

# background fill
bg_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = COLOR_BG
root.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0))

# put all UI into an offset group so top line isn't clipped
ui = displayio.Group(x=0, y=TOP_OFFSET)
root.append(ui)

time_label = label.Label(
    terminalio.FONT,
    text="--:--:-- ---   --/--/--                  Batt:%",
    color=COLOR_TIME,
    x=PAD_X,
    y=2,
)
ui.append(time_label)

banner_y = TIME_H
banner_bitmap = displayio.Bitmap(WIDTH, BANNER_H, 1)
banner_palette = displayio.Palette(1)
banner_palette[0] = COLOR_BANNER_BG
ui.append(displayio.TileGrid(banner_bitmap, pixel_shader=banner_palette, x=0, y=banner_y))

banner_label = label.Label(terminalio.FONT, text="MAIN MENU", color=COLOR_BANNER_TEXT)
banner_label.anchor_point = (0.5, 0.0)
banner_label.anchored_position = (WIDTH // 2, banner_y + 4)
ui.append(banner_label)

menu_top = banner_y + BANNER_H + GAP_Y
ui_height = HEIGHT - TOP_OFFSET
menu_height = ui_height - menu_top - 2
VISIBLE_ROWS = max(1, menu_height // ROW_H)

rows_group = displayio.Group()
rows_group.y = menu_top
ui.append(rows_group)

row_bg_palettes = []
row_labels = []

for i in range(VISIBLE_ROWS):
    y = i * ROW_H
    rbm = displayio.Bitmap(WIDTH, ROW_H, 1)
    rpal = displayio.Palette(1)
    rpal[0] = COLOR_ROW_BG
    row_bg_palettes.append(rpal)
    rows_group.append(displayio.TileGrid(rbm, pixel_shader=rpal, x=0, y=y))

    lbl = label.Label(
        terminalio.FONT,
        text="",
        color=COLOR_ROW_TEXT,
        x=PAD_X,
        y=y + 8,
    )
    row_labels.append(lbl)
    rows_group.append(lbl)

set_root_group(display, root)

# ============================================================
#   Menu logic
# ============================================================

entries = list_programs_root()
selected = 0
scroll = 0
last_selected = -1
last_scroll = -1

def _truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max(0, max_chars - 3)] + "..."

MAX_CHARS = (WIDTH - (PAD_X * 2)) // 6
display_names = [_truncate(p, MAX_CHARS) for p in entries]
row_entry_idx = [-1] * VISIBLE_ROWS

def _set_row(row, idx, is_sel):
    if idx < 0 or idx >= len(entries):
        if row_entry_idx[row] != -1:
            row_entry_idx[row] = -1
            row_labels[row].text = ""
        if row_bg_palettes[row][0] != COLOR_ROW_BG:
            row_bg_palettes[row][0] = COLOR_ROW_BG
        if row_labels[row].color != COLOR_ROW_TEXT:
            row_labels[row].color = COLOR_ROW_TEXT
        return

    if row_entry_idx[row] != idx:
        row_entry_idx[row] = idx
        row_labels[row].text = display_names[idx]

    new_bg = COLOR_HILITE_BG if is_sel else COLOR_ROW_BG
    if row_bg_palettes[row][0] != new_bg:
        row_bg_palettes[row][0] = new_bg
    new_color = COLOR_HILITE_TEXT if is_sel else COLOR_ROW_TEXT
    if row_labels[row].color != new_color:
        row_labels[row].color = new_color

def render_menu(force=False):
    global scroll, last_scroll, last_selected

    if not entries:
        for i in range(VISIBLE_ROWS):
            _set_row(i, -1, False)
            if i == 0:
                row_labels[i].text = "No .py programs found"
        return

    if selected < scroll:
        scroll = selected
    elif selected >= scroll + VISIBLE_ROWS:
        scroll = selected - VISIBLE_ROWS + 1

    if force or scroll != last_scroll:
        for i in range(VISIBLE_ROWS):
            idx = scroll + i
            _set_row(i, idx, idx == selected)
    else:
        if last_selected != -1:
            old_row = last_selected - scroll
            if 0 <= old_row < VISIBLE_ROWS:
                _set_row(old_row, last_selected, False)
        new_row = selected - scroll
        if 0 <= new_row < VISIBLE_ROWS:
            _set_row(new_row, selected, True)

    last_scroll = scroll
    last_selected = selected

last_batt_value = None

def update_time(batt_value=None):
    global last_batt_value
    local_tt, tz = ts.pacific_now()
    if local_tt is None:
        return
    hh, mm, ss = local_tt.tm_hour, local_tt.tm_min, local_tt.tm_sec
    yr = local_tt.tm_year - 2000
    mon = local_tt.tm_mon
    day = local_tt.tm_mday

    if batt_value is None:
        batt_value = last_batt_value
    else:
        last_batt_value = batt_value
    if batt_value is None:
        batt_value = "?"
    time_label.text = (
        f"{hh:02d}:{mm:02d}:{ss:02d} {tz}   {mon:02d}/{day:02d}/{yr:02d}"
        f"                  Batt:{batt_value}%"
    )

def _status(msg: str):
    time_label.text = msg
    try:
        display.refresh()
    except Exception:
        pass

def launch_selected(fn: str):
    _status("Launching...")

#     if fn.startswith("/sd"):
#         work_path = "/sd/picocalc_code"
#     else:
#         work_path = "/"
# 
#     print(os.listdir("/sd/picocalc_code/"))
#     print(fn)
    supervisor.set_next_code_file(
        fn,
        working_directory="/",
        reload_on_success=True,
        reload_on_error=True,
        sticky_on_success=False,
        sticky_on_error=False,
        sticky_on_reload=False
    )
    displayio.release_displays()
    supervisor.reload()

    _status("Reload blocked; press CTRL-D")
    while True:
        time.sleep(1)

def view_selected(fn: str):
    # Store absolute path so the viewer can open it directly.
    
    try:
        nvm_write_str(fn)
    except Exception as e:
        _status("NVM write failed")
        print("NVM write failed:", e)
        time.sleep(1.0)
        return

    _status("Viewing...")

    supervisor.set_next_code_file(
        VIEWER_FILE,
        working_directory="/",
        reload_on_success=True,
        reload_on_error=True,
        sticky_on_success=False,
        sticky_on_error=False,
        sticky_on_reload=False,
    )
    displayio.release_displays()
    supervisor.reload()

    _status("Reload blocked; press CTRL-D")
    while True:
        time.sleep(1)

# ============================================================
# Main
# ============================================================

def main():
    global selected, entries, last_batt_value


    render_menu(force=True)
    last_update = time.monotonic()
    last_batt = -10.0

    while True:
        now = time.monotonic()
        if now - last_update >= 1.0:
            last_update = now
            # update battery less frequently to avoid ADC stalls
            if now - last_batt >= 5.0:
                last_batt = now
                last_batt_value = inp.read_battery()
                update_time(last_batt_value)
            else:
                update_time(last_batt_value)

        ch = inp.get_char()
        if ch is None:
            time.sleep(0.01)
            continue

        if ch == KEY_UP and entries and selected > 0:
            selected -= 1
            render_menu()

        elif ch == KEY_DOWN and entries and selected < (len(entries) - 1):
            selected += 1
            render_menu()

        elif ch == KEY_CR and entries:
            launch_selected(entries[selected])

        # Optional: run with R/r (matches what you described)
        elif ch in (KEY_R_UPPER, KEY_R_LOWER) and entries:
            launch_selected(entries[selected])

        # View with V/v
        elif ch in (KEY_V_UPPER, KEY_V_LOWER) and entries:
            view_selected(entries[selected])

main()
