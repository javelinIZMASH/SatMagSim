"""Simulation and spacecraft constants for SatMagSim Extended.

``Constants``: Gravitational parameters, orbit elements, inertia matrix,
noise and time settings, CubeSat dimensions, impulsive maneuver defaults,
and derived quantities (T_PERIOD, INITIAL_UT, etc.).

Used by ``core`` and ``gui``; no side effects on import.
"""

import math
import datetime

import numpy as np


class Constants:
    """Central repository for simulation and spacecraft parameters.

    All values are class-level constants. Derived quantities (e.g.
    T_PERIOD, INITIAL_UT, SPECIFIC_TIME) are computed at class definition time.
    """

    # Gravitational constant (GM) for Earth (WGS84 model) [km^3/s^2]
    MU = 398600.4418

    # True anomalies (degrees)
    TRUE_ANOMALIES = [270]

    ALTITUDE = 500
    R_RADIUS = 6378.1363

    q = np.array([0, 0, 0, 1])
    w = np.array([0.03, 0.04, 0.05])

    SATELLITE_PARAMS = {
        "sma": 6878.1363,
        "ecc": 9.4080e-04,
        "inc": 97.8,
        "ra": 102,
        "aop": 0,
        "ta": 270,
        "srp_area": 0.01,
        "cr": 1.8,
        "cd": 2.2,
        "dry_mass": 0.8,
        "drag_area": 0.01,
    }

    impulsive_spherical_params = {
        "magnitude": 1,
        "azimuth": 0,
        "elevation": 0,
    }

    impulsive_local_params = {
        "element1": 1,
        "element2": 1,
        "element3": 1,
    }

    T_PERIOD = math.ceil(
        (2 * math.pi * math.sqrt(SATELLITE_PARAMS["sma"] ** 3 / MU))
    )
    DISTURBANCE_TORQUES = np.array([3e-07, 3e-07, 3e-07])
    PROPORTIONAL_CONSTANT = 0.007

    J_MATRIX = np.array([
        [0.000826, 0.000001, 0.0000000619],
        [0.000001, 0.000425, -0.000002],
        [0.0000000619, -0.000002, 0.0012],
    ])

    W_NOISE_SCALE = 1e-5
    BTOT_NOISE_SCALE = 100
    STEP = 10
    NUM_STEPS = 3600
    INTERVAL_DELAY = 20  # ms between animation frames (was 100; 5x faster for quicker testing)
    W_NOISE = W_NOISE_SCALE
    BTOT_NOISE = BTOT_NOISE_SCALE

    SPECIFIC_TIME_STR = "20 Jul 2020 12:00:00.000"
    SPECIFIC_TIME = datetime.datetime.strptime(
        SPECIFIC_TIME_STR, "%d %b %Y %H:%M:%S.%f"
    )
    SPECIFIC_TIME = SPECIFIC_TIME.replace(tzinfo=datetime.timezone.utc)

    T0 = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    INITIAL_UT = (SPECIFIC_TIME - T0).total_seconds()

    CUBE_SIZE = [0.6936, 0.6936, 0.1942]
    CUBE_ORIGIN = np.array([
        [-0.6936 / 2, -0.6936 / 2, -0.1942 / 2],
        [0.6936 / 2, -0.6936 / 2, -0.1942 / 2],
        [0.6936 / 2, 0.6936 / 2, -0.1942 / 2],
        [-0.6936 / 2, 0.6936 / 2, -0.1942 / 2],
        [-0.6936 / 2, -0.6936 / 2, 0.1942 / 2],
        [0.6936 / 2, -0.6936 / 2, 0.1942 / 2],
        [0.6936 / 2, 0.6936 / 2, 0.1942 / 2],
        [-0.6936 / 2, 0.6936 / 2, 0.1942 / 2],
    ])

    RESOLUTION_SCALE = 10
    RESOLUTION = RESOLUTION_SCALE
    KP_IDX = 6
    CURRENT_TIME = SPECIFIC_TIME
    SEPERATION_TIME = 10  # seconds
    DEPLOYMENT_TIMER = 20  # minutes
