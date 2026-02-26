"""Quaternion and rotation utilities for attitude and magnetic field transforms.

Google-style docstrings; used by core (SatelliteSimulator) and gui (Euler/quat display).
"""

import numpy as np


def q_to_DCM(q, Btot_ECI):
    """Build rotation matrix from quaternion and rotate Btot from ECI to body.

    Args:
        q: Quaternion (q1, q2, q3, q4) scalar-last convention.
        Btot_ECI: Total magnetic field in ECI, shape (3,) or (3, 1).

    Returns:
        tuple: (q_DCM, Btot_body)
            - q_DCM: 3x3 direction cosine matrix (body from ECI).
            - Btot_body: Btot expressed in body frame, shape (3,).
    """
    q1, q2, q3, q4 = q
    q_DCM = np.array([
        [
            q4 ** 2 + q1 ** 2 - q2 ** 2 - q3 ** 2,
            2 * (q1 * q2 + q3 * q4),
            2 * (q1 * q3 - q2 * q4),
        ],
        [
            2 * (q1 * q2 - q3 * q4),
            q4 ** 2 - q1 ** 2 + q2 ** 2 - q3 ** 2,
            2 * (q2 * q3 + q1 * q4),
        ],
        [
            2 * (q1 * q3 + q2 * q4),
            2 * (q2 * q3 - q1 * q4),
            q4 ** 2 - q1 ** 2 - q2 ** 2 + q3 ** 2,
        ],
    ])
    Btot_ECI_flat = np.asarray(Btot_ECI).flatten()
    Btot_body = q_DCM @ Btot_ECI_flat
    return q_DCM, Btot_body


def euler_from_quaternion(q):
    """Convert a quaternion into Euler angles (roll, pitch, yaw).

    Args:
        q: Quaternion (x, y, z, w) or (q1, q2, q3, q4). Interpreted as x, y, z, w.

    Returns:
        tuple: (roll_x, pitch_y, yaw_z) in radians.
    """
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


def get_quaternion_from_euler(roll, pitch, yaw):
    """Convert Euler angles (roll, pitch, yaw) to a quaternion.

    Args:
        roll: Rotation around x-axis, radians.
        pitch: Rotation around y-axis, radians.
        yaw: Rotation around z-axis, radians.

    Returns:
        tuple: (qx, qy, qz, qw) in [x, y, z, w] format.
    """
    qx = (
        np.sin(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2)
        - np.cos(roll / 2) * np.sin(pitch / 2) * np.sin(yaw / 2)
    )
    qy = (
        np.cos(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2)
        + np.sin(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2)
    )
    qz = (
        np.cos(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2)
        - np.sin(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2)
    )
    qw = (
        np.cos(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2)
        + np.sin(roll / 2) * np.sin(pitch / 2) * np.sin(yaw / 2)
    )
    return qx, qy, qz, qw
