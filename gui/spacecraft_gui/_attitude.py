"""Quaternion / Euler / cube preview and toggles for SpacecraftGUI."""

import math

import numpy as np
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config.constants import Constants
from config.theme import roboto_prop


class SpacecraftGUIAttitudeMixin:
    """Mixin: quaternion↔euler conversion, preview, bindings, toggles. Uses create_fig2, setup_3d_axes, rotate_cube, create_cube from FiguresMixin."""

    def q_to_DCM(self, q):
        """Build 3x3 DCM from quaternion q (q1,q2,q3,q4)."""
        q1, q2, q3, q4 = q
        q_DCM = np.array([
            [q4**2 + q1**2 - q2**2 - q3**2, 2*(q1*q2 + q3*q4), 2*(q1*q3 - q2*q4)],
            [2*(q1*q2 - q3*q4), q4**2 - q1**2 + q2**2 - q3**2, 2*(q2*q3 + q1*q4)],
            [2*(q1*q3 + q2*q4), 2*(q2*q3 - q1*q4), q4**2 - q1**2 - q2**2 + q3**2],
        ])
        return q_DCM

    def euler_from_quaternion(self, q):
        """Return (roll, pitch, yaw) in radians from quaternion [x,y,z,w]."""
        x, y, z, w = q
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = np.arctan2(t0, t1)
        t2 = +2.0 * (w * y - z * x)
        t2 = np.clip(t2, -1.0, 1.0)
        pitch_y = np.arcsin(t2)
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = np.arctan2(t3, t4)
        return roll_x, pitch_y, yaw_z

    def get_quaternion_from_euler(self, roll, pitch, yaw):
        """Roll/pitch/yaw in degrees → (qx, qy, qz, qw)."""
        roll = roll * math.pi / 180
        pitch = pitch * math.pi / 180
        yaw = yaw * math.pi / 180
        qx = np.sin(roll/2)*np.cos(pitch/2)*np.cos(yaw/2) - np.cos(roll/2)*np.sin(pitch/2)*np.sin(yaw/2)
        qy = np.cos(roll/2)*np.sin(pitch/2)*np.cos(yaw/2) + np.sin(roll/2)*np.cos(pitch/2)*np.sin(yaw/2)
        qz = np.cos(roll/2)*np.cos(pitch/2)*np.sin(yaw/2) - np.sin(roll/2)*np.sin(pitch/2)*np.cos(yaw/2)
        qw = np.cos(roll/2)*np.cos(pitch/2)*np.cos(yaw/2) + np.sin(roll/2)*np.sin(pitch/2)*np.sin(yaw/2)
        return qx, qy, qz, qw

    def cartesian_to_spherical(self, x, y, z):
        """Return (azimuth_deg, elevation_deg) from unit vector (x,y,z)."""
        r = np.sqrt(x**2 + y**2 + z**2)
        elevation = math.degrees(np.arccos(z / r))
        azimuth = math.degrees(np.arctan2(y, x))
        return azimuth, elevation

    def update_preview(self):
        """Redraw 3D cube from quaternion entries and update impulsive spherical params."""
        try:
            qx = float(self.q_entries[0].get())
            qy = float(self.q_entries[1].get())
            qz = float(self.q_entries[2].get())
            qw = float(self.q_entries[3].get())
            roll = float(self.euler_entries[0].get())
            pitch = float(self.euler_entries[1].get())
            yaw = float(self.euler_entries[2].get())

            q = [qx, qy, qz, qw]
            dcm = self.q_to_DCM(q)
            vertices_rotated = self.rotate_cube(Constants.CUBE_ORIGIN, dcm)

            fig2, ax2 = self.create_fig2()
            self.create_cube(ax2, vertices_rotated)
            euler_text = f"(Roll: {roll:.2f}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f})"
            ax2.text2D(
                0.5, 0.95, euler_text,
                transform=ax2.transAxes, fontsize=8, color="white",
                fontweight="bold", ha="center",
            )

            cyan_normal = np.dot(dcm, np.array([0, 0, -1]))
            azimuth, elevation = self.cartesian_to_spherical(
                cyan_normal[0], cyan_normal[1], cyan_normal[2],
            )
            Constants.impulsive_spherical_params["azimuth"] = azimuth
            Constants.impulsive_spherical_params["elevation"] = elevation

            vx = np.sin(np.radians(elevation)) * np.cos(np.radians(azimuth))
            vy = np.sin(np.radians(elevation)) * np.sin(np.radians(azimuth))
            vz = np.cos(np.radians(elevation))
            cyan_normal = cyan_normal / np.linalg.norm(cyan_normal)
            new_vector = np.array([vx, vy, vz]) / np.linalg.norm(np.array([vx, vy, vz]))
            ax2.quiver(0, 0, 0, cyan_normal[0], cyan_normal[1], cyan_normal[2],
                       color="white", linewidth=2, arrow_length_ratio=0.1, label="Cyan Normal")
            ax2.quiver(0, 0, 0, new_vector[0], new_vector[1], new_vector[2],
                       color="red", linewidth=2, arrow_length_ratio=0.01, label="Azimuth/Elevation Vector")

            for widget in self.cube_frame.winfo_children():
                widget.destroy()
            self.canvas_fig2 = FigureCanvasTkAgg(fig2, master=self.cube_frame)
            fig_widget = self.canvas_fig2.get_tk_widget()
            fig_widget.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.canvas_fig2.draw()
            self._preview_fig_agg = self.canvas_fig2
            self.cube_frame.update_idletasks()
        except Exception as e:
            self.progress_file_label.configure(text=f"Preview error: {str(e)}")

    def update_quaternion_from_euler(self):
        """Compute quaternion from Euler entries and fill q_entries."""
        try:
            roll = self.euler_entries[0].get()
            pitch = self.euler_entries[1].get()
            yaw = self.euler_entries[2].get()
            if roll == "" or pitch == "" or yaw == "":
                self.progress_file_label.configure(text="")
                self.preview_button.configure(state="disabled", fg_color="red", hover_color="darkred")
                return
            roll, pitch, yaw = float(roll), float(pitch), float(yaw)
            if not (-180 <= roll <= 180):
                raise ValueError("Euler Angles must be between -180 and +180 degrees")
            if not (-180 <= pitch <= 180):
                raise ValueError("Euler Angles must be between -180 and +180 degrees")
            if not (-180 <= yaw <= 180):
                raise ValueError("Euler Angles must be between -180 and +180 degrees")
            self.progress_file_label.configure(text="")
            qx, qy, qz, qw = self.get_quaternion_from_euler(roll, pitch, yaw)
            for entry, value in zip(self.q_entries, [qx, qy, qz, qw]):
                entry.configure(state="normal", fg_color="grey", text_color="white")
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.6f}")
                entry.configure(state="disabled")
            self.preview_button.configure(state="normal", fg_color="green", hover_color="darkgreen")
        except ValueError as e:
            self.progress_file_label.configure(text=f"Error: {str(e)}")
            self.preview_button.configure(state="disabled", fg_color="red", hover_color="darkred")

    def bind_euler_entries(self):
        for entry in self.euler_entries:
            entry.bind("<KeyRelease>", lambda e: self.update_quaternion_from_euler())

    def update_euler_from_quaternion(self):
        """Compute Euler from quaternion entries and fill euler_entries."""
        try:
            qx = self.q_entries[0].get()
            qy = self.q_entries[1].get()
            qz = self.q_entries[2].get()
            qw = self.q_entries[3].get()
            if qx == "" or qy == "" or qz == "" or qw == "":
                return
            qx, qy, qz, qw = float(qx), float(qy), float(qz), float(qw)
            quaternion_norm = np.sqrt(qx**2 + qy**2 + qz**2 + qw**2)
            if not np.isclose(quaternion_norm, 1):
                raise ValueError("Quaternion norm must be 1")
            self.progress_file_label.configure(text="")
            q = [qx, qy, qz, qw]
            roll, pitch, yaw = self.euler_from_quaternion(q)
            for entry, value in zip(self.euler_entries, [roll, pitch, yaw]):
                entry.configure(state="normal", fg_color="grey", text_color="white")
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.2f}")
                entry.configure(state="disabled")
            self.progress_file_label.configure(text="")
            self.preview_button.configure(state="normal", fg_color="green", hover_color="darkgreen")
        except ValueError as e:
            self.progress_file_label.configure(text=f"Error: {str(e)}")
            self.preview_button.configure(state="disabled", fg_color="red", hover_color="darkred")

    def bind_quaternion_entries(self):
        for entry in self.q_entries:
            entry.bind("<KeyRelease>", lambda e: self.update_euler_from_quaternion())

    def toggle_quaternion(self):
        if self.quaternion_check.get():
            self.euler_check.set(False)
            self.euler_checkbox.configure(state="disabled")
            for entry in self.euler_entries:
                entry.delete(0, tk.END)
                entry.configure(state="disabled")
            for entry in self.q_entries:
                entry.configure(state="normal")
        else:
            for entry in self.q_entries:
                entry.delete(0, tk.END)
                entry.configure(state="disabled")
            self.euler_checkbox.configure(state="normal")

    def toggle_euler(self):
        if self.euler_check.get():
            self.quaternion_check.set(False)
            self.quaternion_checkbox.configure(state="disabled")
            for entry in self.q_entries:
                entry.delete(0, tk.END)
                entry.configure(state="disabled")
            for entry in self.euler_entries:
                entry.configure(state="normal")
        else:
            for entry in self.euler_entries:
                entry.delete(0, tk.END)
                entry.configure(state="disabled")
            self.quaternion_checkbox.configure(state="normal")
