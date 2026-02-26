"""Entry point for SatMagSim Extended.

Applies theme (dark mode, Roboto, dark-blue) and runs the main GUI.
Run from project root: python main.py  or  python SatMagSim_Extended.py

Flow (birebir SatMagSim_Base / SatMagSim ile aynı):
- Backend: SpacecraftGUI → Run → run_simulation (gui/spacecraft_gui/_simulation.py)
  → core/satellite_simulator.calculate_magnetic_fields + MagneticFieldData
- Next → start_gui → MagneticFieldData(data_geodetic, data_magnetic, data_PV, data_dyn_kin)
  → MagneticFieldGUI(root, data) (gui/magnetic_field_gui)
- Frontend: harita çizgi+nokta (latitude_data, longitude_data), 3D küp (q_DCM),
  zaman grafiği (angular_vel wx/wy/wz), anlık B/altitude (update_gui) — hepsi aynı frame ile senkron.
"""

from config.theme import setup_theme
from gui import SpacecraftGUI

if __name__ == "__main__":
    setup_theme()
    app = SpacecraftGUI()
    app.mainloop()
