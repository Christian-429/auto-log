import sys
import time
from datetime import datetime

import pyautogui as pg
import pyperclip as clip

from config import (
    NAME,
    POSITION,
    CONTACT_MODE,
    CORDS,
    INPUT_FILE,
    REFERENCE_SCREEN_SIZE,
)
from screen_coordinates import scale_coordinates


# ---------------------------------------------------------------------------
# Application settings and screen layout
# ---------------------------------------------------------------------------

pg.PAUSE = 0.25

RESET = "__NOTHING_COPIED__"
COPY_SETTLE_DELAY = 0.25
CLICK_SETTLE_DELAY = 0.2

MOD = "command" if sys.platform == "darwin" else "ctrl"


# CORDS in config.py remain easy to calibrate (2880 x 1800); all clicks below
# use display-relative versions of those points.
CORDS = scale_coordinates(CORDS, REFERENCE_SCREEN_SIZE)


def activate_browser_tab(number):
    pg.hotkey(MOD, str(number))


# ---------------------------------------------------------------------------
# Input and appointment-row helpers
# ---------------------------------------------------------------------------

def get_student_ids(filename):
    with open(filename, "r") as file:
        return [line.strip() for line in file if line.strip()]


def sort_by_date(rows):
    return sorted(rows, key=lambda row: datetime.strptime(row[0], "%m/%d/%Y"))


def parse_row(raw):
    try:
        cols = [c.strip() for c in raw.split("\t")]
    except AttributeError:
        return False

    raw_name = cols[0]
    date = cols[1]
    service_field = cols[6]
    note = cols[7]

    name = NAME.get(raw_name, raw_name)
    position = POSITION.get(raw_name, "")

    tokens = [t.strip() for t in service_field.split(",")]
    contact = next((CONTACT_MODE[t] for t in tokens if t in CONTACT_MODE), "")

    return [date, name, position, contact, "", note]


# ---------------------------------------------------------------------------
# Appointment grid: select a student and collect their appointments
# ---------------------------------------------------------------------------

def copy_current_row():
    clip.copy(RESET)
    pg.hotkey(MOD, "c")
    time.sleep(COPY_SETTLE_DELAY)
    data = clip.paste()

    if data == RESET or "\t" not in data:
        return None
    return data


def select_student(student_id):
    # The appointment site must be in browser tab 1.
    activate_browser_tab(1)

    pg.doubleClick(CORDS["studentName"])

    pg.press("Backspace")
    pg.write(student_id)

    pg.leftClick(CORDS["app_first_row"])
    time.sleep(CLICK_SETTLE_DELAY)


def next_page():
    pg.click(CORDS["next_button"])
    time.sleep(CLICK_SETTLE_DELAY)
    pg.click(CORDS['top_of_grid'], clicks=3)
    # pg.moveTo(CORDS["sort_grid"])
    pg.click(CORDS["sort_grid"], clicks=3)
    time.sleep(0.15)
    pg.click(CORDS["app_first_row"])


def collect_appointments(student_id):
    select_student(student_id)

    appointments = []
    prev_raw = None

    while True:
        raw = copy_current_row()

        clean = parse_row(raw)

        if appointments and appointments[0] == ['', '', '', '', '', '']:
            appointments.pop(0)
        if not clean:
            raw = copy_current_row()
            clean = parse_row(raw)
        if appointments and (clean == appointments[0]):  # is this new page the same as the first one?
            break
        if raw is None or raw == prev_raw:  # the list has stopped advancing
            next_page()
            raw = copy_current_row()
            if raw == prev_raw:
                pg.press("down")
            continue

        appointments.append(clean)
        prev_raw = raw
        pg.press("down")
    return appointments


# ---------------------------------------------------------------------------
# Student sheet: locate the log and paste appointment rows
# ---------------------------------------------------------------------------

def go_to_beginning():
    """Navigate the open student log sheet to its first entry row."""
    pg.click(CORDS["sheets_menu"])
    pg.click(CORDS["beginning_log_tab"])
    pg.click(CORDS["w_ID"])


def move_to_next_tab():
    """Move from the current school-year sheet tab to the next one."""
    pg.hotkey("alt", "up")
    pg.press("down", presses=6, interval=0.05)


def find_student_log(student_id):
    # The student-log sheet must be in browser tab 2.
    activate_browser_tab(2)
    pg.click(CORDS["w_ID"])

    is_found = False
    while not is_found:
        pg.press("down")
        pg.hotkey(MOD, "c")
        if clip.paste() == student_id:
            pg.press("enter")
            time.sleep(CLICK_SETTLE_DELAY)
            pg.press("tab")
            time.sleep(CLICK_SETTLE_DELAY)
            pg.press("enter")
            time.sleep(CLICK_SETTLE_DELAY + 4)
            go_to_beginning()
            pg.press("down", presses=6, interval=0.05)
            return True
    print("unable to find student")
    return is_found


def write_to_sheets(appts, student_id):
    find_student_log(student_id)

    first_date = datetime.strptime(appts[0][0], "%m/%d/%Y")

    if first_date.month in (1, 2, 3, 4, 5, 6, 7, 8):
        curr_year = first_date.year - 1
    else:
        curr_year = first_date.year

    end_year = curr_year + 1
    for app in appts:
        clip.copy("\t".join(app))
        if datetime.strptime(app[0], "%m/%d/%Y") > datetime.strptime(f"9/1/{end_year}", "%m/%d/%Y"):
            move_to_next_tab()
            end_year += 1
        pg.hotkey(MOD, "v")
        pg.press("down")
    time.sleep(CLICK_SETTLE_DELAY)
    # The student-specific sheet opens in browser tab 3.  Closing it by tab
    # number works even when browser tabs have different widths.
    activate_browser_tab(3)
    time.sleep(CLICK_SETTLE_DELAY)
    pg.hotkey(MOD, "w")
    activate_browser_tab(2)
    pg.click(CORDS["reload_tab_2"])
    pg.click(CORDS["reload_button"])


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

def main():
    student_ids = get_student_ids(INPUT_FILE)
    time.sleep(5)

    for student_id in student_ids:
        appointments = sort_by_date(collect_appointments(student_id))
        write_to_sheets(appointments, student_id)
        print(f"finished {student_id}")


if __name__ == "__main__":
    main()
    print("Done!")
