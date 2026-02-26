"""Magnetic field visualization window: composes mixins and layout.

This is the main window class for the magnetic field GUI. The program entry
point is project root main.py; this module is not named main to avoid confusion.
"""

import threading
import numpy as np
import tkinter as tk

from config.constants import Constants
from gui.common import get_default_font, get_default_font_small, get_button_font

from ._figures import MagneticFieldGUIFiguresMixin
from ._layout import MagneticFieldGUILayoutMixin
from ._serial_esp32 import MagneticFieldGUISerialMixin
from ._animations import MagneticFieldGUIAnimationsMixin


class MagneticFieldGUI(
    MagneticFieldGUIFiguresMixin,
    MagneticFieldGUILayoutMixin,
    MagneticFieldGUISerialMixin,
    MagneticFieldGUIAnimationsMixin,
):
    """Magnetic field visualization: Btot map, 3D vectors/cube, angular velocity, ESP32."""

    def __init__(self, root, data):
        self.root = root
        self.data = data

        try:
            self.Btot_ECEF_ = np.load(f"Btot_magnitude_altitude_{int(Constants.ALTITUDE)}.npy")
        except FileNotFoundError:
            self.Btot_ECEF_ = np.zeros((1, 10, 10))
        self.Btot_magnitude = np.linalg.norm(self.Btot_ECEF_, axis=0)
        if self.Btot_magnitude.ndim == 2:
            self.Btot_magnitude = self.Btot_magnitude[np.newaxis, :, :]

        self.was_stopped = False
        self.pause_flag = False
        self.stopped_flag = False
        self.esp32_pause_event = threading.Event()
        self.esp32_stop_event = threading.Event()
        self.esp32_paused_frame = 0
        self.esp32_was_stopped = False
        self.import_button_pressed = False

        self.roboto_font = get_default_font()
        self.roboto_font2 = get_default_font_small()
        self.custom_font_fixedsys = get_button_font()
        self.cube_origin = Constants.CUBE_ORIGIN

        self.ani_fig1 = None
        self.ani_fig2 = None
        self.ani_fig3 = None

        self.setup_gui()

    def setup_gui(self):
        self.eci_visible = tk.BooleanVar(value=False)
        self.body_visible = tk.BooleanVar(value=False)
        self.r_eci_visible = tk.BooleanVar(value=False)
        self.v_eci_visible = tk.BooleanVar(value=False)
        self.sat_body_visible = tk.BooleanVar(value=False)
        self.body_additional_entries_checkbox = tk.BooleanVar(value=False)
        self.init_ui()
        self.draw_figures()
