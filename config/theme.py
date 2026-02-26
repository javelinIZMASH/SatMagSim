"""Theme and font setup for SatMagSim Extended GUI.

Resolves paths for Roboto font and dark-blue theme (project folder first,
then fallback). Sets CustomTkinter appearance and sets module-level
``roboto_prop`` for use in figures.

Call ``setup_theme()`` once before creating the main application window.
"""

import os

from matplotlib.font_manager import FontProperties


def _script_dir():
    """Return the directory containing the config package (project root)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Project root; used by main and GUI for asset paths.
script_dir = _script_dir()

# Set by setup_theme(); use in GUI for matplotlib figures.
roboto_prop = FontProperties()


def setup_theme():
    """Apply dark theme and resolve font/theme paths.

    Sets CustomTkinter appearance mode and color theme. Prefers files in
    project directory (Roboto-Regular.ttf, dark-blue.json); falls back
    to legacy paths if not found. Sets module-level ``roboto_prop`` for
    matplotlib (Roboto if file exists, else default).
    """
    global roboto_prop
    from customtkinter import set_appearance_mode, set_default_color_theme

    roboto_path = os.path.join(script_dir, "Roboto-Regular.ttf")
    if not os.path.isfile(roboto_path):
        roboto_path = "C:/Users/GumushAerospace/Desktop/taurus/Roboto-Regular.ttf"

    theme_path = os.path.join(script_dir, "dark-blue.json")
    if not os.path.isfile(theme_path):
        theme_path = "C:/Users/GumushAerospace/Desktop/taurus/dark-blue.json"

    set_appearance_mode("dark")
    set_default_color_theme(
        theme_path if os.path.isfile(theme_path) else "dark-blue"
    )

    roboto_prop = (
        FontProperties(fname=roboto_path)
        if os.path.isfile(roboto_path)
        else FontProperties()
    )
