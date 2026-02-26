"""Parameter panels (frames), progress bar, and control buttons for SpacecraftGUI.

Layout follows gui.ui_system (single UI contract): spacing, panel, form row, section, action.
"""

import tkinter as tk
import customtkinter as ctk

from customtkinter import (
    CTkFrame,
    CTkButton,
    CTkEntry,
    CTkFont,
    CTkLabel,
    CTkProgressBar,
    CTkCheckBox,
)

from config.constants import Constants
from gui.common import SECTION_HEADER_BG, SECTION_HEADER_HOVER
from gui.ui_system import (
    PAD,
    ROW_GAP,
    SECTION_GAP,
    LABEL_COL_MINSIZE,
    ENTRY_MIN_WIDTH,
    ENTRY_COL_MAX,
    MIDDLE_COL_ENTRY_WIDTH,
    RIGHT_COL_ENTRY_WIDTH,
    FORM_ROW_PADX,
    BORDER_WIDTH,
    BORDER_COLOR,
    CANVAS_BG,
    SECTION_HEADER_PADY,
    ACTION_BUTTON_WIDTH,
    ACTION_BUTTON_HEIGHT,
    ACTION_GAP,
    BOTTOM_BAR_ROW_HEIGHT,
    BOTTOM_BAR_PAD_V,
)


def _section_header(parent, text, font, row=0, columnspan=2):
    """Place section header at row; same font, padding, mavi arka plan."""
    btn = CTkButton(
        parent, text=text, font=font,
        fg_color=SECTION_HEADER_BG, hover_color=SECTION_HEADER_HOVER,
    )
    btn.grid(row=row, column=0, columnspan=columnspan, pady=SECTION_HEADER_PADY, sticky="w")
    return row + 1


class SpacecraftGUIFramesMixin:
    """Mixin: all create_*_frame, add_*_section, create_bottom_bar; layout via ui_system."""

    def add_preview_section_header(self, parent):
        """Sağ sütun row 0: mavi section başlığı."""
        _section_header(parent, "Preview (3D) / Normalized Vectors", self.custom_font, row=0, columnspan=1)

    def add_map_section_header(self, parent):
        """Sağ sütun row 4: harita bölümü başlığı."""
        _section_header(parent, "Magnetic Field Magnitude (ECEF)", self.custom_font, row=4, columnspan=1)

    def create_top_preview_canvas_frame(self, parent):
        """Section A — Preview (3D) canvas panel, CANVAS_BG, border. Grid row=1."""
        frame = CTkFrame(
            parent,
            fg_color=CANVAS_BG,
            border_width=BORDER_WIDTH,
            border_color=BORDER_COLOR,
        )
        frame.grid(row=1, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        return frame

    def create_canvas_frame(self, parent):
        """Section C — Field/Map canvas: same style as preview panel. Grid row=4."""
        canvas_frame = CTkFrame(
            parent,
            fg_color=CANVAS_BG,
            border_width=BORDER_WIDTH,
            border_color=BORDER_COLOR,
        )
        canvas_frame.grid(row=5, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        canvas_frame.grid_columnconfigure(0, weight=1)
        canvas_frame.grid_rowconfigure(0, weight=1)
        return canvas_frame

    def create_time_coord_system_frame(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=0, column=0, padx=PAD, pady=PAD, sticky="nsew")
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        frame.grid_columnconfigure(1, weight=0, minsize=ENTRY_COL_MAX)
        r = _section_header(frame, "Time and Coordinate System", self.custom_font, row=0)
        labels = ["DateFormat:", "CoordinateSystem:", "Epoch"]
        defaults = ["UTCGregorian", "EarthMJ2000Eq", Constants.SPECIFIC_TIME_STR]
        for i, (label, default_value) in enumerate(zip(labels, defaults)):
            CTkLabel(frame, text=label, font=self.custom_font, anchor="w").grid(
                row=r + i, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
            )
            entry = CTkEntry(frame, font=self.custom_font, width=ENTRY_COL_MAX)
            entry.grid(row=r + i, column=1, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, default_value)
            if label == "Epoch":
                self.epoch_entry = entry
            if label in ["DateFormat:", "CoordinateSystem:"]:
                entry.configure(state="disabled")

    def create_keplerian_elements_frame(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=1, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        frame.grid_columnconfigure(1, weight=0, minsize=ENTRY_COL_MAX)
        r = _section_header(frame, "Keplerian Elements", self.custom_font, row=0)
        labels = ["Semi-major axis (km)", "Eccentricity", "Inclination (deg)", "RAAN (deg)", "AOP (deg)", "TA (deg)"]
        keys = ["sma", "ecc", "inc", "ra", "aop", "ta"]
        for i, (label, key) in enumerate(zip(labels, keys)):
            CTkLabel(frame, text=label, font=self.custom_font, anchor="w").grid(
                row=r + i, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
            )
            entry = CTkEntry(frame, font=self.custom_font, width=ENTRY_COL_MAX)
            entry.grid(row=r + i, column=1, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, Constants.SATELLITE_PARAMS[key])
            if key == "sma":
                self.semi_major_axis_entry = entry
            elif key == "ecc":
                self.ecc_entry = entry
            elif key == "inc":
                self.inc_entry = entry
            elif key == "ra":
                self.ra_entry = entry
            elif key == "aop":
                self.aop_entry = entry
            elif key == "ta":
                self.ta_entry = entry

    def update_keplerian_elements(self):
        """Refresh Keplerian entry fields from Constants.SATELLITE_PARAMS."""
        self.semi_major_axis_entry.delete(0, "end")
        self.semi_major_axis_entry.insert(0, Constants.SATELLITE_PARAMS["sma"])
        self.ecc_entry.delete(0, "end")
        self.ecc_entry.insert(0, Constants.SATELLITE_PARAMS["ecc"])
        self.inc_entry.delete(0, "end")
        self.inc_entry.insert(0, Constants.SATELLITE_PARAMS["inc"])
        self.ra_entry.delete(0, "end")
        self.ra_entry.insert(0, Constants.SATELLITE_PARAMS["ra"])
        self.aop_entry.delete(0, "end")
        self.aop_entry.insert(0, Constants.SATELLITE_PARAMS["aop"])
        self.ta_entry.delete(0, "end")
        self.ta_entry.insert(0, Constants.SATELLITE_PARAMS["ta"])

    def create_physical_properties_frame(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=2, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        frame.grid_columnconfigure(1, weight=0, minsize=ENTRY_COL_MAX)
        r = _section_header(frame, "Physical Properties and Surface Areas", self.custom_font, row=0)
        for i, (label, key) in enumerate(zip(["DryMass (kg)", "DragArea (m^2)", "SRPArea (m^2)"], ["dry_mass", "drag_area", "srp_area"])):
            CTkLabel(frame, text=label, font=self.custom_font, anchor="w").grid(
                row=r + i, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
            )
            entry = CTkEntry(frame, font=self.custom_font, width=ENTRY_COL_MAX)
            entry.grid(row=r + i, column=1, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, Constants.SATELLITE_PARAMS[key])
            if key == "dry_mass":
                self.dry_mass_entry = entry
            elif key == "drag_area":
                self.drag_area_entry = entry
            else:
                self.srp_area_entry = entry

    def create_aerodynamic_properties_frame(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=3, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        frame.grid_columnconfigure(1, weight=0, minsize=ENTRY_COL_MAX)
        r = _section_header(frame, "Aerodynamic and Solar Radiation Properties", self.custom_font, row=0)
        labels_vals = [("Cr", Constants.SATELLITE_PARAMS["cr"]), ("Cd", Constants.SATELLITE_PARAMS["cd"]), ("MagneticIndex (0-6)", "6")]
        for i, (label, default_value) in enumerate(labels_vals):
            CTkLabel(frame, text=label, font=self.custom_font, anchor="w").grid(
                row=r + i, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
            )
            entry = CTkEntry(frame, font=self.custom_font, width=ENTRY_COL_MAX)
            entry.grid(row=r + i, column=1, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, default_value)
            if label == "Cr":
                self.cr_entry = entry
            elif label == "Cd":
                self.cd_entry = entry
            else:
                self.mag_index_entry = entry

    def create_deployment_properties_frame(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=4, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        frame.grid_columnconfigure(1, weight=0, minsize=ENTRY_COL_MAX)
        r = _section_header(frame, "Deployment Scenario", self.custom_font, row=0)
        labels = ["Before Seperation (sec)", "Deployment Timer (min)"]
        defaults = [Constants.SEPERATION_TIME, Constants.DEPLOYMENT_TIMER]
        for i, (label, default_value) in enumerate(zip(labels, defaults)):
            CTkLabel(frame, text=label, font=self.custom_font, anchor="w").grid(
                row=r + i, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
            )
            entry = CTkEntry(frame, font=self.custom_font, width=ENTRY_COL_MAX)
            entry.grid(row=r + i, column=1, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, default_value)
            if "Seperation" in label:
                self.seperation_entry = entry
            else:
                self.deployment_timer_entry = entry

    def create_spacecraft_constants_frame(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=0, column=0, padx=PAD, pady=PAD, sticky="nsew")
        for c in range(3):
            frame.grid_columnconfigure(c, weight=0, minsize=MIDDLE_COL_ENTRY_WIDTH)
        r = _section_header(frame, "Disturbance Torques (Nm)", self.custom_font, row=0, columnspan=3)
        self.torque_entries = []
        for i, value in enumerate(Constants.DISTURBANCE_TORQUES):
            entry = CTkEntry(frame, font=self.custom_font, width=MIDDLE_COL_ENTRY_WIDTH)
            entry.grid(row=r, column=i, padx=FORM_ROW_PADX, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, value)
            self.torque_entries.append(entry)
        r += 1
        CTkLabel(frame, text="Inertia Matrix (kg*m^2)", font=self.custom_font, anchor="w").grid(
            row=r, column=0, columnspan=3, pady=SECTION_HEADER_PADY, sticky="w"
        )
        r += 1
        self.inertia_matrix_entries = []
        for i in range(3):
            row_entries = []
            for j in range(3):
                entry = CTkEntry(frame, font=self.custom_font, width=MIDDLE_COL_ENTRY_WIDTH)
                entry.grid(row=r + i, column=j, padx=FORM_ROW_PADX, pady=(0, ROW_GAP), sticky="ew")
                entry.insert(0, Constants.J_MATRIX[i][j])
                row_entries.append(entry)
            self.inertia_matrix_entries.append(row_entries)
        r += 3
        CTkLabel(frame, text="Proportional Constant for control law", font=self.custom_font, anchor="w").grid(
            row=r, column=0, columnspan=3, pady=SECTION_HEADER_PADY, sticky="w"
        )
        r += 1
        self.prop_const_entry = CTkEntry(frame, font=self.custom_font, width=MIDDLE_COL_ENTRY_WIDTH)
        self.prop_const_entry.grid(row=r, column=0, pady=(0, ROW_GAP), sticky="ew")
        self.prop_const_entry.insert(0, "0.007")
        r += 1
        CTkLabel(frame, text="W-Noise (rad/s)", font=self.custom_font, anchor="w").grid(
            row=r, column=0, columnspan=3, pady=(0, ROW_GAP), sticky="w"
        )
        r += 1
        self.w_noise_entry = CTkEntry(frame, font=self.custom_font, width=MIDDLE_COL_ENTRY_WIDTH)
        self.w_noise_entry.grid(row=r, column=0, pady=(0, ROW_GAP), sticky="ew")
        self.w_noise_entry.insert(0, Constants.W_NOISE_SCALE)
        r += 1
        CTkLabel(frame, text="B-Noise (nT)", font=self.custom_font, anchor="w").grid(
            row=r, column=0, columnspan=3, pady=(0, ROW_GAP), sticky="w"
        )
        r += 1
        self.b_noise_entry = CTkEntry(frame, font=self.custom_font, width=MIDDLE_COL_ENTRY_WIDTH)
        self.b_noise_entry.grid(row=r, column=0, pady=(0, ROW_GAP), sticky="ew")
        self.b_noise_entry.insert(0, Constants.BTOT_NOISE_SCALE)

    def create_simulation_parameters_frame(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=1, column=0, columnspan=3, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        frame.grid_columnconfigure(1, weight=0, minsize=ENTRY_COL_MAX)
        r = _section_header(frame, "Simulation Parameters", self.custom_font, row=0)
        labels = ["Total Simulation Time (sec)", "Time Step (sec)", "Interval (ms)", "Resolution"]
        defaults = [Constants.NUM_STEPS, Constants.STEP, Constants.INTERVAL_DELAY, Constants.RESOLUTION_SCALE]
        for i, (label, default_value) in enumerate(zip(labels, defaults)):
            CTkLabel(frame, text=label, font=self.custom_font, anchor="w").grid(
                row=r + i, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
            )
            entry = CTkEntry(frame, font=self.custom_font, width=ENTRY_COL_MAX)
            entry.grid(row=r + i, column=1, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, default_value)
            if "Total" in label:
                self.simulation_time_entry = entry
            elif "Time Step" in label:
                self.time_step_entry = entry
            elif "Interval" in label:
                self.interval_entry = entry
            else:
                self.resolution_entry = entry

    def add_angular_rate_section(self, parent):
        frame = CTkFrame(parent)
        frame.grid(row=2, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        parent.grid_columnconfigure(0, weight=0)
        for c in range(3):
            frame.grid_columnconfigure(c, weight=0, minsize=MIDDLE_COL_ENTRY_WIDTH)
        labels_ar = ["Angular Rate ωx (rad/s)", "Angular Rate ωy (rad/s)", "Angular Rate ωz (rad/s)"]
        self.angular_rate_entries = []
        for i, (label, value) in enumerate(zip(labels_ar, Constants.w)):
            CTkLabel(frame, text=label, font=self.custom_font, anchor="w").grid(
                row=i * 2, column=0, columnspan=3, pady=(0, ROW_GAP), sticky="w"
            )
            entry = CTkEntry(frame, font=self.custom_font, width=MIDDLE_COL_ENTRY_WIDTH)
            entry.grid(row=i * 2 + 1, column=i, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, value)
            self.angular_rate_entries.append(entry)

    def create_bottom_bar(self):
        """Root row1: progress left, 5 buttons right (Deploy/Next/Cancel/Apply/Run). Same order."""
        self.bottom_bar_frame = CTkFrame(self)
        self.bottom_bar_frame.grid(
            row=1, column=0, columnspan=3,
            padx=PAD, pady=(BOTTOM_BAR_PAD_V, BOTTOM_BAR_PAD_V),
            sticky="nsew",
        )
        self.bottom_bar_frame.grid_rowconfigure(0, weight=0, minsize=BOTTOM_BAR_ROW_HEIGHT)
        self.bottom_bar_frame.grid_columnconfigure(0, weight=1)
        self.bottom_bar_frame.grid_columnconfigure(1, weight=0, minsize=360)
        self.create_progress_bar(self.bottom_bar_frame)
        self.create_control_buttons(self.bottom_bar_frame)

    def create_progress_bar(self, parent):
        self.progress_frame = CTkFrame(parent)
        self.progress_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        parent.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_rowconfigure(0, weight=0, minsize=BOTTOM_BAR_ROW_HEIGHT)
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_columnconfigure(1, weight=0)
        self.progress_frame.grid_columnconfigure(2, weight=0)
        self.progress_frame.grid_columnconfigure(3, weight=0)
        self.progress_bar = CTkProgressBar(self.progress_frame)
        self.progress_bar.grid(row=0, column=0, padx=(0, PAD), pady=(1, 1), sticky="ew")
        self.progress_label = CTkLabel(self.progress_frame, text="0.0%", font=CTkFont(family="Roboto", size=9))
        self.progress_label.grid(row=0, column=1, padx=(0, PAD), sticky="nsew")
        self.step_label = CTkLabel(self.progress_frame, text="0 / 0", font=CTkFont(family="Roboto", size=9), anchor="e")
        self.step_label.grid(row=0, column=2, padx=(0, PAD), sticky="nsew")
        self.progress_file_label = CTkLabel(self.progress_frame, text="", font=CTkFont(family="Roboto", size=9))
        self.progress_file_label.grid(row=0, column=3, padx=(0, PAD), sticky="nsew")
        self.update_progress(0.0, step=0, num_step=0)

    def create_control_buttons(self, parent):
        """Single row: Deploy / Next / Cancel / Apply / Run (order fixed); right-aligned."""
        button_frame = CTkFrame(parent)
        button_frame.grid(row=0, column=1, padx=(PAD, 0), pady=0, sticky="e")
        for c in range(5):
            button_frame.grid_columnconfigure(c, weight=1)
        pad = ACTION_GAP
        self.deployment_button = CTkButton(
            button_frame, font=self.custom_font_fixedsys, text="Deploy",
            width=ACTION_BUTTON_WIDTH, height=ACTION_BUTTON_HEIGHT,
            command=self.open_deployment_window,
        )
        self.deployment_button.grid(row=0, column=0, padx=pad, pady=(ROW_GAP, 0))
        self.next_button = CTkButton(
            button_frame, font=self.custom_font_fixedsys, text="Next",
            width=ACTION_BUTTON_WIDTH, height=ACTION_BUTTON_HEIGHT,
            fg_color="red", hover_color="darkred",
            state="disabled", command=self.start_gui,
        )
        self.next_button.grid(row=0, column=1, padx=pad, pady=(ROW_GAP, 0))
        self.cancel_button = CTkButton(
            button_frame, font=self.custom_font_fixedsys, text="Cancel",
            width=ACTION_BUTTON_WIDTH, height=ACTION_BUTTON_HEIGHT,
            command=self.close_window,
        )
        self.cancel_button.grid(row=0, column=2, padx=pad, pady=(ROW_GAP, 0))
        self.apply_button = CTkButton(
            button_frame, font=self.custom_font_fixedsys, text="Apply",
            width=ACTION_BUTTON_WIDTH, height=ACTION_BUTTON_HEIGHT,
            command=self.apply_values,
        )
        self.apply_button.grid(row=0, column=3, padx=pad, pady=(ROW_GAP, 0))
        self.run_button = CTkButton(
            button_frame, font=self.custom_font_fixedsys, text="Run",
            width=ACTION_BUTTON_WIDTH, height=ACTION_BUTTON_HEIGHT,
            fg_color="green", hover_color="darkgreen",
            command=self.start_simulation_thread,
        )
        self.run_button.grid(row=0, column=4, padx=pad, pady=(ROW_GAP, 0))

    def add_altitude_section(self, parent):
        """Section D — Altitude + Calculate; en altta (row 6)."""
        frame = CTkFrame(parent)
        frame.grid(row=6, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        parent.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        frame.grid_columnconfigure(1, weight=0, minsize=ENTRY_COL_MAX)
        frame.grid_columnconfigure(2, weight=0)
        frame.grid_columnconfigure(3, weight=0)
        CTkLabel(frame, text="Altitude (km)", font=self.custom_font, anchor="w").grid(
            row=0, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
        )
        self.altitude_entry = CTkEntry(frame, width=ENTRY_MIN_WIDTH, font=self.custom_font, state="disabled")
        self.altitude_entry.grid(row=0, column=1, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="ew")
        self.altitude_check = tk.BooleanVar()
        CTkCheckBox(frame, text="", variable=self.altitude_check, onvalue=True, offvalue=False, command=self.toggle_altitude).grid(
            row=0, column=2, padx=(PAD, 0), pady=(0, ROW_GAP), sticky="e"
        )
        self.calculate_button = CTkButton(
            frame, font=self.custom_font_fixedsys, text="Calculate",
            width=ACTION_BUTTON_WIDTH, height=ACTION_BUTTON_HEIGHT,
            fg_color="green", hover_color="darkgreen",
            command=self.INITGUI_run_simulation,
        )
        self.calculate_button.grid(row=0, column=3, padx=(PAD, 0), pady=(0, ROW_GAP), sticky="e")

    def add_quaternion_section(self, parent):
        """Section B — label | q1 q2 q3 q4 (eski boyut) | checkbox. Preview Euler satırında."""
        frame = CTkFrame(parent)
        frame.grid(row=2, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        parent.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        for c in range(1, 5):
            frame.grid_columnconfigure(c, weight=1, minsize=ENTRY_MIN_WIDTH)
        frame.grid_columnconfigure(5, weight=0)
        frame.grid_rowconfigure(0, weight=0)
        CTkLabel(frame, text="Quaternion (q1 q2 q3 q4)", font=self.custom_font, anchor="w").grid(
            row=0, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
        )
        self.q_entries = []
        default_q = (0, 0, 0, 1)
        for i in range(4):
            entry = CTkEntry(frame, font=self.custom_font, width=ENTRY_MIN_WIDTH, state="disabled")
            entry.grid(row=0, column=i + 1, padx=FORM_ROW_PADX, pady=(0, ROW_GAP), sticky="ew")
            entry.insert(0, str(default_q[i]))
            self.q_entries.append(entry)
        self.quaternion_check = tk.BooleanVar(value=True)
        self.quaternion_checkbox = CTkCheckBox(
            frame, text="", variable=self.quaternion_check,
            onvalue=True, offvalue=False, command=self.toggle_quaternion,
        )
        self.quaternion_checkbox.grid(row=0, column=5, padx=(FORM_ROW_PADX, 0), pady=(0, ROW_GAP), sticky="e")

    def add_euler_angles_section(self, parent):
        """Section B — label | roll pitch yaw (dar) | checkbox | Preview. Preview burada, tam görünsün."""
        frame = CTkFrame(parent)
        frame.grid(row=3, column=0, padx=PAD, pady=SECTION_GAP, sticky="nsew")
        parent.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(0, minsize=LABEL_COL_MINSIZE, weight=0)
        for c in range(1, 4):
            frame.grid_columnconfigure(c, weight=1, minsize=RIGHT_COL_ENTRY_WIDTH)
        frame.grid_columnconfigure(4, weight=0)
        frame.grid_columnconfigure(5, weight=0)
        frame.grid_rowconfigure(0, weight=0)
        CTkLabel(frame, text="Euler Angles (roll pitch yaw)", font=self.custom_font, anchor="w").grid(
            row=0, column=0, padx=(0, FORM_ROW_PADX), pady=(0, ROW_GAP), sticky="w"
        )
        self.euler_entries = []
        for i in range(3):
            entry = CTkEntry(frame, font=self.custom_font, width=RIGHT_COL_ENTRY_WIDTH, state="disabled")
            entry.grid(row=0, column=i + 1, padx=FORM_ROW_PADX, pady=(0, ROW_GAP), sticky="ew")
            self.euler_entries.append(entry)
        self.euler_check = tk.BooleanVar()
        self.euler_checkbox = CTkCheckBox(
            frame, text="", variable=self.euler_check,
            onvalue=True, offvalue=False, command=self.toggle_euler,
        )
        self.euler_checkbox.grid(row=0, column=4, padx=(FORM_ROW_PADX, ACTION_GAP), pady=(0, ROW_GAP), sticky="e")
        self.preview_button = CTkButton(
            frame, text="Preview", font=self.custom_font_fixedsys,
            width=ACTION_BUTTON_WIDTH, height=ACTION_BUTTON_HEIGHT,
            fg_color="red", hover_color="darkred", state="normal",
            command=self.update_preview,
        )
        self.preview_button.grid(row=0, column=5, padx=0, pady=(0, ROW_GAP), sticky="e")

    def toggle_altitude(self):
        state = "normal" if self.altitude_check.get() else "disabled"
        self.altitude_entry.configure(state=state)
        semi_state = "disabled" if self.altitude_check.get() else "normal"
        if semi_state == "disabled":
            self.semi_major_axis_entry.delete(0, tk.END)
        self.semi_major_axis_entry.configure(state=semi_state)
