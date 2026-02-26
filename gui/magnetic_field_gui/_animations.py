"""Animations: start/pause/stop, init_fig1/2/3, update_fig1/2/3, draw_figures for MagneticFieldGUI."""

import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from config.constants import Constants
from config.theme import roboto_prop


class MagneticFieldGUIAnimationsMixin:
    """Mixin: start_animations, pause_animations, stop_animations, init/update_fig1/2/3, draw_figures."""

    def stop_animations(self):
        try:
            self.pause_flag = False
            self.stopped_flag = True
            self.was_stopped = True
            self._unified_animation = False
            if getattr(self, "_anim_after_id", None) is not None:
                self.root.after_cancel(self._anim_after_id)
                self._anim_after_id = None

            if hasattr(self, "orbit_segment_lines"):
                for seg_line in self.orbit_segment_lines:
                    try:
                        seg_line.remove()
                    except (ValueError, AttributeError):
                        pass
                self.orbit_segment_lines.clear()
            if hasattr(self, "point") and self.point in self.ax1.collections:
                self.point.remove()
            if hasattr(self, "satellite_label"):
                self.satellite_label.set_text("")
            if hasattr(self, "point"):
                self.point.set_data([], [])
            if hasattr(self, "satellite_label"):
                self.satellite_label.set_position((0, 0))
            if hasattr(self, "orbit_segment_lines"):
                self.orbit_segment_lines.clear()

            if hasattr(self, "quivers"):
                for quiver in self.quivers:
                    if quiver in self.ax2.collections:
                        quiver.remove()
            self.quivers = [
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color="y"),
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color="b"),
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color="r"),
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color="w"),
            ]
            if hasattr(self, "normal_quivers"):
                for quiver in self.normal_quivers:
                    if quiver in self.ax2.collections:
                        quiver.remove()
            normal_colors = ["g", "r", "m"]
            self.normal_quivers = [
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color=c) for c in normal_colors
            ]

            if hasattr(self, "cube_collection") and self.cube_collection is not None:
                self.cube_collection.remove()
            rotated_vertices = self.rotate_cube(self.cube_origin, self.data.q_DCM[0])
            self.cube_collection = self.create_cube(self.ax2, rotated_vertices)

            if hasattr(self, "line_wx") and self.line_wx in self.ax3.lines:
                self.line_wx.set_data([], [])
            if hasattr(self, "line_wy") and self.line_wy in self.ax3.lines:
                self.line_wy.set_data([], [])
            if hasattr(self, "line_wz") and self.line_wz in self.ax3.lines:
                self.line_wz.set_data([], [])

            for key in self.entries:
                for entry in self.entries[key]:
                    entry.delete(0, tk.END)
                    entry.insert(0, "")

            self.eci_visible.set(False)
            self.body_visible.set(False)
            self.r_eci_visible.set(False)
            self.v_eci_visible.set(False)
            self.sat_body_visible.set(False)
            self.body_additional_entries_checkbox.set(False)

            self.draw_figures()
        except Exception as e:
            print(f"Error stopping animations: {e}")

    def pause_animations(self):
        try:
            self.pause_flag = True
            self.was_stopped = False
            self.stopped_flag = False
            self.current_frame_fig1 = getattr(self, "_anim_frame", 0)
            self.current_frame_fig2 = self.current_frame_fig1
            self.current_frame_fig3 = self.current_frame_fig1
            if getattr(self, "_anim_after_id", None) is not None:
                self.root.after_cancel(self._anim_after_id)
                self._anim_after_id = None
        except Exception as e:
            print(f"Error pausing: {e}")

    def _clear_fig1_artists(self):
        if hasattr(self, "orbit_segment_lines"):
            for seg_line in self.orbit_segment_lines:
                try:
                    seg_line.remove()
                except (ValueError, AttributeError):
                    pass
            self.orbit_segment_lines.clear()
        if hasattr(self, "point"):
            try:
                self.point.remove()
            except (ValueError, AttributeError):
                pass
        if hasattr(self, "satellite_label"):
            self.satellite_label.set_text("")

    def _clear_fig2_quivers(self):
        if hasattr(self, "quivers"):
            for quiver in self.quivers:
                try:
                    quiver.remove()
                except (ValueError, AttributeError):
                    pass
        if hasattr(self, "normal_quivers"):
            for quiver in self.normal_quivers:
                try:
                    quiver.remove()
                except (ValueError, AttributeError):
                    pass

    def _animation_tick(self):
        """Single timer: update all 3 figures + GUI in sync, then draw_idle for smooth animation."""
        if self.stopped_flag or self.pause_flag:
            return
        n = len(self.data.latitude_data)
        frame = getattr(self, "_anim_frame", 0)
        if frame >= n:
            return
        self._unified_animation = True
        self.update_fig1(frame, self.data.longitude_data, self.data.latitude_data, self.point, self.satellite_label)
        self.update_fig2(frame, self.data)
        self.update_fig3(frame)
        if frame % 3 == 0:
            self.update_gui(frame)
        self.canvas_fig1.draw_idle()
        self.canvas_fig2.draw_idle()
        self.canvas_fig3.draw_idle()
        self._anim_frame = frame + 1
        if self._anim_frame < n and not self.stopped_flag and not self.pause_flag:
            self._anim_after_id = self.root.after(Constants.INTERVAL_DELAY, self._animation_tick)

    def start_animations(self):
        """Start all 3 figures with Run simulation data (single timer for smooth animation)."""
        try:
            n = len(self.data.latitude_data)
            if n == 0:
                return
            if self.pause_flag:
                self._anim_frame = getattr(self, "current_frame_fig1", 0)
                self._clear_fig1_artists()
                self._clear_fig2_quivers()
            elif self.was_stopped:
                self._anim_frame = 0
                self._clear_fig1_artists()
                self._clear_fig2_quivers()
            else:
                self._anim_frame = 0

            self.pause_flag = False
            self.stopped_flag = False
            self.ani_fig1 = self.ani_fig2 = self.ani_fig3 = None
            self._unified_animation = True

            self.init_fig1()
            self.init_fig2()
            self.init_fig3()

            self.draw_figures()
            self.update_gui(self._anim_frame)
            self._animation_tick()
        except Exception as e:
            print(f"Error starting animations: {e}")

    def init_fig1(self):
        self.orbit_segment_lines = []
        self.point, = self.ax1.plot([], [], marker="o", color="white", transform=ccrs.PlateCarree())
        self.satellite_label = self.ax1.text(
            0, 0, "", color="white", fontsize=8, ha="right", fontproperties=roboto_prop
        )
        return self.point, self.satellite_label

    @staticmethod
    def _to_plot_lon(lon):
        """Longitude to -180..180 for PlateCarree."""
        lon = np.asarray(lon, dtype=float)
        out = np.where(lon > 180, lon - 360, lon)
        return np.where(out < -180, out + 360, out)

    @staticmethod
    def _orbit_segments(lon, lat):
        """Split at date-line wrap (works for -180..180 and 0-360). Wrap = crossing 180°."""
        def to_plot(l):
            l = np.asarray(l, dtype=float)
            o = np.where(l > 180, l - 360, l)
            return np.where(o < -180, o + 360, o)
        lon = np.asarray(lon, dtype=float)
        lat = np.asarray(lat, dtype=float)
        if len(lon) == 0:
            return []
        if len(lon) == 1:
            return [(to_plot(lon), lat)]
        lon360 = lon % 360.0
        cross_high_low = (lon360[:-1] >= 180) & (lon360[1:] < 180)
        cross_low_high = (lon360[:-1] < 180) & (lon360[1:] >= 180)
        gaps = cross_high_low | cross_low_high
        if not np.any(gaps):
            return [(to_plot(lon), lat)]
        break_indices = np.where(gaps)[0] + 1
        starts = np.concatenate([[0], break_indices])
        ends = np.concatenate([break_indices, [len(lon)]])
        return [(to_plot(lon[s:e]), lat[s:e]) for s, e in zip(starts, ends) if e > s]

    def update_fig1(self, frame, longitude_data, latitude_data, point, satellite_label):
        for seg_line in self.orbit_segment_lines:
            try:
                seg_line.remove()
            except (ValueError, AttributeError):
                pass
        self.orbit_segment_lines.clear()
        lon_trail = longitude_data[:frame]
        lat_trail = latitude_data[:frame]
        if len(lon_trail) > 0:
            for seg_lon, seg_lat in self._orbit_segments(lon_trail, lat_trail):
                line, = self.ax1.plot(
                    seg_lon, seg_lat,
                    color="white", linewidth=1.5,
                    transform=ccrs.PlateCarree(),
                )
                self.orbit_segment_lines.append(line)
        lon_cur = float(self._to_plot_lon(np.array([longitude_data[frame]]))[0])
        lat_cur = latitude_data[frame]
        self.point.set_data([lon_cur], [lat_cur])
        self.satellite_label.set_position((lon_cur, lat_cur))
        self.satellite_label.set_text("Taurus  ")
        return self.point, self.satellite_label

    def init_fig2(self):
        if hasattr(self, "cube_collection") and self.cube_collection is not None:
            self.cube_collection.remove()

        self.quivers = [
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color="y", label="B_ECI"),
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color="b", label="B_Body"),
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color="#FFA500", label="R_ECI"),
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color="w", label="V_ECI"),
        ]
        rotated_vertices = self.rotate_cube(self.cube_origin, self.data.q_DCM[0])
        self.cube_collection = self.create_cube(self.ax2, rotated_vertices)

        normals = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        normal_colors = ["g", "r", "m"]
        self.normal_quivers = [
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color=c) for c in normal_colors
        ]

        self.legend_labels = ["B_ECI", "B_Body", "R_ECI", "V_ECI"]
        self.legend_colors = ["y", "b", "#FFA500", "w"]
        self.legend_handles = [
            plt.Line2D([0], [0], color=c, lw=4) for c in self.legend_colors
        ]
        self.legend = self.ax2.legend(
            handles=self.legend_handles,
            labels=self.legend_labels,
            loc="upper right",
            fontsize=10,
            prop=roboto_prop,
            bbox_to_anchor=(1.1, 1.05),
        )
        plt.setp(self.legend.get_texts(), color="#03A062")
        self.legend.get_frame().set_facecolor("#f0f0f0")
        self.legend.get_frame().set_edgecolor("#000000")

        satbody_labels = ["SatBodyX", "SatBodyY", "SatBodyZ"]
        satbody_colors = ["g", "r", "m"]
        satbody_handles = [plt.Line2D([0], [0], color=c, lw=4) for c in satbody_colors]
        self.satbody_legend = self.ax2.legend(
            handles=satbody_handles,
            labels=satbody_labels,
            loc="upper left",
            fontsize=10,
            prop=roboto_prop,
            bbox_to_anchor=(-0.1, 1.05),
        )
        plt.setp(self.satbody_legend.get_texts(), color="#03A062")
        self.satbody_legend.get_frame().set_facecolor("#f0f0f0")
        self.satbody_legend.get_frame().set_edgecolor("#000000")
        self.ax2.add_artist(self.legend)
        self.ax2.add_artist(self.satbody_legend)
        return self.quivers

    def update_fig2(self, frame, data):
        for quiver in self.quivers:
            quiver.remove()
        for quiver in self.normal_quivers:
            quiver.remove()

        if self.eci_visible.get():
            self.quivers[0] = self.ax2.quiver(
                0, 0, 0,
                data.Btot_ECI_norm[frame, 0],
                data.Btot_ECI_norm[frame, 1],
                data.Btot_ECI_norm[frame, 2],
                color="y",
                label="B_ECI",
            )
        else:
            self.quivers[0] = self.ax2.quiver([], [], [], [], [], [])

        if self.body_visible.get():
            self.quivers[1] = self.ax2.quiver(
                0, 0, 0,
                data.Btot_body_norm[frame, 0],
                data.Btot_body_norm[frame, 1],
                data.Btot_body_norm[frame, 2],
                color="b",
                label="B_Body",
            )
        else:
            self.quivers[1] = self.ax2.quiver([], [], [], [], [], [])

        if self.r_eci_visible.get():
            self.quivers[2] = self.ax2.quiver(
                0, 0, 0,
                data.R_ECI_norm[frame, 0],
                data.R_ECI_norm[frame, 1],
                data.R_ECI_norm[frame, 2],
                color="#FFA500",
                label="R_ECI",
            )
        else:
            self.quivers[2] = self.ax2.quiver([], [], [], [], [], [])

        if self.v_eci_visible.get():
            self.quivers[3] = self.ax2.quiver(
                0, 0, 0,
                data.V_ECI_norm[frame, 0],
                data.V_ECI_norm[frame, 1],
                data.V_ECI_norm[frame, 2],
                color="w",
                label="V_ECI",
            )
        else:
            self.quivers[3] = self.ax2.quiver([], [], [], [], [], [])

        if hasattr(self, "cube_collection") and self.cube_collection is not None:
            self.cube_collection.remove()
        rotated_vertices = self.rotate_cube(self.cube_origin, data.q_DCM[frame])
        self.cube_collection = self.create_cube(self.ax2, rotated_vertices)

        if self.sat_body_visible.get():
            normals = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            normal_colors = ["g", "r", "m"]
            self.normal_quivers = [
                self.update_quiver(
                    self.rotate_cube(norm, data.q_DCM[frame]), color
                )
                for norm, color in zip(normals, normal_colors)
            ]
        else:
            self.normal_quivers = [
                self.ax2.quiver([], [], [], [], [], []) for _ in range(3)
            ]

        return self.quivers

    def init_fig3(self):
        alen = len(self.data.angular_vel)
        if alen == 0:
            self.ax3.set_xlim(0, 1)
            self.ax3.set_ylim(0, 1)
        else:
            self.ax3.set_xlim(0, alen)
            self.ax3.set_ylim(np.min(self.data.angular_vel), np.max(self.data.angular_vel))
        if not hasattr(self, "legend_created"):
            self.line_wx, = self.ax3.plot([], [], color="r", label=r"$\omega_x$")
            self.line_wy, = self.ax3.plot([], [], color="g", label=r"$\omega_y$")
            self.line_wz, = self.ax3.plot([], [], color="b", label=r"$\omega_z$")
            self.ax3.legend(loc="upper right", fontsize=10, prop=roboto_prop)
            self.legend_created = True
        return self.line_wx, self.line_wy, self.line_wz

    def update_fig3(self, frame):
        x_data = np.arange(frame)
        self.line_wx.set_data(x_data, self.data.angular_vel[:frame, 0])
        self.line_wy.set_data(x_data, self.data.angular_vel[:frame, 1])
        self.line_wz.set_data(x_data, self.data.angular_vel[:frame, 2])
        return self.line_wx, self.line_wy, self.line_wz

    def draw_figures(self):
        if not hasattr(self, "point"):
            self.init_fig1()
            self.init_fig2()
            self.init_fig3()
        self.canvas_fig1.draw()
        self.canvas_fig2.draw()
        self.canvas_fig3.draw()
