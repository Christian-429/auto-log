import time
import pyautogui as pg
import pyperclip as clip

from config import NAME, POSITION, CONTACT_MODE, CORDS, INPUT_FILE

pg.PAUSE = 0.3

SENTINEL = "__NOTHING_COPIED__"
COPY_SETTLE_DELAY = 0.3
CLICK_SETTLE_DELAY = 0.2


def get_student_ids(filename):
    with open(filename, "r") as file:
        return [line.strip() for line in file if line.strip()]


def parse_row(raw):
    cols = [c.strip() for c in raw.split("\t")]

    raw_name = cols[0]
    date = cols[1]
    service_field = cols[6]
    note = cols[7]

    name = NAME.get(raw_name, raw_name)
    position = POSITION.get(raw_name, "")

    tokens = [t.strip() for t in service_field.split(",")]
    contact = next((CONTACT_MODE[t] for t in tokens if t in CONTACT_MODE), "")

    return [date, name, position, contact, "", note]


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


def collect_appointments(student_id):
    select_student(student_id)

    appointments = []
    prev_raw = None

    while True:
        raw = copy_current_row()

        clean = parse_row(raw)
        if appointments and clean == appointments[0]: # is this new page the same as the first one?
            break
        if raw is None or raw == prev_raw: # the list has stopped advancing
            next_page()
            continue

        appointments.append(clean)
        prev_raw = raw
        pg.press("down")
    return appointments

def next_page():
    pg.moveTo(CORDS["next_button"])
    pg.click()
    time.sleep(CLICK_SETTLE_DELAY)
    pg.moveTo(CORDS['sort_grid'])
    for i in range(4):
        pg.click()
    pg.moveTo(CORDS["app_first_row"])
    pg.click()


#after collected appointments funcs
# so appointments has all of ONE student appointments

def main():
    student_ids = get_student_ids(INPUT_FILE)
    time.sleep(5)

    for student_id in student_ids:
        appointments = collect_appointments(student_id)
        print(appointments)


if __name__ == "__main__":
    main()