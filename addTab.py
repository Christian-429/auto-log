import time
import pyautogui as pg
import pyperclip as clip
from config import ADD_TAB_CORDS as CORDS
# tab name must be in format 20xx-20xx, e.g. 2026-2027


CLICK_SETTLE_DELAY = 0.2
DATA_RANGE = 'A7:G50'
DOWN_PRESS_INTERVAL = 0.3
ID_LIST_PATH = 'input.txt'

pg.PAUSE = 0.3
STUDENT_START = 1

def get_tab_name():
    return input('Enter the new year to be added (format: 20xx-20xx): ')


def get_student_count(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        print(lines[STUDENT_START])
    return len(lines)


def click(coord_key):
    pg.moveTo(CORDS[coord_key])
    pg.click()


def select_student_row(student_index):
    click('tab2')
    click('w_ID')
    pg.press('down', presses=student_index, interval=DOWN_PRESS_INTERVAL)


def confirm_selection():
    pg.press('enter')
    time.sleep(CLICK_SETTLE_DELAY)
    pg.press('tab')
    time.sleep(CLICK_SETTLE_DELAY)
    pg.press('enter')
    time.sleep(CLICK_SETTLE_DELAY + 4)


def duplicate_and_rename_sheet(tab_name):
    click('sheet_tab1')
    time.sleep(CLICK_SETTLE_DELAY)
    pg.rightClick()
    time.sleep(CLICK_SETTLE_DELAY)

    pg.moveTo(CORDS['duplicate_button'])
    pg.click()

    pg.moveTo(CORDS['sheet_tab2'])
    pg.rightClick()
    pg.moveTo(CORDS['rename_button'])
    pg.click()

    clip.copy(tab_name)
    pg.hotkey('ctrl', 'v')

    click('click_off_area')


def move_new_sheet_left():
    pg.moveTo(CORDS['sheet_tab2'])
    pg.rightClick()
    pg.moveTo(CORDS['move_left_button'])
    pg.click()


def clear_data_range():
    click('sheet_tab1')
    click('range_box')
    pg.write(DATA_RANGE)
    pg.press('enter')
    pg.press('backspace')


def close_and_reload():
    click('close_tab_3')
    click('reload_tab_2')
    click('reload_button')
    time.sleep(2)


def process_student(tab_name, student_index):
    select_student_row(student_index)
    confirm_selection()
    duplicate_and_rename_sheet(tab_name)
    move_new_sheet_left()
    clear_data_range()
    close_and_reload()


def main():
    tab_name = get_tab_name()
    student_count = get_student_count(ID_LIST_PATH)

    time.sleep(5)
    pg.press('down')

    for curr_student in range(STUDENT_START, student_count + 1):
        process_student(tab_name, curr_student)


if __name__ == '__main__':
    main()