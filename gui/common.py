"""Shared GUI resources: fonts, colors, and layout constants.

Use these everywhere so one change updates all windows. The program has a single
entry point at project root (main.py); GUI packages expose their window class
from window.py, not main.py.
"""

from customtkinter import CTkFont

# ─── Fonts (same names everywhere) ───────────────────────────────────────────
FONT_FAMILY = "Century Gothic"
FONT_FAMILY_FIXED = "Fixedsys"

def font_standard(size=12):
    return CTkFont(family=FONT_FAMILY, size=size)

def font_small(size=10):
    return CTkFont(family=FONT_FAMILY, size=size)

def font_buttons(size=12):
    return CTkFont(family=FONT_FAMILY_FIXED, size=size)

# Use get_default_font() etc. in window __init__ (after root exists)
def get_default_font():
    return font_standard(12)


def get_default_font_small():
    return font_small(10)


def get_button_font():
    return font_buttons(12)

# ─── Colors (matplotlib and CTk) ─────────────────────────────────────────────
FIGURE_FACECOLOR = "#2B2B2B"
AXIS_GRID_COLOR = "#03A062"
TEXT_COLOR = "#FFFFFF"
LEGEND_FRAME_FACE = "#f0f0f0"
LEGEND_FRAME_EDGE = "#000000"
# Section header background (tüm sütunlarda aynı mavi)
SECTION_HEADER_BG = "#1f538d"
SECTION_HEADER_HOVER = "#2a6bb8"

# ─── Spacing: from UI design system (single source of truth) ──────────────────
from gui.ui_system import SPACE_1, SPACE_2

UI_SPACING = SPACE_2   # 8
UI_PAD_SMALL = SPACE_1  # 4

# ─── Window defaults ─────────────────────────────────────────────────────────
SPACECRAFT_WINDOW_MIN_WIDTH = 1160
SPACECRAFT_WINDOW_MIN_HEIGHT = 640
SPACECRAFT_WINDOW_DEFAULT_WIDTH = 1500
SPACECRAFT_WINDOW_DEFAULT_HEIGHT = 800

MAGNETIC_WINDOW_MIN_WIDTH = 1280
MAGNETIC_WINDOW_MIN_HEIGHT = 720
