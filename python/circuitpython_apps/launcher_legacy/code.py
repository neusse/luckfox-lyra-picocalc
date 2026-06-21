# picocalc launcher
# code.py - PicoCalc Main Menu (CircuitPython)
# Grid launcher driven by launcher_data.json icons/apps.

import json
import os
import time

import displayio
import terminalio
import supervisor # pyright: ignore[reportMissingImports]
import microcontroller # pyright: ignore[reportMissingImports]

from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

from picocalc_app import init_pcalc, load_secrets, build_ntp_sync
from picocalc_screenshot import save_pixels
import picocalc_sd

# --- Static config (layout, colors, data) ---
DATA_FILE = "launcher_data.json"
VIEWER_FILE = "picocalc_py_view.py"
ICON_SIZE = 64
ICON_GAP = 10
MARGIN_X = 10
MARGIN_Y = 8
FOOTER_H = 18
TOP_OFFSET = 16
TIME_H = 16
BANNER_H = 22
GAP_Y = 2

BG = 0x0B0F14
TEXT = 0x00FF00 #0xE5E7EB
HILITE = 0x38BDF8
PLACEHOLDER_BG = 0x111827
PLACEHOLDER_OUTLINE = 0x374151
PLACEHOLDER_TEXT = 0x9CA3AF
TIME_COLOR = 0x00FF00 #0x38BDF8
BANNER_BG = 0x1D4ED8
BANNER_TEXT = 0xFFFF00 #0xE5E7EB


# --- PicoCalc init (display + input) ---
inp, pcd, display = init_pcalc("picocalc_launcher.py", rotation=0, debug=False)
WIDTH = display.width
HEIGHT = display.height

try:
    display.auto_refresh = False
except Exception:
    pass


# --- Time sync (matches code.py header behavior) ---
secrets = load_secrets({"ssid": "", "password": ""})
ts = build_ntp_sync(secrets)
ts.sync_now()


# --- Key map ---
KEY_LEFT = getattr(inp, "KEY_LEFT", 180)
KEY_UP = getattr(inp, "KEY_UP", 181)
KEY_DOWN = getattr(inp, "KEY_DOWN", 182)
KEY_RIGHT = getattr(inp, "KEY_RIGHT", 183)
KEY_ENTER = getattr(inp, "KEY_CR", 13)
KEY_V_UPPER = ord("V")
KEY_V_LOWER = ord("v")


# Title: Normalize path
# Desc: Ensure absolute paths and strip whitespace.
def _normalize_path(path):
    if not path:
        return ""
    path = str(path).strip()
    if not path:
        return ""
    if not path.startswith("/"):
        path = "/" + path
    return path


# Title: Truncate label
# Desc: Keep footer text within display width.
def _truncate(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)] + "..."


# Title: NVM path write
# Desc: Store selected app path for the viewer.
def nvm_write_str(s):
    b = s.encode("utf-8")
    nvm = microcontroller.nvm
    if len(b) > (len(nvm) - 1):
        raise ValueError("Path too long for NVM")
    nvm[0] = len(b)
    nvm[1 : 1 + len(b)] = b


# Title: Load launcher entries
# Desc: Read JSON metadata and load BMP icons.
def load_entries():
    # Load app metadata and keep bitmap file handles alive.
    entries = []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("Launcher data load error:", e)
        return entries

    for item in data.get("icons", []):
        name = str(item.get("name", "")).strip()
        app = _normalize_path(item.get("app", ""))
        bmp = _normalize_path(item.get("bmp", ""))

        entry = {
            "name": name or "App",
            "app": app,
            "bmp": bmp,
            "file": None,
            "bitmap": None,
            "missing_app": False,
        }

        if app:
            try:
                os.stat(app)
            except Exception:
                entry["missing_app"] = True

        if bmp:
            try:
                f = open(bmp, "rb")
                entry["file"] = f
                entry["bitmap"] = displayio.OnDiskBitmap(f)
            except Exception as e:
                print("Icon load error:", bmp, e)

        entries.append(entry)

    return entries


# Title: Placeholder tile
# Desc: Show a fallback box when the BMP is missing.
def make_placeholder_group(text, x, y):
    # Simple fallback tile when a BMP is missing.
    grp = displayio.Group(x=x, y=y)
    grp.append(
        Rect(
            0,
            0,
            ICON_SIZE,
            ICON_SIZE,
            fill=PLACEHOLDER_BG,
            outline=PLACEHOLDER_OUTLINE,
            stroke=1,
        )
    )
    short = "?"
    if text:
        short = text[:1].upper()
    lbl = label.Label(terminalio.FONT, text=short, color=PLACEHOLDER_TEXT, scale=2)
    lbl.anchor_point = (0.5, 0.5)
    lbl.anchored_position = (ICON_SIZE // 2, ICON_SIZE // 2)
    grp.append(lbl)
    return grp


# Title: Root group setter
# Desc: Set the active display root group safely.
def set_root_group(disp, group):
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


# Title: Display refresh
# Desc: Manually refresh when auto_refresh is off.
def refresh():
    try:
        if hasattr(display, "auto_refresh") and (display.auto_refresh is False):
            display.refresh(minimum_frames_per_second=0)
    except Exception:
        pass


# Title: App launcher
# Desc: Chain into another app with supervisor.
def launch_app(app_path):
    if not app_path:
        return False
    supervisor.set_next_code_file(
        app_path,
        working_directory="/",
        reload_on_success=True,
        reload_on_error=True,
        sticky_on_success=False,
        sticky_on_error=False,
        sticky_on_reload=False,
    )
    displayio.release_displays()
    supervisor.reload()
    return True


# Title: Source viewer launcher
# Desc: Store path in NVM and chain to viewer.
def view_app(app_path):
    if not app_path:
        return False
    try:
        nvm_write_str(app_path)
    except Exception as e:
        print("NVM write failed:", e)
        return False
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
    return True


# --- Load launcher data ---
entries = load_entries()

# --- Grid geometry ---
banner_y = TOP_OFFSET + TIME_H
grid_top = banner_y + BANNER_H + GAP_Y
grid_bottom = HEIGHT - FOOTER_H - MARGIN_Y
grid_height = max(ICON_SIZE, grid_bottom - grid_top)

columns = max(1, (WIDTH - 2 * MARGIN_X + ICON_GAP) // (ICON_SIZE + ICON_GAP))
rows = max(1, (grid_height + ICON_GAP) // (ICON_SIZE + ICON_GAP))
per_page = max(1, columns * rows)

grid_w = columns * ICON_SIZE + (columns - 1) * ICON_GAP
grid_h = rows * ICON_SIZE + (rows - 1) * ICON_GAP
grid_x = (WIDTH - grid_w) // 2
grid_y = grid_top + (grid_height - grid_h) // 2


# --- Build root display groups ---
root = displayio.Group()
root.append(Rect(0, 0, WIDTH, HEIGHT, fill=BG, outline=None))

time_label = label.Label(
    terminalio.FONT,
    text="--:--:-- ---   --/--/--                  Batt:%",
    color=TIME_COLOR,
    x=MARGIN_X,
    y=TOP_OFFSET + 2,
)
root.append(time_label)

root.append(Rect(0, banner_y, WIDTH, BANNER_H, fill=BANNER_BG, outline=None))
banner_label = label.Label(terminalio.FONT, text="LAUNCHER", color=BANNER_TEXT)
banner_label.anchor_point = (0.5, 0.0)
banner_label.anchored_position = (WIDTH // 2, banner_y + 4)
root.append(banner_label)

icon_group = displayio.Group()
root.append(icon_group)

cursor_group = displayio.Group()
cursor_rect = Rect(0, 0, ICON_SIZE + 6, ICON_SIZE + 6, fill=None, outline=HILITE, stroke=2)
cursor_group.append(cursor_rect)
root.append(cursor_group)

footer_label = label.Label(terminalio.FONT, text="", color=TEXT, scale=1)
footer_label.anchor_point = (0.5, 1.0)
footer_label.anchored_position = (WIDTH // 2, HEIGHT - 2)
root.append(footer_label)

# --- Push UI to display ---
set_root_group(display, root)

# --- Selection state ---
selected = 0
page_start = -1
slot_positions = []
last_batt_value = None


# Title: Footer label update
# Desc: Show selection name or short status.
def update_footer(message=None):
    if message is not None:
        footer_label.text = message
        return
    if not entries:
        footer_label.text = "No icons in launcher_data.json"
        return
    entry = entries[selected]
    name = entry["name"] or entry["app"] or "App"
    max_chars = max(8, WIDTH // 6)
    text = _truncate(name, max_chars)
    if entry["missing_app"]:
        text = _truncate(f"{name} (missing)", max_chars)
    footer_label.text = text


# Title: Page renderer
# Desc: Render the current icon page and cursor.
def render_page():
    # Rebuild only the current page to keep memory usage down.
    global page_start, slot_positions
    while len(icon_group):
        icon_group.pop()
    slot_positions = []

    if not entries:
        cursor_group.x = -1000
        cursor_group.y = -1000
        update_footer()
        return

    page_start = (selected // per_page) * per_page
    for slot in range(per_page):
        idx = page_start + slot
        if idx >= len(entries):
            break
        row = slot // columns
        col = slot % columns
        x = grid_x + col * (ICON_SIZE + ICON_GAP)
        y = grid_y + row * (ICON_SIZE + ICON_GAP)
        entry = entries[idx]
        if entry["bitmap"] is not None:
            grp = displayio.Group(x=x, y=y)
            tg = displayio.TileGrid(entry["bitmap"], pixel_shader=entry["bitmap"].pixel_shader)
            grp.append(tg)
            icon_group.append(grp)
        else:
            icon_group.append(make_placeholder_group(entry["name"], x, y))
        slot_positions.append((idx, x, y))

    update_cursor()
    update_footer()


# Title: Cursor updater
# Desc: Move the highlight to the active icon slot.
def update_cursor():
    # Cursor follows the current selection slot.
    if not entries:
        cursor_group.x = -1000
        cursor_group.y = -1000
        return
    slot = selected - page_start
    if slot < 0 or slot >= len(slot_positions):
        cursor_group.x = -1000
        cursor_group.y = -1000
        return
    _, x, y = slot_positions[slot]
    cursor_group.x = x - 3
    cursor_group.y = y - 3


# Title: Status message
# Desc: Temporarily replace footer text with a message.
def set_status(msg, pause=0.7):
    update_footer(message=msg)
    refresh()
    if pause:
        time.sleep(pause)
    update_footer()


# Title: Time/battery header
# Desc: Update the top line using NTP time and battery.
def update_time(batt_value=None):
    # Match the code.py time/battery line format.
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

def screenshot():
#     # Initialize SD Card & Mount Virtual File System
#     spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
#     cs = digitalio.DigitalInOut(board.SD_CS)
#     sdcard = adafruit_sdcard.SDCard(spi, cs)
#     vfs = storage.VfsFat(sdcard)
#     storage.mount(vfs, "/sd")  # /sd is root dir of SD Card

    print("Taking Screenshot... ")
    save_pixels("/sd/screenshot.bmp", display)
    print("Screenshot Saved")



# --- Initial render ---
render_page()
refresh()

# --- Header update cadence ---
last_update = time.monotonic()
last_batt = -10.0

# --- Main loop ---
while True:
    # Poll input, update header, and launch/view apps.
    # Header refresh: time every second, battery every 5 seconds.
    now = time.monotonic()
    if now - last_update >= 1.0:
        last_update = now
        if now - last_batt >= 5.0:
            last_batt = now
            update_time(inp.read_battery())
        else:
            update_time()
        refresh()

    # Input handling (navigation + launch/view).
    ch = inp.get_char()
    if ch is None:
        time.sleep(0.02)
        continue


    if ch == ord("s"):
        screenshot()

    if ch == KEY_LEFT and selected > 0:
        selected -= 1
    elif ch == KEY_RIGHT and selected < (len(entries) - 1):
        selected += 1
    elif ch == KEY_UP and selected - columns >= 0:
        selected -= columns
    elif ch == KEY_DOWN and selected + columns < len(entries):
        selected += columns
    elif ch == KEY_ENTER and entries:
        entry = entries[selected]
        if entry["missing_app"] or not entry["app"]:
            set_status("Missing app")
        else:
            set_status("Launching...")
            launch_app(entry["app"])
            set_status("Reload blocked")
    elif ch in (KEY_V_UPPER, KEY_V_LOWER) and entries:
        entry = entries[selected]
        if entry["missing_app"] or not entry["app"]:
            set_status("Missing app")
        else:
            set_status("Viewing...")
            view_app(entry["app"])
            set_status("Reload blocked")

    # Page redraw only when crossing page boundaries.
    new_start = (selected // per_page) * per_page if entries else -1
    if new_start != page_start:
        render_page()
    else:
        update_cursor()
        update_footer()
    refresh()
