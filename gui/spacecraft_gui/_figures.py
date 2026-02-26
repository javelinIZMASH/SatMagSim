"""Matplotlib figures and canvas helpers for SpacecraftGUI (Btot map, 3D cube)."""

import tkinter as tk

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from config.constants import Constants
from config.theme import roboto_prop
from gui.common import FIGURE_FACECOLOR, AXIS_GRID_COLOR, TEXT_COLOR
from gui.ui_system import PAD, ROW_GAP


class SpacecraftGUIFiguresMixin:
    """Mixin: create_fig1, create_fig2, setup_3d_axes, create_canvas, create_canvas_figure, rotate_cube, create_cube."""

    def create_fig2(self):
        """Return (fig2, ax2) for 3D normalized vectors."""
        fig2 = Figure(figsize=(6.5, 3.5), facecolor=FIGURE_FACECOLOR)
        ax2 = fig2.add_subplot(111, projection="3d")
        self.setup_3d_axes(ax2)
        ax2.set_title(
            "Normalized Vectors",
            fontsize=10,
            color="#FFFFFF",
            fontproperties=roboto_prop,
        )
        return fig2, ax2

    def setup_initial_preview_figure(self, parent):
        """Row0'ı doldur: boş 3D axes (siyah arka plan + sınırlar). Preview basınca update_preview günceller. Debounced resize."""
        fig2, ax2 = self.create_fig2()
        ax2.set_title("Preview (3D) / Normalized Vectors", fontsize=10, color="#FFFFFF", fontproperties=roboto_prop)
        self._preview_fig_agg = FigureCanvasTkAgg(fig2, master=parent)
        self._preview_fig_agg.get_tk_widget().place(relx=0, rely=0, relwidth=1, relheight=1)
        self._preview_fig_agg.draw_idle()
        self._preview_resize_after_id = None
        self._preview_last_wh = (0, 0)
        self._preview_resize_delay_ms = 150
        parent.bind("<Configure>", self._on_preview_canvas_configure)

    def _on_preview_canvas_configure(self, event):
        """Debounced: handler sadece boyut kaydeder; 2px eşik, 150ms sonra tek resize+draw_idle."""
        agg = getattr(self, "_preview_fig_agg", None)
        if agg is None:
            return
        w = max(1, event.width)
        h = max(1, event.height)
        last = getattr(self, "_preview_last_wh", (0, 0))
        if (w, h) == last:
            return
        if abs(w - last[0]) < 2 and abs(h - last[1]) < 2:
            return
        aid = getattr(self, "_preview_resize_after_id", None)
        if aid:
            self.after_cancel(aid)
        self._pending_preview_wh = (w, h)
        self._preview_resize_after_id = self.after(
            getattr(self, "_preview_resize_delay_ms", 150),
            self._do_preview_canvas_resize,
        )

    def _do_preview_canvas_resize(self):
        """Sadece debounced callback'te: _preview_fig_agg resize + draw_idle."""
        self._preview_resize_after_id = None
        agg = getattr(self, "_preview_fig_agg", None)
        if agg is None:
            return
        wh = getattr(self, "_pending_preview_wh", (0, 0))
        w, h = max(1, wh[0]), max(1, wh[1])
        last = getattr(self, "_preview_last_wh", (0, 0))
        if abs(w - last[0]) < 2 and abs(h - last[1]) < 2:
            return
        self._preview_last_wh = (w, h)
        try:
            fig = agg.figure
            dpi = fig.get_dpi()
            fig.set_size_inches(w / dpi, h / dpi)
            agg.draw_idle()
        except Exception:
            pass

    def setup_3d_axes(self, ax):
        """Style 3D axes (dark background, white labels)."""
        ax.set_facecolor(FIGURE_FACECOLOR)
        for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
            pane.set_facecolor(FIGURE_FACECOLOR)
            pane.set_edgecolor("white")
            pane.fill = False
        ax.grid(True, color=AXIS_GRID_COLOR)
        ax.tick_params(colors="white", labelsize=10, width=2)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.zaxis.label.set_color("white")
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])
        ax.set_xticks(np.arange(-1, 1))
        ax.set_yticks(np.arange(-1, 1))
        ax.set_zticks(np.arange(-1, 1))
        ax.set_xlabel("X", labelpad=6, fontsize=8, fontweight="bold", fontproperties=roboto_prop)
        ax.set_ylabel("Y", labelpad=6, fontsize=8, fontweight="bold", fontproperties=roboto_prop)
        ax.set_zlabel("Z", labelpad=6, fontsize=8, fontweight="bold", fontproperties=roboto_prop)

    def rotate_cube(self, vertices, dcm):
        """Return vertices rotated by DCM (vertices shape (N,3), dcm (3,3))."""
        return dcm @ vertices.T

    def create_cube(self, ax, vertices):
        """Draw cube on 3D axes; vertices shape (3, 8). Return Poly3DCollection."""
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
        collection = Poly3DCollection(
            faces, facecolors=face_colors, linewidths=1, edgecolors="r"
        )
        ax.add_collection3d(collection)
        return collection

    def create_fig1(self):
        """Build Btot magnitude map (PlateCarree), attach to canvas1, draw."""
        if getattr(self, "canvas_fig1", None) is not None:
            try:
                self.canvas_fig1.get_tk_widget().destroy()
            except Exception:
                pass
        fig1 = Figure(figsize=(6.5, 3.5), facecolor=FIGURE_FACECOLOR)
        ax1 = fig1.add_subplot(111, projection=ccrs.PlateCarree())
        ax1.add_feature(cfeature.COASTLINE)
        ax1.add_feature(cfeature.BORDERS, linestyle=":")
        ax1.set_global()
        ax1.set_facecolor(FIGURE_FACECOLOR)

        lon, lat = np.meshgrid(
            np.linspace(-180, 179, self.Btot_magnitude.shape[2]),
            np.linspace(-89, 90, self.Btot_magnitude.shape[1]),
        )
        heatmap = ax1.contourf(
            lon, lat, self.Btot_magnitude[0], 60,
            transform=ccrs.PlateCarree(), cmap="jet",
        )
        cbar = fig1.colorbar(heatmap, ax=ax1, orientation="vertical", pad=0.05, shrink=0.8)
        vmin, vmax = heatmap.get_clim()
        ticks = np.linspace(vmin, vmax, num=4)
        cbar.set_ticks(ticks)
        cbar.ax.text(
            1.02, 1.05, r"$10^4$",
            transform=cbar.ax.transAxes,
            fontsize=8, va="bottom", ha="right",
            color="#FFFFFF", fontproperties=roboto_prop, fontweight="bold",
        )
        tick_labels = [f"{t/1e4:.1f}" for t in ticks]
        cbar.set_ticklabels(tick_labels)
        plt.setp(
            cbar.ax.get_yticklabels(),
            color="#FFFFFF", fontsize=8, fontproperties=roboto_prop, fontweight="bold",
        )
        cbar.set_label(
            "(nanoTesla)",
            color="#FFFFFF", fontproperties=roboto_prop, fontsize=8, fontweight="bold",
        )
        ax1.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
        ax1.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
        ax1.set_xlabel(
            "Longitude (degrees)",
            color="#FFFFFF", fontsize=8, labelpad=3,
            fontproperties=roboto_prop, fontweight="bold",
        )
        ax1.set_ylabel(
            "Latitude (degrees)",
            color="#FFFFFF", fontsize=8, labelpad=3,
            fontproperties=roboto_prop, fontweight="bold",
        )
        ax1.tick_params(axis="x", colors="#FFFFFF", labelsize=8, width=1.5)
        ax1.tick_params(axis="y", colors="#FFFFFF", labelsize=8, width=1.5)
        ax1.gridlines(
            draw_labels=False,
            xlocs=np.arange(-180, 181, 60),
            ylocs=np.arange(-90, 91, 30),
            color="#FFFFFF",
        )
        ax1.set_title(
            fr"$B_{{tot}} \, \mathrm{{Magnitude}}$ (ECEF) @{Constants.ALTITUDE} km",
            fontsize=10, color="#FFFFFF", pad=5,
            fontproperties=roboto_prop, fontweight="bold",
        )
        self.canvas_fig1 = self.create_canvas_figure(fig1, self.canvas1)
        self._canvas_resize_after_id = None
        self._canvas_last_wh = (0, 0)
        self._canvas_resize_delay_ms = 150
        self.canvas1.bind(
            "<Configure>",
            lambda e: self._on_figure_canvas_configure(e, self.canvas_fig1),
        )
        self.canvas_fig1.draw()

    def create_canvas(self, parent, row, column):
        """Create tk.Canvas in parent at grid (row, column) for Btot map; fills cell (responsive)."""
        canvas = tk.Canvas(parent, bg="black")
        canvas.grid(row=row, column=column, padx=PAD, pady=ROW_GAP, sticky="nsew")
        return canvas

    def _on_figure_canvas_configure(self, event, canvas_fig):
        """Debounced: handler sadece boyut kaydeder, geometry/draw yok. Fark >= 2px ise schedule."""
        if canvas_fig is None:
            return
        w = max(1, event.width)
        h = max(1, event.height)
        last = getattr(self, "_canvas_last_wh", (0, 0))
        if (w, h) == last:
            return
        if abs(w - last[0]) < 2 and abs(h - last[1]) < 2:
            return
        aid = getattr(self, "_canvas_resize_after_id", None)
        if aid:
            self.after_cancel(aid)
        delay = getattr(self, "_canvas_resize_delay_ms", 150)
        self._canvas_resize_after_id = self.after(
            delay,
            lambda: self._do_canvas_resize(canvas_fig, w, h),
        )

    def _do_canvas_resize(self, canvas_fig, w, h):
        """Sadece debounced callback'te: fig resize + draw_idle; boyut değişmediyse çizim yok."""
        self._canvas_resize_after_id = None
        if canvas_fig is None:
            return
        last = getattr(self, "_canvas_last_wh", (0, 0))
        if abs(w - last[0]) < 2 and abs(h - last[1]) < 2:
            return
        self._canvas_last_wh = (w, h)
        try:
            fig = canvas_fig.figure
            dpi = fig.get_dpi()
            fig.set_size_inches(w / dpi, h / dpi)
            canvas_fig.draw_idle()
        except Exception:
            pass

    def create_canvas_figure(self, fig, canvas):
        """Embed matplotlib figure in canvas; return FigureCanvasTkAgg. Caller should bind <Configure> for resize."""
        canvas_fig = FigureCanvasTkAgg(fig, master=canvas)
        canvas_fig.get_tk_widget().place(relx=0, rely=0, relwidth=1, relheight=1)
        canvas.update_idletasks()
        return canvas_fig
