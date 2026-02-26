"""GUI package: main and auxiliary windows for SatMagSim Extended.

- SpacecraftGUI: main parameters window (Keplerian, run, deploy, next).
- MagneticFieldGUI: magnetic field visualization and ESP32 send.
- ImpulsiveBurnGUI: impulsive burn (Local/Spherical) and LoadScript.
"""

from gui.spacecraft_gui import SpacecraftGUI
from gui.magnetic_field_gui import MagneticFieldGUI
from gui.impulsive_burn_gui import ImpulsiveBurnGUI

__all__ = ["SpacecraftGUI", "MagneticFieldGUI", "ImpulsiveBurnGUI"]
