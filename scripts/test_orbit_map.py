"""
Test script: same orbit data as main.py (live simulation), animated with segment drawing.

- Runs the same simulation as main.py (GMAT + SatelliteSimulator) to get latitude_data, longitude_data.
- Animates the orbit on a map: trail grows frame-by-frame, Taurus dot moves; segments at ±180° so no straight line across map.

Run from project root:
  python scripts/test_orbit_map.py
"""

import sys
import datetime as _dt

# Project root for imports
_script_dir = __file__.replace("\\", "/").rsplit("/", 1)[0]
_root = _script_dir.rsplit("/", 1)[0]
if _root not in sys.path:
    sys.path.insert(0, _root)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from config.constants import Constants
from core.gmat_sim import satellites, gator, initialize_data_structures
from core.satellite_simulator import SatelliteSimulator, MagneticFieldData


def _to_plot_lon(lon):
    """Convert longitude to -180..180 for PlateCarree (180 -> -180, 360 -> 0 stays 0)."""
    lon = np.asarray(lon, dtype=float)
    out = np.where(lon > 180, lon - 360, lon)
    return np.where(out < -180, out + 360, out)


def _orbit_segments(lon, lat):
    """Split at date-line wrap. Works for both -180..180 and 0-360 longitude.
    Wrap = crossing 180° (e.g. 350->10 or 170->-170). Each segment plotted in -180..180."""
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    if len(lon) == 0:
        return []
    if len(lon) == 1:
        return [(_to_plot_lon(lon), lat)]
    # Detect wrap: cross from [180,360] to [0,180) or vice versa (in 0-360 sense)
    lon360 = lon % 360.0
    cross_high_low = (lon360[:-1] >= 180) & (lon360[1:] < 180)
    cross_low_high = (lon360[:-1] < 180) & (lon360[1:] >= 180)
    gaps = cross_high_low | cross_low_high
    if not np.any(gaps):
        return [(_to_plot_lon(lon), lat)]
    break_indices = np.where(gaps)[0] + 1
    starts = np.concatenate([[0], break_indices])
    ends = np.concatenate([break_indices, [len(lon)]])
    return [(_to_plot_lon(lon[s:e]), lat[s:e]) for s, e in zip(starts, ends) if e > s]


def run_simulation():
    """Same loop as SpacecraftGUI.run_simulation; returns MagneticFieldData."""
    data_magnetic, data_dyn_kin, data_PV, data_geodetic = initialize_data_structures(satellites)
    step = Constants.STEP
    num_steps = Constants.NUM_STEPS
    specific_time = Constants.SPECIFIC_TIME
    initial_ut = Constants.INITIAL_UT
    kp_index = Constants.KP_IDX
    total_steps = int(num_steps / step)
    time_ = 0.0

    for x in range(total_steps):
        gator.Step(step)
        time_ += step
        current_time = specific_time + _dt.timedelta(seconds=time_)
        simulator = SatelliteSimulator(
            J=Constants.J_MATRIX,
            k=Constants.PROPORTIONAL_CONSTANT,
            N=np.random.randn(1) * Constants.DISTURBANCE_TORQUES,
            w_noise=np.random.randn(3) * Constants.W_NOISE,
            Btot_noise=np.random.randn(3) * Constants.BTOT_NOISE,
        )
        simulator.calculate_magnetic_fields(
            satellites=satellites,
            initial_ut=initial_ut,
            current_time=current_time,
            kp_index=kp_index,
            x=x,
            num_steps=num_steps,
            step=step,
            data_dyn_kin=data_dyn_kin,
            data_PV=data_PV,
            data_geodetic=data_geodetic,
            data_magnetic=data_magnetic,
        )
        initial_ut += Constants.STEP

    return MagneticFieldData(data_geodetic, data_magnetic, data_PV, data_dyn_kin)


def main():
    print("Running same simulation as main.py (GMAT + magnetic fields)...")
    data = run_simulation()
    lon = np.asarray(data.longitude_data, dtype=float)
    lat = np.asarray(data.latitude_data, dtype=float)
    n = len(lon)
    print(f"Got {n} points. Building map animation (segments at ±180°)...")

    fig = plt.figure(figsize=(12, 6), facecolor="#2B2B2B")
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.set_global()
    ax.set_facecolor("#2B2B2B")
    ax.set_title("Test: Orbit (same data as main.py, segment draw)", color="white", fontsize=12)
    ax.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
    ax.tick_params(colors="white")

    segment_lines = []
    point_plot, = ax.plot([], [], marker="o", color="white", transform=ccrs.PlateCarree())
    label = ax.text(0, 0, "", color="white", fontsize=8, ha="right", transform=ccrs.PlateCarree())

    def init():
        for line in segment_lines:
            try:
                line.remove()
            except (ValueError, AttributeError):
                pass
        segment_lines.clear()
        point_plot.set_data([], [])
        label.set_text("")
        return point_plot, label

    def update(frame):
        for line in segment_lines:
            try:
                line.remove()
            except (ValueError, AttributeError):
                pass
        segment_lines.clear()
        lon_trail = lon[:frame]
        lat_trail = lat[:frame]
        if len(lon_trail) > 0:
            for seg_lon, seg_lat in _orbit_segments(lon_trail, lat_trail):
                line, = ax.plot(
                    seg_lon, seg_lat,
                    color="white", linewidth=1.5,
                    transform=ccrs.PlateCarree(),
                )
                segment_lines.append(line)
        lon_cur = float(_to_plot_lon(np.array([lon[frame]]))[0])
        lat_cur = lat[frame]
        point_plot.set_data([lon_cur], [lat_cur])
        label.set_position((lon_cur, lat_cur))
        label.set_text("Taurus  ")
        return point_plot, label

    ani = FuncAnimation(
        fig, update,
        frames=range(n),
        init_func=init,
        blit=False,
        interval=20,
        repeat=False,
    )
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
