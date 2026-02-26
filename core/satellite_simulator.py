"""Attitude dynamics and magnetic field calculation for SatMagSim.

SatelliteSimulator: inertia J, gain k, disturbance N, noise; integrates
w and q with solve_ivp; calculate_magnetic_fields uses GMAT state,
geopack/IGRF/T89, and utils quaternion helpers.

MagneticFieldData: wraps data_magnetic, data_dyn_kin, data_PV, data_geodetic
into normalized arrays and magnitudes for visualization.
"""

import math
import time

import numpy as np
import pymap3d
from scipy.integrate import solve_ivp
from geopack import geopack, t89
from spacepy import coordinates as coord
from spacepy.time import Ticktock

from config.constants import Constants
from utils.quaternion import q_to_DCM, euler_from_quaternion, get_quaternion_from_euler
from core.gmat_sim import gator


class SatelliteSimulator:
    """Attitude dynamics (w, q) with magnetic torque and optional deployment timing."""

    def __init__(self, J, k, N, w_noise, Btot_noise):
        self.J = J
        self.k = k
        self.N = N
        self.w_noise = w_noise
        self.Btot_noise = Btot_noise
        self.timing_dict = {}
        self.J_inv = np.linalg.inv(J)

    def calculate_average_timings(self):
        """Return per-method average timings from timing_dict."""
        return {key: np.mean(times) for key, times in self.timing_dict.items()}

    @staticmethod
    def skew_symmetric(v):
        """Return 3x3 skew-symmetric (cross-product) matrix for vector v."""
        return np.array([
            [0, -v[2], v[1]],
            [v[2], 0, -v[0]],
            [-v[1], v[0], 0],
        ])

    def w_and_q(self, t, y, Btot_body, x):
        """RHS for w_dot and q_dot: magnetic torque, clipping, deployment timer."""
        start_time = time.time()
        w = y[0:3]
        q = y[3:7]
        Btot_body = Btot_body + self.Btot_noise
        H_RG = self.J @ w
        M_RG = np.cross((1e-9) * Btot_body, -self.k * H_RG) / (np.linalg.norm((1e-9) * Btot_body) ** 2)
        M_RG = np.clip(M_RG, -0.017, 0.017)
        torque_RG = self.skew_symmetric(M_RG) @ (Btot_body * 1e-9)

        if x <= int(Constants.DEPLOYMENT_TIMER * 60 / Constants.STEP):
            torque_RG[0] = 0
            torque_RG[1] = 0
            torque_RG[2] = 0
        else:
            torque_RG[2] = 0

        w_dot = self.J_inv @ (self.N - np.cross(w, H_RG) + torque_RG)

        omega1, omega2, omega3 = w
        Omega_br = np.array([
            [0, omega3, -omega2, omega1],
            [-omega3, 0, omega1, omega2],
            [omega2, -omega1, 0, omega3],
            [-omega1, -omega2, -omega3, 0],
        ])
        q_dot = 0.5 * Omega_br @ q

        self.timing_dict.setdefault("w_and_q", []).append(time.time() - start_time)
        return np.concatenate((w_dot, q_dot))

    def integrate_w_and_q(self, x, w, q, Btot_body, step):
        """Integrate w and q over one step; return w_sol, q_sol with noise on w."""
        start_time = time.time()
        y0 = np.concatenate((w, q))
        sol = solve_ivp(
            self.w_and_q,
            [0, step],
            y0,
            args=(Btot_body, x),
            method="DOP853",
            rtol=1e-9,
            atol=1e-9,
            t_eval=[step],
        )
        w_sol = sol.y[0:3, -1] + self.w_noise
        q_sol = sol.y[3:7, -1]
        self.timing_dict.setdefault("integrate_w_and_q", []).append(time.time() - start_time)
        return w_sol, q_sol

    def calculate_magnetic_fields(
        self,
        satellites,
        initial_ut,
        current_time,
        kp_index,
        x,
        num_steps,
        step,
        data_dyn_kin,
        data_PV,
        data_geodetic,
        data_magnetic,
    ):
        """One step: get GMAT state, compute IGRF+T89 B, update w/q and data dicts."""
        start_time = time.time()
        satellite = satellites[0]
        state = satellite.get_state(gator)
        r = state[:3]
        v = state[3:]
        spacecraft_name = satellite.get_name()

        ecllat, ecllon, alt = pymap3d.eci2geodetic(r[0] * 1e3, r[1] * 1e3, r[2] * 1e3, current_time)
        ps = geopack.recalc(initial_ut)
        ticks = Ticktock(current_time, "UTC")

        R_ECI = coord.Coords([r[0], r[1], r[2]], "ECI2000", "car")
        data_PV[spacecraft_name]["R_ECI"].append(r)
        data_PV[spacecraft_name]["velocity"].append(v)
        R_ECI.ticks = ticks
        R_GSM = R_ECI.convert("GSM", "car").data.flatten()

        xgsm, ygsm, zgsm = [R_GSM[0] / 6371.2, R_GSM[1] / 6371.2, R_GSM[2] / 6371.2]
        bint_xgsm, bint_ygsm, bint_zgsm = geopack.igrf_gsm(xgsm, ygsm, zgsm)
        bext_xgsm, bext_ygsm, bext_zgsm = t89.t89(kp_index + 1, ps, xgsm, ygsm, zgsm)

        bxgsm = bint_xgsm + bext_xgsm
        bygsm = bint_ygsm + bext_ygsm
        bzgsm = bint_zgsm + bext_zgsm
        Btot_GSM = coord.Coords([bxgsm, bygsm, bzgsm], "GSM", "car")
        Btot_GSM.ticks = ticks

        Btot_ECI = Btot_GSM.convert("J2000", "car").data
        Btot_ECI_flat = Btot_ECI.flatten()
        Btot_ECEF = Btot_GSM.convert("GEO", "car").data

        if x == 0:
            w = Constants.w
            q = Constants.q
            q_DCM, Btot_body = q_to_DCM(q, Btot_ECI_flat)
            eu_ang = euler_from_quaternion(q)
            quat_turn = get_quaternion_from_euler(eu_ang[0], eu_ang[1], eu_ang[1])
            data_dyn_kin[spacecraft_name]["w"] = [w]
            data_dyn_kin[spacecraft_name]["q"] = [q]
            data_dyn_kin[spacecraft_name]["DCM"] = [q_DCM]
            data_dyn_kin[spacecraft_name]["euler"] = [eu_ang]
            data_dyn_kin[spacecraft_name]["quat_turn"] = [quat_turn]
        else:
            w = data_dyn_kin[spacecraft_name]["w"][-1]
            q = data_dyn_kin[spacecraft_name]["q"][-1]
            q_DCM, Btot_body = q_to_DCM(q, Btot_ECI_flat)
            data_dyn_kin[spacecraft_name]["DCM"][-1] = q_DCM

        if x >= int(Constants.SEPERATION_TIME / Constants.STEP):
            w_sol, q_sol = self.integrate_w_and_q(x, w, q, Btot_body, step)
        else:
            w_sol, q_sol = w, q

        if x < num_steps - 1:
            eu_ang = euler_from_quaternion(q_sol)
            quat_turn = get_quaternion_from_euler(eu_ang[0], eu_ang[1], eu_ang[2])
            data_dyn_kin[spacecraft_name]["euler"].append(eu_ang)
            data_dyn_kin[spacecraft_name]["w"].append(w_sol)
            data_dyn_kin[spacecraft_name]["q"].append(q_sol)
            data_dyn_kin[spacecraft_name]["DCM"].append(q_DCM)
            data_dyn_kin[spacecraft_name]["quat_turn"].append(quat_turn)

        R_Body = q_DCM @ r
        data_PV[spacecraft_name]["R_Body"].append(R_Body)
        data_magnetic[spacecraft_name]["Btot_ECI"].append(Btot_ECI_flat)
        data_magnetic[spacecraft_name]["Btot_body"].append(Btot_body)
        data_magnetic[spacecraft_name]["Btot_ECEF"].append(Btot_ECEF)
        data_geodetic[spacecraft_name]["latitude"].append(ecllat)
        data_geodetic[spacecraft_name]["longitude"].append(ecllon)
        data_geodetic[spacecraft_name]["altitude"].append(alt)

        self.timing_dict.setdefault("calculate_magnetic_fields", []).append(time.time() - start_time)


class MagneticFieldData:
    """Wraps simulation output dicts into arrays for Magnetic Field GUI.

    Used by MagneticFieldGUI (Next after Spacecraft run):
    - latitude_data, longitude_data: orbit/position → map (white line + flying dot, progressive)
    - q_DCM: attitude per step → 3D panel (cube rotation and vector arrows)
    - angular_vel: wx, wy, wz [deg/s] → time plot (omega_x, omega_y, omega_z)
    All three visualizations use the same step index (frame) so they stay in sync.
    """

    def __init__(self, data_geodetic, data_magnetic, data_PV, data_dyn_kin):
        self.satellite_name = list(data_magnetic.keys())[0]
        self.latitude_data = data_geodetic[self.satellite_name]["latitude"]
        self.longitude_data = data_geodetic[self.satellite_name]["longitude"]
        self.altitude_data = data_geodetic[self.satellite_name]["altitude"]

        self.Btot_ECEF_data = np.squeeze(np.array(data_magnetic[self.satellite_name]["Btot_ECEF"])) / 1000
        self.Btot_ECI_data = np.array(data_magnetic[self.satellite_name]["Btot_ECI"]) / 1000
        self.Btot_body_data = np.array(data_magnetic[self.satellite_name]["Btot_body"]) / 1000

        self.Btot_ECI_mag = np.linalg.norm(self.Btot_ECI_data, axis=1)[:, np.newaxis]
        self.Btot_ECEF_mag = np.linalg.norm(self.Btot_ECEF_data, axis=1)[:, np.newaxis]
        self.Btot_body_mag = np.linalg.norm(self.Btot_body_data, axis=1)[:, np.newaxis]

        self.Btot_ECI_norm = self.Btot_ECI_data / self.Btot_ECI_mag
        self.Btot_body_norm = self.Btot_body_data / self.Btot_body_mag
        self.Btot_ECEF_norm = self.Btot_ECEF_data / self.Btot_ECEF_mag

        self.R_ECI_data = np.array(data_PV[self.satellite_name]["R_ECI"])
        self.R_ECI_mag = np.linalg.norm(self.R_ECI_data, axis=1)[:, np.newaxis]
        self.R_ECI_norm = self.R_ECI_data / self.R_ECI_mag

        self.V_ECI_data = np.array(data_PV[self.satellite_name]["velocity"])
        self.V_ECI_mag = np.linalg.norm(self.V_ECI_data, axis=1)[:, np.newaxis]
        self.V_ECI_norm = self.V_ECI_data / self.V_ECI_mag

        self.R_Body_data = np.array(data_PV[self.satellite_name]["R_Body"])
        self.R_Body_mag = np.linalg.norm(self.R_Body_data, axis=1)[:, np.newaxis]
        self.R_Body_norm = self.R_Body_data / self.R_Body_mag

        self.euler_angles = np.array(data_dyn_kin[self.satellite_name]["euler"]) * (180 / math.pi)
        self.angular_vel = np.array(data_dyn_kin[self.satellite_name]["w"]) * (180 / math.pi)
        self.q_DCM = np.array(data_dyn_kin[self.satellite_name]["DCM"])
