"""Matplotlib figures (Btot map, 3D axes, 2D plot) and canvas/cube helpers for MagneticFieldGUI."""

import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from config.constants import Constants
from config.theme import roboto_prop
from gui.common import FIGURE_FACECOLOR, AXIS_GRID_COLOR, TEXT_COLOR


class MagneticFieldGUIFiguresMixin:
    """Mixin: create_fig1/2/3, setup_2d/3d_axes, create_canvas_figure, create_cube, rotate_cube, update_quiver."""

    def create_canvas(self, **kwargs):
        """Create tk.Canvas on root and place it (SatMagSim_Base birebir)."""
        canvas = tk.Canvas(self.root, bg="#2B2B2B")
        canvas.place(**kwargs)
        return canvas

    def create_fig1(self):
        fig1 = Figure(figsize=(19.2, 10.8), facecolor="#2B2B2B")
        ax1 = fig1.add_subplot(111, projection=ccrs.PlateCarree())
        ax1.add_feature(cfeature.COASTLINE)
        ax1.add_feature(cfeature.BORDERS, linestyle=":")
        ax1.set_global()
        ax1.set_facecolor("#2B2B2B")

        lon, lat = np.meshgrid(
            np.linspace(-180, 179, self.Btot_magnitude.shape[2]),
            np.linspace(-89, 90, self.Btot_magnitude.shape[1]),
        )
        heatmap = ax1.contourf(
            lon, lat, self.Btot_magnitude[0], 60, transform=ccrs.PlateCarree(), cmap="jet"
        )
        for coll in heatmap.collections:
            coll.set_alpha(0.45)
        cbar = fig1.colorbar(heatmap, ax=ax1, orientation="horizontal", pad=0.15, shrink=0.8)
        vmin, vmax = heatmap.get_clim()
        ticks = np.linspace(vmin, vmax, num=6)
        tick_labels = [f"{t / 1e4:.1f}" for t in ticks]
        cbar.set_ticks(ticks)
        cbar.set_ticklabels(tick_labels)
        cbar.ax.text(
            1.05, -0.7, r"$\times 10^{4}$",
            transform=cbar.ax.transAxes, fontsize=10, va="bottom", ha="left",
            color="#FFFFFF", fontproperties=roboto_prop,
        )
        cbar.set_label("(nanoTesla)", fontweight="bold", color="#FFFFFF", fontproperties=roboto_prop)
        plt.setp(cbar.ax.get_xticklabels(), color="#FFFFFF", fontsize=10, fontweight="bold", fontproperties=roboto_prop)

        ax1.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
        ax1.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
        ax1.set_xlabel("Longitude (degrees)", color=TEXT_COLOR, fontproperties=roboto_prop)
        ax1.set_ylabel("Latitude (degrees)", color=TEXT_COLOR, fontproperties=roboto_prop)
        ax1.tick_params(axis="x", colors=TEXT_COLOR)
        ax1.tick_params(axis="y", colors=TEXT_COLOR)
        ax1.set_title(
            fr"$B_{{tot}} \, \mathrm{{Magnitude}}$ (ECEF) @{int(Constants.ALTITUDE)} km",
            fontsize=10, color="#FFFFFF", pad=5, fontproperties=roboto_prop, fontweight="bold",
        )
        return fig1, ax1

    def create_fig2(self):
        fig2 = Figure(figsize=(19.2, 10.8), facecolor="#2B2B2B")
        ax2 = fig2.add_subplot(111, projection="3d")
        self.setup_3d_axes(ax2)
        ax2.set_title("Normalized Vectors", fontsize=12, color="#FFFFFF", fontproperties=roboto_prop)
        return fig2, ax2

    def setup_3d_axes(self, ax):
        ax.set_facecolor("#2B2B2B")
        ax.xaxis.pane.set_facecolor("#2B2B2B")
        ax.yaxis.pane.set_facecolor("#2B2B2B")
        ax.zaxis.pane.set_facecolor("#2B2B2B")
        ax.xaxis.pane.set_edgecolor("white")
        ax.yaxis.pane.set_edgecolor("white")
        ax.zaxis.pane.set_edgecolor("white")
        ax.grid(True, color="#03A062")
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.tick_params(colors="white", labelsize=10, width=2)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.zaxis.label.set_color("white")
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        ax.set_zticks([-1, 0, 1])
        ax.set_xlabel("X", labelpad=10, fontsize=10, fontweight="bold", fontproperties=roboto_prop)
        ax.set_ylabel("Y", labelpad=10, fontsize=10, fontweight="bold", fontproperties=roboto_prop)
        ax.set_zlabel("Z", labelpad=10, fontsize=10, fontweight="bold", fontproperties=roboto_prop)

    def create_fig3(self):
        fig3 = Figure(figsize=(8, 4), facecolor="#2B2B2B")
        ax3 = fig3.add_subplot(111)
        self.setup_2d_axes(ax3)
        fig3.subplots_adjust(left=0.07, right=0.97, top=0.97, bottom=0.17)
        return fig3, ax3

    def setup_2d_axes(self, ax):
        ax.set_facecolor("#2B2B2B")
        ax.grid(True, color="white")
        ax.tick_params(colors="white", labelsize=6, width=0.8)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.set_xlabel("Time [s]", labelpad=1, fontsize=6, fontproperties=roboto_prop, color="white")
        ax.set_ylabel("Value", labelpad=1, fontsize=6, fontproperties=roboto_prop, color="white")
        ax.spines["top"].set_color("white")
        ax.spines["bottom"].set_color("white")
        ax.spines["left"].set_color("white")
        ax.spines["right"].set_color("white")

    def _on_figure_canvas_configure(self, event, canvas_fig):
        """Resize matplotlib figure to match container."""
        if canvas_fig is None:
            return
        w = max(1, event.width)
        h = max(1, event.height)
        fig = canvas_fig.figure
        dpi = fig.get_dpi()
        fig.set_size_inches(w / dpi, h / dpi)
        canvas_fig.draw_idle()

    def create_canvas_figure(self, fig, canvas):
        canvas_fig = FigureCanvasTkAgg(fig, master=canvas)
        canvas_fig.get_tk_widget().place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        return canvas_fig

    def rotate_cube(self, vertices, dcm):
        return dcm @ vertices.T

    def create_cube(self, ax, vertices):
        vertices = vertices.T
        faces = [
            [vertices[j] for j in [0, 1, 2, 3]],
            [vertices[j] for j in [4, 5, 6, 7]],
            [vertices[j] for j in [0, 3, 7, 4]],
            [vertices[j] for j in [1, 2, 6, 5]],
            [vertices[j] for j in [0, 1, 5, 4]],
            [vertices[j] for j in [2, 3, 7, 6]],
        ]
        face_colors = ["cyan", "magenta", "yellow", "green", "blue", "red"]
        collection = Poly3DCollection(faces, facecolors=face_colors, linewidths=1, edgecolors="r")
        ax.add_collection3d(collection)
        return collection

    def update_quiver(self, norm_data, color):
        return self.ax2.quiver(0, 0, 0, norm_data[0], norm_data[1], norm_data[2], color=color)
