import time
from datetime import datetime

import pyautogui as pg
import pyperclip as clip

from config import NAME, POSITION, CONTACT_MODE, CORDS, INPUT_FILE


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

pg.PAUSE = 0.3

SENTINEL = "__NOTHING_COPIED__"
COPY_SETTLE_DELAY = 0.3
CLICK_SETTLE_DELAY = 0.2


# ---------------------------------------------------------------------------
# Input / data helpers
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
# Appointment grid: reading appointments for one student
# ---------------------------------------------------------------------------

def copy_current_row():
    clip.copy(SENTINEL)
    pg.hotkey("ctrl", "c")
    time.sleep(COPY_SETTLE_DELAY)
    data = clip.paste()

    if data == SENTINEL or "\t" not in data:
        return None
    return data


def select_student(student_id):
    pg.moveTo(CORDS["tab1"])
    pg.leftClick()

    pg.moveTo(CORDS["studentName"])
    pg.doubleClick()

    pg.press("Backspace")
    pg.write(student_id)

    pg.moveTo(CORDS["app_first_row"])
    pg.leftClick()
    time.sleep(CLICK_SETTLE_DELAY)


# Moves to the next page on the grid page
def next_page():
    pg.moveTo(CORDS["next_button"])
    pg.click()
    time.sleep(CLICK_SETTLE_DELAY)
    pg.click(CORDS['top_of_grid'], clicks= 3)
    # pg.moveTo(CORDS["sort_grid"])
    pg.click(CORDS["sort_grid"], clicks=3)
    pg.moveTo(CORDS["app_first_row"])
    pg.click()


def collect_appointments(student_id):
    select_student(student_id)

    appointments = []
    prev_raw = None
    
    while True:
        raw = copy_current_row()

        clean = parse_row(raw)

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
# Sheets: after appointments are collected
# (`appointments` holds all of ONE student's appointments)
# ---------------------------------------------------------------------------

def go_to_beginning():
    pg.moveTo(CORDS["sheets_menu"])
    pg.click()
    pg.moveTo(CORDS["beginning_log_tab"])
    pg.click()
    pg.moveTo(CORDS["w_ID"])
    pg.click()


def move_to_next_tab():
    pg.hotkey("alt", "up")
    pg.press("down", presses=6, interval=0.05)


def find_student_log(student_id):
    pg.moveTo(CORDS["tab2"])
    pg.click()
    pg.moveTo(CORDS["w_ID"])
    pg.click()

    is_found = False
    while not is_found:
        pg.press("down")
        pg.hotkey("ctrl", "c")
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

    if first_date.month in (1,2,3,4,5, 6, 7, 8):
        curr_year = first_date.year - 1
    else:
        curr_year = first_date.year

    end_year = curr_year + 1
    for app in appts:
        clip.copy("\t".join(app))
        if datetime.strptime(app[0], "%m/%d/%Y") > datetime.strptime(f"9/1/{end_year}", "%m/%d/%Y"):
            move_to_next_tab()
            end_year += 1
        pg.hotkey("ctrl", "v")
        pg.press("down")
    time.sleep(CLICK_SETTLE_DELAY)
    pg.moveTo(CORDS["close_tab_3"])
    time.sleep(CLICK_SETTLE_DELAY)
    pg.click()
    pg.moveTo(CORDS["reload_tab_2"])
    pg.click()
    pg.moveTo(CORDS["reload_button"])
    pg.click()


# ---------------------------------------------------------------------------
# Entry point
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