"""Helpers for using a recorded screen layout on different display sizes."""


def scale_coordinates(coordinates, reference_size, screen_size=None):
    """Map points captured on ``reference_size`` to the current display.

    The browser must be maximized and use the same browser zoom and
    operating-system display scaling as the display used for calibration.
    """
    reference_width, reference_height = reference_size
    if screen_size is None:
        # Import only when an actual screen measurement is needed.  This keeps
        # the pure scaling calculation easy to test without GUI dependencies.
        import pyautogui as pg

        screen_size = pg.size()

    screen_width, screen_height = screen_size
    x_scale = screen_width / reference_width
    y_scale = screen_height / reference_height

    return {
        name: (round(x * x_scale), round(y * y_scale))
        for name, (x, y) in coordinates.items()
    }
