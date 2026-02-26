"""Spacecraft parameters window: composes mixins and wires layout.

The program entry point is project root main.py; this module is not named main.
"""

import os

import customtkinter as ctk
from customtkinter import CTk, CTkFrame, CTkScrollableFrame
from PIL import Image, ImageTk

from config.theme import script_dir
from gui.common import (
    get_default_font,
    get_button_font,
    SPACECRAFT_WINDOW_DEFAULT_WIDTH,
    SPACECRAFT_WINDOW_DEFAULT_HEIGHT,
    SPACECRAFT_WINDOW_MIN_WIDTH,
    SPACECRAFT_WINDOW_MIN_HEIGHT,
)
from gui.ui_system import PAD, COL_GAP, ROW_GAP, SECTION_GAP, PREVIEW_ROW_MINSIZE, MAP_ROW_MINSIZE

from ._frames import SpacecraftGUIFramesMixin
from ._simulation import SpacecraftGUISimulationMixin
from ._attitude import SpacecraftGUIAttitudeMixin
from ._figures import SpacecraftGUIFiguresMixin


class SpacecraftGUI(
    SpacecraftGUIFiguresMixin,
    SpacecraftGUIAttitudeMixin,
    SpacecraftGUISimulationMixin,
    SpacecraftGUIFramesMixin,
    CTk,
):
    """Spacecraft parameters window: Keplerian, run sim, deploy, magnetic field viz."""

    def __init__(self):
        super().__init__()
        from config.constants import Constants
        from geopack import geopack
        from spacepy.time import Ticktock

        self.ps = geopack.recalc(Constants.INITIAL_UT)
        self.ticks = Ticktock(Constants.SPECIFIC_TIME, "UTC")
        self.KP_IDX = Constants.KP_IDX
        self.is_calculate_button_pressed = False

        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.title("Spacecraft Parameters")

        self.minsize(SPACECRAFT_WINDOW_MIN_WIDTH, SPACECRAFT_WINDOW_MIN_HEIGHT)
        w, h = SPACECRAFT_WINDOW_DEFAULT_WIDTH, SPACECRAFT_WINDOW_DEFAULT_HEIGHT
        x = (self.winfo_screenwidth() // 2) - (w // 2) - 15
        y = (self.winfo_screenheight() // 2) - (h // 2) - 40
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.after(100, self._start_maximized)

        # Sol ve orta tüm inputlar tam görünsün (Epoch vb. kesilmesin)
        self.grid_columnconfigure(0, weight=0, minsize=410)
        self.grid_columnconfigure(1, weight=0, minsize=440)
        self.grid_columnconfigure(2, weight=1, minsize=380)
        self.grid_rowconfigure(0, weight=1, minsize=400)
        self.grid_rowconfigure(1, weight=0, minsize=44)

        self.custom_font = get_default_font()
        self.custom_font_fixedsys = get_button_font()

        # Sol kenar PAD; 1–2 ve 2–3 arası COL_GAP (sol taraftaki boşlukla aynı toplam)
        self.left_frame = CTkScrollableFrame(self)
        self.left_frame.grid(row=0, column=0, padx=(PAD, COL_GAP), pady=PAD, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.right_frame = CTkScrollableFrame(self)
        self.right_frame.grid(row=0, column=1, padx=(COL_GAP, COL_GAP), pady=PAD, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.third_frame = CTkScrollableFrame(self)
        self.third_frame.grid(row=0, column=2, padx=(COL_GAP, PAD), pady=PAD, sticky="nsew")
        self.third_frame.grid_columnconfigure(0, weight=1)

        self.third_content = CTkFrame(self.third_frame)
        self.third_content.grid(row=0, column=0, sticky="nsew")
        self.third_content.grid_columnconfigure(0, weight=1)
        self.third_content.grid_rowconfigure(0, weight=0, minsize=28)
        self.third_content.grid_rowconfigure(1, weight=1, minsize=PREVIEW_ROW_MINSIZE)
        self.third_content.grid_rowconfigure(2, weight=0)
        self.third_content.grid_rowconfigure(3, weight=0)
        self.third_content.grid_rowconfigure(4, weight=0)
        self.third_content.grid_rowconfigure(5, weight=1, minsize=MAP_ROW_MINSIZE)
        self.third_content.grid_rowconfigure(6, weight=0, minsize=44)
        self._third_content_width_after_id = None
        self._third_content_width_delay_ms = 150
        self._last_third_content_width = -1
        self.third_frame.bind("<Configure>", self._on_third_frame_configure)

        self.create_time_coord_system_frame(self.left_frame)
        self.create_keplerian_elements_frame(self.left_frame)
        self.create_physical_properties_frame(self.left_frame)
        self.create_aerodynamic_properties_frame(self.left_frame)
        self.create_deployment_properties_frame(self.left_frame)
        self.create_spacecraft_constants_frame(self.right_frame)
        self.create_simulation_parameters_frame(self.right_frame)
        self.add_angular_rate_section(self.right_frame)

        self.add_preview_section_header(self.third_content)
        self.top_preview_canvas_frame = self.create_top_preview_canvas_frame(self.third_content)
        self.top_preview_canvas = self.create_canvas(self.top_preview_canvas_frame, row=0, column=0)
        self.cube_frame = self.top_preview_canvas
        self.setup_initial_preview_figure(self.top_preview_canvas)
        self.add_quaternion_section(self.third_content)
        self.add_euler_angles_section(self.third_content)
        self.add_map_section_header(self.third_content)
        self.canvas_frame = self.create_canvas_frame(self.third_content)
        self.canvas1 = self.create_canvas(self.canvas_frame, row=0, column=0)
        self.add_altitude_section(self.third_content)

        self.create_bottom_bar()
        self.bind_euler_entries()
        self.bind_quaternion_entries()
        # Default: quaternion active with 0,0,0,1; sync euler to 0,0,0
        self.toggle_quaternion()
        self.update_euler_from_quaternion()

        self.display_logo(self.canvas1)

    def on_calculate_button_press(self):
        self.is_calculate_button_pressed = True

    def display_logo(self, canvas):
        image_path = os.path.join(script_dir, "gumushlogo.png")
        if not os.path.isfile(image_path):
            image_path = "C:/Users/GumushAerospace/Desktop/taurus/gumushlogo.png"
        if not os.path.isfile(image_path):
            return
        self.logo_image = Image.open(image_path)
        self.logo_image = self.logo_image.resize((128, 115), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(self.logo_image)
        canvas.create_image(400, 165, anchor="center", image=self.logo_photo)
        canvas.image = self.logo_photo

    def open_deployment_window(self):
        from gui.impulsive_burn_gui import ImpulsiveBurnGUI
        burn_window = ctk.CTkToplevel(self)
        ImpulsiveBurnGUI(burn_window, self)

    def _start_maximized(self):
        """Pencere gösterildikten sonra tam ekran (Windows zoomed)."""
        try:
            self.state("zoomed")
        except Exception:
            pass

    def close_window(self):
        self.quit()
        self.destroy()

    def _on_third_frame_configure(self, event):
        """Debounced: handler sadece boyutu kaydeder, geometry değiştirmez (döngüyü kırmak)."""
        w = max(0, event.width)
        if getattr(self, "_third_content_width_after_id", None):
            self.after_cancel(self._third_content_width_after_id)
        self._pending_third_width = w
        self._third_content_width_after_id = self.after(
            self._third_content_width_delay_ms,
            self._sync_third_content_width,
        )

    def _sync_third_content_width(self):
        """Sadece debounced callback'te ve fark >= 2px ise width set (configure→configure döngüsü yok)."""
        self._third_content_width_after_id = None
        w = getattr(self, "_pending_third_width", 0)
        if w <= 0 or not hasattr(self, "third_content"):
            return
        try:
            current = self.third_content.winfo_width()
            if current <= 0:
                current = getattr(self, "_last_third_content_width", -1)
            if abs(w - current) < 2:
                return
            self.third_content.configure(width=w)
            self._last_third_content_width = w
        except Exception:
            pass

    def update_progress(self, value, step, num_step):
        self.progress_bar.set(value / 100.0)
        self.progress_label.configure(text=f"{value:.1f}%")
        if self.is_calculate_button_pressed:
            self.step_label.configure(text=f"{step} / {self.total_steps}")
        else:
            self.step_label.configure(text=f"{step} / {num_step}")
