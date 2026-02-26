"""Layout: place() birebir SatMagSim_Base — canvases, fields, checkboxes, comboboxes, update_gui."""

import tkinter as tk
from tkinter import ttk

from customtkinter import CTkButton, CTkEntry, CTkCheckBox

from config.constants import Constants


class MagneticFieldGUILayoutMixin:
    """Mixin: init_ui, create_fields, create_checkboxes, update_checkbox_quivers, update_gui (place layout)."""

    def create_checkboxes(self, checkbox_data):
        """checkbox_data: list of (text, variable, rel_x, rel_y). Sol tarafta 3D görünümün yanında."""
        for text, variable, rel_x, rel_y in checkbox_data:
            cb = CTkCheckBox(
                self.root,
                text=text,
                variable=variable,
                onvalue=True,
                offvalue=False,
                bg_color="#2B2B2B",
                command=self.update_checkbox_quivers,
            )
            cb.place(relx=rel_x, rely=rel_y, anchor="w")

    def toggle_body_extra_fields(self):
        state = tk.NORMAL if self.body_additional_entries_checkbox.get() else tk.DISABLED
        for entry in self.entries["B.Body ="][4:]:
            entry.configure(state=state)

    def update_checkbox_quivers(self):
        if not getattr(self, "quivers", None):
            return
        if self.pause_flag:
            frame = getattr(self, "current_frame_fig2", 0) - 1
            if frame < 0:
                frame = 0
        else:
            frame = len(self.data.latitude_data) - 1
        self.update_fig2(frame, self.data)
        self.canvas_fig2.draw()

    def init_ui(self):
        # Canvases: SatMagSim_Base konumları
        self.canvas1 = self.create_canvas(relx=0.02, rely=0.02, relwidth=0.46, relheight=0.70)
        self.canvas2 = self.create_canvas(relx=0.52, rely=0.02, relwidth=0.46, relheight=0.70)
        self.canvas3 = self.create_canvas(relx=0.52, rely=0.73, relwidth=0.46, relheight=0.25)

        self.fig1, self.ax1 = self.create_fig1()
        self.fig2, self.ax2 = self.create_fig2()
        self.fig3, self.ax3 = self.create_fig3()

        self.create_fields()
        self.create_checkboxes([
            ("R.ECI", self.r_eci_visible, 0.53, 0.25),
            ("B.ECI", self.eci_visible, 0.53, 0.30),
            ("B.Body", self.body_visible, 0.53, 0.35),
            ("V.ECI", self.v_eci_visible, 0.53, 0.40),
            ("Sat.Body", self.sat_body_visible, 0.53, 0.45),
        ])

        self.canvas_fig1 = self.create_canvas_figure(self.fig1, self.canvas1)
        self.canvas_fig2 = self.create_canvas_figure(self.fig2, self.canvas2)
        self.canvas_fig3 = self.create_canvas_figure(self.fig3, self.canvas3)

        self.canvas1.bind("<Configure>", lambda e: self._on_figure_canvas_configure(e, self.canvas_fig1))
        self.canvas2.bind("<Configure>", lambda e: self._on_figure_canvas_configure(e, self.canvas_fig2))
        self.canvas3.bind("<Configure>", lambda e: self._on_figure_canvas_configure(e, self.canvas_fig3))

        combobox_options = [
            "Btot_ECI", "Btot_ECEF", "Btot_Body",
            "Btot_ECEF Magnitude", "Btot_ECI Magnitude", "Btot_Body Magnitude",
            "Btot_ECEF Normalized", "Btot_ECI Normalized", "Btot_Body Normalized",
        ]
        available_ports = self.get_available_ports()
        if available_ports:
            self.combobox_port = ttk.Combobox(self.root, values=available_ports, state="readonly", width=5)
            self.combobox_port.set(available_ports[0])
        else:
            self.combobox_port = ttk.Combobox(self.root, values=["No Ports Found"], state="readonly", width=5)
            self.combobox_port.set("No Ports Found")
        self.combobox_port.place(relx=0.44, rely=0.765, anchor="w")

        self.combobox_data = ttk.Combobox(self.root, values=combobox_options, state="readonly", width=10)
        self.combobox_data.set("Select Data Field")
        self.combobox_data.place(relx=0.32, rely=0.765, anchor="w")

        self.combo_values_baud = ["921600", "115200", "256000", "230400", "512000"]
        self.combobox_baud = ttk.Combobox(self.root, values=self.combo_values_baud, state="readonly", width=10)
        self.combobox_baud.set("Baud Rate")
        self.combobox_baud.place(relx=0.38, rely=0.765, anchor="w")

    def update_gui(self, index):
        """Update B/altitude entries for step index; same index drives map line/dot, 3D cube, time plot (sync)."""
        if self.stopped_flag or self.pause_flag:
            return

        for i in range(3):
            self.entries["B.ECEF ="][i].delete(0, tk.END)
            self.entries["B.ECEF ="][i].insert(0, f"{float(self.data.Btot_ECEF_data[index, i]):.2f}")
            self.entries["B.ECI ="][i].delete(0, tk.END)
            self.entries["B.ECI ="][i].insert(0, f"{float(self.data.Btot_ECI_data[index, i]):.2f}")
            self.entries["B.Body ="][i].delete(0, tk.END)
            self.entries["B.Body ="][i].insert(0, f"{float(self.data.Btot_body_data[index, i]):.2f}")

        self.entries["B.ECEF ="][3].delete(0, tk.END)
        self.entries["B.ECEF ="][3].insert(0, f"{float(self.data.Btot_ECEF_mag[index, 0]):.2f}")
        self.entries["B.ECI ="][3].delete(0, tk.END)
        self.entries["B.ECI ="][3].insert(0, f"{float(self.data.Btot_ECI_mag[index, 0]):.2f}")
        self.entries["B.Body ="][3].delete(0, tk.END)
        self.entries["B.Body ="][3].insert(0, f"{float(self.data.Btot_body_mag[index, 0]):.2f}")

        self.altitude_data_entry.delete(0, tk.END)
        self.altitude_data_entry.insert(0, f"{float(self.data.altitude_data[index]) / 1000:.2f}")

        n = len(self.data.latitude_data)
        if index < n - 1 and not getattr(self, "_unified_animation", False):
            self.root.after(Constants.INTERVAL_DELAY, self.update_gui, index + 1)

    def create_fields(self):
        """Sol alt: Altitude, X/Y/Z/Mag başlıkları, B.ECEF/ECI/Body, Start/Pause/Stop/Import (SatMagSim_Base place)."""
        parent = self.root
        bg = "#2B2B2B"

        CTkButton(parent, text="Altitude (km):", width=100, fg_color=bg, bg_color=bg, border_color=bg, font=self.roboto_font).place(relx=0.02, rely=0.04, anchor="w")
        self.altitude_data_entry = CTkEntry(parent, width=75, fg_color=bg, bg_color=bg, border_color=bg, font=self.roboto_font)
        self.altitude_data_entry.place(relx=0.08, rely=0.04, anchor="w")

        axes = ["X(μT)", "Y(μT)", "Z(μT)", "Magnitude"]
        for i, axis in enumerate(axes):
            CTkButton(parent, text=axis, width=75, height=10, font=self.roboto_font2).place(relx=0.08 + i * 0.06, rely=0.765, anchor="w")

        fields = ["B.ECEF =", "B.ECI =", "B.Body ="]
        self.entries = {}
        for i, field in enumerate(fields):
            rely_row = 0.8 + i * 0.05
            CTkButton(parent, text=field, width=70, font=self.roboto_font, anchor=tk.CENTER).place(relx=0.02, rely=rely_row, anchor="w")
            self.entries[field] = []
            for j in range(4):
                entry = CTkEntry(parent, width=75, font=self.roboto_font)
                entry.place(relx=0.08 + j * 0.06, rely=rely_row, anchor="w")
                self.entries[field].append(entry)
            if field == "B.Body =":
                for j in range(4, 7):
                    entry = CTkEntry(parent, width=50, font=self.roboto_font)
                    entry.place(relx=0.08 + 4 * 0.06 + (j - 4) * 0.04, rely=rely_row, anchor="w")
                    self.entries[field].append(entry)
                    entry.configure(state=tk.DISABLED)
                CTkCheckBox(parent, text="Extra", variable=self.body_additional_entries_checkbox, command=self.toggle_body_extra_fields).place(relx=0.08 + 4 * 0.06 + 3 * 0.04, rely=rely_row, anchor="w")

        buttons_rely = 0.8 + len(fields) * 0.05
        CTkButton(parent, fg_color="green", hover_color="darkgreen", font=self.custom_font_fixedsys, text="Start", width=100, command=self.start_animations).place(relx=0.08, rely=buttons_rely, anchor="w")
        CTkButton(parent, font=self.custom_font_fixedsys, text="Pause", width=100, command=lambda: self.pause_esp32_communication() if self.import_button_pressed else self.pause_animations()).place(relx=0.16, rely=buttons_rely, anchor="w")
        CTkButton(parent, fg_color="red", hover_color="darkred", font=self.custom_font_fixedsys, text="Stop", width=100, command=lambda: self.stop_esp32_communication() if self.import_button_pressed else self.stop_animations()).place(relx=0.24, rely=buttons_rely, anchor="w")
        CTkButton(parent, text="Import", width=100, fg_color="black", font=self.custom_font_fixedsys, command=self.start_esp32_communication).place(relx=0.32, rely=buttons_rely, anchor="w")
