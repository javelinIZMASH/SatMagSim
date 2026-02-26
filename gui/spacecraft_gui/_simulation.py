"""Simulation run, Btot grid calculation, and Apply-values logic for SpacecraftGUI."""

import datetime
import os
import threading
import time

import numpy as np
import pymap3d
import customtkinter as ctk
import ctypes

from customtkinter import CTk
from geopack import geopack, t89
from spacepy import coordinates as coord
from spacepy.time import Ticktock

from config.theme import script_dir
from config.constants import Constants
from core.gmat_sim import satellites, gator, initialize_data_structures
from core.satellite_simulator import SatelliteSimulator, MagneticFieldData

# Module-level shared data (used by run_simulation and start_gui)
data_magnetic, data_dyn_kin, data_PV, data_geodetic = initialize_data_structures(
    satellites
)


class SpacecraftGUISimulationMixin:
    """Mixin: INITGUI_*, run_simulation, run_calculations, start_simulation_thread, start_gui, apply_values."""

    def INITGUI_geodetic_to_eci(self, lat, lon, altitude):
        """Convert geodetic (deg, m) to ECI at Constants.SPECIFIC_TIME. Returns (3,) array."""
        x, y, z = pymap3d.geodetic2eci(
            lat, lon, altitude * 1e3, Constants.SPECIFIC_TIME, deg=True
        )
        return np.array([float(np.asarray(x).flat[0]), float(np.asarray(y).flat[0]), float(np.asarray(z).flat[0])])

    def INITGUI_calc_geomagnetic_fields(self, r):
        """Compute Btot in GEO (ECEF) from ECI position r (km)."""
        R_ECI = coord.Coords([r[0], r[1], r[2]], "ECI2000", "car")
        R_ECI.ticks = self.ticks
        R_GSM = R_ECI.convert("GSM", "car").data.flatten()
        xgsm, ygsm, zgsm = R_GSM[0] / 6371.2, R_GSM[1] / 6371.2, R_GSM[2] / 6371.2
        bint_xgsm, bint_ygsm, bint_zgsm = geopack.igrf_gsm(xgsm, ygsm, zgsm)
        bext_xgsm, bext_ygsm, bext_zgsm = t89.t89(
            self.KP_IDX + 1, self.ps, xgsm, ygsm, zgsm
        )
        bxgsm = bint_xgsm + bext_xgsm
        bygsm = bint_ygsm + bext_ygsm
        bzgsm = bint_zgsm + bext_zgsm
        Btot_GSM = coord.Coords([bxgsm, bygsm, bzgsm], "GSM", "car")
        Btot_GSM.ticks = self.ticks
        return Btot_GSM.convert("GEO", "car").data

    def INITGUI_run_simulation(self):
        """Start run_calculations in a background thread."""
        try:
            self.is_calculate_button_pressed = True
            self.altitude_checked = self.altitude_check.get()
            if self.altitude_checked:
                self.altitude_value = float(self.altitude_entry.get().strip() or "0")
            else:
                self.altitude_value = float(self.semi_major_axis_entry.get().strip() or "6878.1363") - 6378.1363
            self.progress_file_label.configure(text="Calculate running...")
            self.run_thread = threading.Thread(target=self._run_calculations_safe)
            self.run_thread.start()
        except ValueError as e:
            self.progress_file_label.configure(text=f"Error: {str(e)}")

    def start_simulation_thread(self):
        """Start run_simulation in a background thread."""
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.start()

    def run_simulation(self):
        """Propagate with GMAT and compute magnetic fields for each step; update progress."""
        import datetime as _dt
        self.is_calculate_button_pressed = False
        step = Constants.STEP
        num_steps = Constants.NUM_STEPS
        specific_time = Constants.SPECIFIC_TIME
        initial_ut = Constants.INITIAL_UT
        kp_index = Constants.KP_IDX
        total_steps = int(num_steps / step)
        current_step = 0
        start_time_sim = time.time()
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
            current_step += 1
            progress_value = (current_step / total_steps) * 100
            self.after(0, self.update_progress, progress_value, current_step, total_steps)
            self.update_idletasks()

        end_time_sim = time.time()
        total_sim_time = end_time_sim - start_time_sim
        print(f"Total Sim. Time: {total_sim_time:.1f} saniye")
        simulator.timing_dict["Total simulation time"] = total_sim_time
        print("Average timings:", simulator.calculate_average_timings())
        self.progress_file_label.configure(text=f"{total_sim_time:.1f}sec")
        self.next_button.configure(state="normal", fg_color="green", hover_color="darkgreen")
        return simulator

    def start_gui(self):
        """Open Magnetic Field Visualization window (lazy import)."""
        from gui.magnetic_field_gui import MagneticFieldGUI
        from gui.common import MAGNETIC_WINDOW_MIN_WIDTH, MAGNETIC_WINDOW_MIN_HEIGHT
        root = CTk()
        root.title("Magnetic Field Visualization")
        root.configure(fg_color="#2B2B2B")
        roboto_font_path = os.path.join(script_dir, "Roboto-Regular.ttf")
        if not os.path.isfile(roboto_font_path):
            roboto_font_path = "C:/Users/GumushAerospace/Desktop/taurus/Roboto-Regular.ttf"
        if os.path.isfile(roboto_font_path):
            ctypes.windll.gdi32.AddFontResourceW(roboto_font_path)
        root.minsize(MAGNETIC_WINDOW_MIN_WIDTH, MAGNETIC_WINDOW_MIN_HEIGHT)
        root.resizable(True, True)
        data = MagneticFieldData(data_geodetic, data_magnetic, data_PV, data_dyn_kin)
        app2 = MagneticFieldGUI(root, data)
        app2.draw_figures()
        root.mainloop()

    def _finish_run_calculations(self, npy_filename):
        """Called on main thread after run_calculations: update label and draw Btot map."""
        try:
            self.progress_file_label.configure(text=f"Saved: {npy_filename}")
            self.create_fig1()
        except Exception as e:
            self.progress_file_label.configure(text=f"Error: {str(e)}")

    def _finish_run_calculations_error(self, err_msg):
        """Called on main thread when run_calculations fails."""
        self.progress_file_label.configure(text=f"Error: {err_msg}")

    def _run_calculations_safe(self):
        """Wrapper that runs run_calculations and reports errors to main thread."""
        try:
            self.run_calculations()
        except Exception as e:
            self.after(0, self._finish_run_calculations_error, str(e))

    def run_calculations(self):
        """Compute Btot grid over lat/lon at current altitude; save .npy and draw fig1."""
        latitudes_2d = np.linspace(-89, 90, Constants.RESOLUTION)
        longitudes_2d = np.linspace(-180, 179, Constants.RESOLUTION)
        altitude_value = self.altitude_value
        Constants.ALTITUDE = self.altitude_value
        eci_coords = np.zeros((3, len(latitudes_2d), len(longitudes_2d)))
        Btot_ECEF_data = np.zeros((3, len(latitudes_2d), len(longitudes_2d)))
        total_steps = len(latitudes_2d) * len(longitudes_2d)
        self.total_steps = total_steps
        current_step = 0

        for i, lat in enumerate(latitudes_2d):
            for j, lon in enumerate(longitudes_2d):
                eci_coords[:, i, j] = self.INITGUI_geodetic_to_eci(
                    lat, lon, altitude_value
                )
                r = eci_coords[:, i, j] * 1e-3
                b_geo = self.INITGUI_calc_geomagnetic_fields(r)
                Btot_ECEF_data[:, i, j] = np.asarray(b_geo).flatten()[:3]
                current_step += 1
                progress_value = (current_step / total_steps) * 100
                self.after(0, self.update_progress, progress_value, current_step, total_steps)
                self.update_idletasks()

        self.Btot_magnitude = np.linalg.norm(Btot_ECEF_data, axis=0)
        self.Btot_magnitude = self.Btot_magnitude[np.newaxis, :, :]
        altitude_value_int = int(altitude_value)
        npy_filename = f"Btot_magnitude_altitude_{altitude_value_int}.npy"
        np.save(npy_filename, self.Btot_magnitude)
        self.after(0, self._finish_run_calculations, npy_filename)

    def apply_values(self):
        """Read all GUI entries and write to Constants; validate ranges."""
        try:
            if self.altitude_check.get():
                Constants.ALTITUDE = int(self.altitude_entry.get())
                Constants.R_RADIUS = 6378.1363
                altitude_value = float(self.altitude_entry.get())
                Constants.SATELLITE_PARAMS["sma"] = Constants.R_RADIUS + altitude_value
            else:
                Constants.SATELLITE_PARAMS["sma"] = float(self.semi_major_axis_entry.get())

            if Constants.SATELLITE_PARAMS["sma"] <= 6478.1363:
                raise ValueError("Semi-major axis must be greater than 6478.1363 km")
            self.progress_file_label.configure(text="")

            Constants.SATELLITE_PARAMS["ecc"] = float(self.ecc_entry.get())
            if not (
                Constants.SATELLITE_PARAMS["ecc"] < 0.9999999
                or Constants.SATELLITE_PARAMS["ecc"] > 1.0
            ):
                raise ValueError("Eccentricity must be < 0.9999999 or > 1")
            self.progress_file_label.configure(text="")

            Constants.SATELLITE_PARAMS["inc"] = float(self.inc_entry.get())
            if not (0 <= Constants.SATELLITE_PARAMS["inc"] <= 180):
                raise ValueError("Inclination must be between 0 and 180 degrees")
            self.progress_file_label.configure(text="")

            Constants.SATELLITE_PARAMS["ra"] = float(self.ra_entry.get())
            Constants.SATELLITE_PARAMS["aop"] = float(self.aop_entry.get())
            Constants.SATELLITE_PARAMS["ta"] = float(self.ta_entry.get())
            Constants.SATELLITE_PARAMS["dry_mass"] = float(self.dry_mass_entry.get())
            Constants.SATELLITE_PARAMS["drag_area"] = float(self.drag_area_entry.get())
            Constants.SATELLITE_PARAMS["srp_area"] = float(self.srp_area_entry.get())
            Constants.SATELLITE_PARAMS["cr"] = float(self.cr_entry.get())
            Constants.SATELLITE_PARAMS["cd"] = float(self.cd_entry.get())

            Constants.DISTURBANCE_TORQUES[0] = float(self.torque_entries[0].get())
            Constants.DISTURBANCE_TORQUES[1] = float(self.torque_entries[1].get())
            Constants.DISTURBANCE_TORQUES[2] = float(self.torque_entries[2].get())
            for i in range(3):
                for j in range(3):
                    Constants.J_MATRIX[i][j] = float(
                        self.inertia_matrix_entries[i][j].get()
                    )
            Constants.PROPORTIONAL_CONSTANT = float(self.prop_const_entry.get())
            Constants.W_NOISE_SCALE = float(self.w_noise_entry.get())
            Constants.BTOT_NOISE_SCALE = int(self.b_noise_entry.get())
            Constants.SPECIFIC_TIME_STR = self.epoch_entry.get()
            Constants.KP_IDX = int(self.mag_index_entry.get())
            Constants.TRUE_ANOMALIES = float(self.ta_entry.get())
            Constants.NUM_STEPS = int(self.simulation_time_entry.get())
            Constants.STEP = int(self.time_step_entry.get())
            Constants.INTERVAL_DELAY = int(self.interval_entry.get())
            Constants.RESOLUTION = int(self.resolution_entry.get())
            Constants.DEPLOYMENT_TIMER = int(self.deployment_timer_entry.get())
            Constants.SEPERATION_TIME = int(self.seperation_entry.get())

            if Constants.SEPERATION_TIME > 60:
                raise ValueError("Seperation Time must be less than 1 min")
            self.progress_file_label.configure(text="")
            if Constants.DEPLOYMENT_TIMER * 60 > (Constants.NUM_STEPS / 2):
                raise ValueError("Deployment Timer cannot exceed half of NUM_STEP")
            self.progress_file_label.configure(text="")

            Constants.q = np.array(
                [
                    float(self.q_entries[0].get()),
                    float(self.q_entries[1].get()),
                    float(self.q_entries[2].get()),
                    float(self.q_entries[3].get()),
                ]
            )
            Constants.w = np.array(
                [
                    float(self.angular_rate_entries[0].get()),
                    float(self.angular_rate_entries[1].get()),
                    float(self.angular_rate_entries[2].get()),
                ]
            )

            self.progress_file_label.configure(text="Initial Values Saved.")
        except ValueError as e:
            self.progress_file_label.configure(text=f"Error: {str(e)}")
