# Data contract

In-memory data structures produced by core and consumed by the GUIs. No file outputs are part of this contract; all data is passed in process. Derived from current code; no fabrication.

---

## Producers

- **`core.gmat_sim.initialize_data_structures(satellites)`** — Returns `(data_magnetic, data_dyn_kin, data_PV, data_geodetic)`. Each dict is keyed by spacecraft name (e.g. `Taurus1`).
- **`core.satellite_simulator.SatelliteSimulator.calculate_magnetic_fields(...)`** — Fills the four dicts for each step (GMAT state → IGRF/T89 B → attitude integration → append to lists).
- **`core.satellite_simulator.MagneticFieldData(data_geodetic, data_magnetic, data_PV, data_dyn_kin)`** — Wraps the four dicts into normalized arrays and magnitudes for MagneticFieldGUI.

---

## data_magnetic (per spacecraft)

| Key | Type | Description |
|-----|------|-------------|
| Bint_ECI | list | (Initialized; may be unused in current flow) |
| Bext_ECI | list | (Initialized; may be unused in current flow) |
| Btot_ECI | list of (3,) | Total B in ECI per step |
| Btot_body | list of (3,) | Total B in body frame per step |
| Btot_ECEF | list | B in ECEF (GEO) per step |

---

## data_dyn_kin (per spacecraft)

| Key | Type | Description |
|-----|------|-------------|
| w | list of (3,) | Angular velocity (rad/s) per step |
| q | list of (4,) | Quaternion per step |
| DCM | list of 3×3 | Direction cosine matrix (body from ECI) per step |
| euler | list of (3,) | Euler angles (rad) per step |
| quat_turn | list | Quaternion turn (for display) per step |

---

## data_PV (per spacecraft)

| Key | Type | Description |
|-----|------|-------------|
| R_ECI | list of (3,) | Position in ECI (km) per step |
| R_Body | list of (3,) | Position in body frame per step |
| velocity | list of (3,) | Velocity in ECI (km/s) per step |

---

## data_geodetic (per spacecraft)

| Key | Type | Description |
|-----|------|-------------|
| latitude | list | Geodetic latitude (deg) per step |
| longitude | list | Geodetic longitude (deg) per step |
| altitude | list | Altitude (km) per step |

---

## MagneticFieldData (consumer: MagneticFieldGUI)

**Constructor:** `MagneticFieldData(data_geodetic, data_magnetic, data_PV, data_dyn_kin)`. Uses first spacecraft name from `data_magnetic.keys()`.

| Attribute | Shape / unit | Description |
|-----------|--------------|-------------|
| satellite_name | str | First spacecraft name |
| latitude_data, longitude_data, altitude_data | list | From data_geodetic (orbit for map) |
| Btot_ECEF_data, Btot_ECI_data, Btot_body_data | ndarray | In nT; divided by 1000 in constructor |
| Btot_ECI_mag, Btot_ECEF_mag, Btot_body_mag | ndarray | Magnitudes |
| Btot_ECI_norm, Btot_body_norm, Btot_ECEF_norm | ndarray | Normalized vectors |
| R_ECI_data, R_ECI_mag, R_ECI_norm | ndarray | Position ECI (km) |
| V_ECI_data, V_ECI_mag, V_ECI_norm | ndarray | Velocity ECI |
| R_Body_data, R_Body_mag, R_Body_norm | ndarray | Position body frame |
| euler_angles | ndarray | Euler in degrees (rad × 180/π) |
| angular_vel | ndarray | Angular velocity in deg/s |
| q_DCM | ndarray | DCM per step (3D cube rotation) |

All arrays are indexed by step (frame); MagneticFieldGUI keeps map, 3D panel, and time plot in sync by shared frame index.

---

## Notes

- **Stage:** Data is produced in `gui/spacecraft_gui/_simulation.run_simulation` → `SatelliteSimulator.calculate_magnetic_fields`; consumed by `MagneticFieldGUI(root, data)` where `data` is a `MagneticFieldData` instance.
- **GMAT state:** `gator.GetState()` (from `core.gmat_sim`) returns position + velocity; step size and count from `Constants.STEP`, `Constants.NUM_STEPS`.
