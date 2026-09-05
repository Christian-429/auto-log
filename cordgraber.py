import pyautogui as pg
from pynput.mouse import Listener, Button

# Get screen size
screenWidth, screenHeight = pg.size()
print(f"Screen size: {screenWidth} x {screenHeight}")

# This function will be called whenever a mouse event occurs
def on_click(x, y, button, pressed):
    if button == Button.left and pressed:
        # Get current mouse position at the moment of click
        currentMouseX, currentMouseY = pg.position()
        print(f"Left click detected at: ({currentMouseX}, {currentMouseY})")
with Listener(on_click=on_click) as listener:
    print("Listening for left clicks... Press Ctrl+C to stop")
    listener.join()  # This keeps the script running