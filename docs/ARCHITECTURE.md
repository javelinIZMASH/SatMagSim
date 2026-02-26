# Architecture

High-level view of the SatMagSim Extended application: purpose, components, entry points, and conventions. See `CONFIG_CONTRACT.md` and `DATA_CONTRACT.md` for config and in-memory data details.

---

## Purpose

Academic desktop application for satellite attitude dynamics and magnetic field simulation: GMAT orbit propagation, IGRF/T89 magnetic field, reaction-wheel–style magnetic torque control, and visualization (orbit map, 3D cube, angular velocity, Btot magnitude). Single entry point (`main.py`) opens SpacecraftGUI; after Run, MagneticFieldGUI shows orbit, attitude, and field data. No pipeline file outputs; all data is in-memory and passed between GUI stages.

---

## Components

1. **Core** — GMAT spacecraft, force model, propagator (`core/gmat_sim.py`); attitude dynamics and magnetic field integration (`core/satellite_simulator.py`). Produces in-memory dicts: `data_magnetic`, `data_dyn_kin`, `data_PV`, `data_geodetic`; and `MagneticFieldData` for the second GUI.
2. **GUI** — SpacecraftGUI (parameters, Run, Next) in `gui/spacecraft_gui/`; MagneticFieldGUI (map, 3D, time plot, ESP32) in `gui/magnetic_field_gui/`; ImpulsiveBurnGUI in `gui/impulsive_burn_gui.py`. Layout and styling from `gui/ui_system.py`, `gui/common.py`, `config/theme.py`.
3. **Config** — `config/constants.py` (Constants: orbit, inertia, time, noise); `config/theme.py` (theme, font paths, `script_dir`). UI constants in `gui/ui_system.py` and `gui/common.py`.

---

## Entry points

- **`main.py`** (or **`SatMagSim_Extended.py`**) — Apply theme (`config.theme.setup_theme`), then run `SpacecraftGUI()` and `mainloop()`. No CLI arguments.
- **SpacecraftGUI** — User sets parameters, runs simulation (thread → `run_simulation` → `calculate_magnetic_fields`), then "Next" builds `MagneticFieldData` and opens MagneticFieldGUI.
- **ImpulsiveBurnGUI** — Opened from SpacecraftGUI; impulsive burn (Local/Spherical), Apply, Run, LoadScript; does not replace the main flow.

---

## Conventions

- **Config:** All simulation and spacecraft constants in `config.constants.Constants`; theme and paths in `config.theme`. See `docs/CONFIG_CONTRACT.md`.
- **Data flow:** Core produces four dicts keyed by spacecraft name; `MagneticFieldData` wraps them for MagneticFieldGUI. See `docs/DATA_CONTRACT.md`.
- **UI:** Single source of truth for layout: `gui.ui_system` (spacing, panels, forms); fonts/colors/window sizes in `gui.common`. No arbitrary magic numbers in frames.
- **GMAT:** Loaded via `load_gmat.py`; `GmatInstall` must point to GMAT root. GMAT is not on PyPI.
