"""Utility package: quaternion/geometry helpers.

Provides:
    - ``q_to_DCM``: Quaternion to DCM and rotate Btot from ECI to body.
    - ``euler_from_quaternion``: Quaternion to Euler (roll, pitch, yaw) in radians.
    - ``get_quaternion_from_euler``: Euler (rad) to quaternion [x, y, z, w].
"""

from utils.quaternion import (
    q_to_DCM,
    euler_from_quaternion,
    get_quaternion_from_euler,
)

__all__ = [
    "q_to_DCM",
    "euler_from_quaternion",
    "get_quaternion_from_euler",
]
