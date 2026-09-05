import pyautogui as pg
# from pynput.mouse import Listener, Button


screenWidth, screenHeight = pg.size()
print(f"Screen size: {screenWidth} x {screenHeight}")

cords = {
    'tab1' : (256,38),
    'tab2' : (641,38),
    'tab3' : (1026,38),
    'tab4' : (1411,38),
    'studentName' : (313,1456),
    'print' : (741,1540),
}

def getIDs(filename):
    with open(filename, 'r') as file:
        studentIDs= []
        for line in file:
            studentIDs.append(line.strip())
    return studentIDs


if __name__ == "__main__":
    studentIDs = getIDs('input.txt')
    #for student in studentIDs:
    pg.sleep(5)
    pg.moveTo(cords['tab1'])
    pg.leftClick()
    pg.moveTo(cords['studentName'])
    pg.doubleClick()
    pg.press('Backspace')
    pg.write(studentIDs[3])
    pg.moveTo(cords['print'])
    pg.leftClick()

