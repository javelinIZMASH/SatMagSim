# SatMagSim Extended

**Satellite attitude dynamics & magnetic field simulation with GMAT and CustomTkinter GUI**

Desktop application for orbit propagation (GMAT), IGRF/T89 magnetic field, magnetic-torque attitude dynamics, and visualization: SpacecraftGUI (parameters, Run, Next) and MagneticFieldGUI (orbit map, 3D cube, angular velocity, Btot magnitude). Single entry point; no pipeline file outputs — all data is in-memory between GUI stages.

---

## Application flow

```
main.py  (or SatMagSim_Extended.py)
    │
    ├─ setup_theme()  ───────────── config/theme.py (dark, Roboto, dark-blue)
    │
    └─ SpacecraftGUI
            │
            ├─ Run  ─────────────── core/gmat_sim (GMAT) + core/satellite_simulator
            │                         → data_magnetic, data_dyn_kin, data_PV, data_geodetic
            │
            └─ Next ─────────────── MagneticFieldData(...) → MagneticFieldGUI
                                      (orbit map, 3D attitude, angular velocity, Btot)
```

ImpulsiveBurnGUI can be opened from SpacecraftGUI for Delta-V (Local/Spherical) and GMAT script run.

---

## Quick start

### Prerequisites

| Dependency | Install |
|-----------|---------|
| Python ≥ 3.10 | [python.org](https://www.python.org/) |
| GMAT R2025a (or compatible) | [GMAT wiki](https://github.com/NASA-GMAT/GMAT/wiki) — set `GmatInstall` in `load_gmat.py` |
| pip packages | `pip install -r requirements.txt` |

> **Note:** GMAT is not on PyPI. Install GMAT and run its API startup (e.g. `BuildApiStartupFile.py` once). Point `load_gmat.GmatInstall` in `load_gmat.py` to your GMAT top-level folder.

### Run the application

```bash
python main.py
```

Or:

```bash
python SatMagSim_Extended.py
```

Use **Run** in SpacecraftGUI to simulate; then **Next** to open the magnetic field visualization window.

---

## Project structure

```
satmagsim/
├── main.py                 # Single entry point
├── SatMagSim_Extended.py   # Alternative entry
├── load_gmat.py            # GMAT API loader (GmatInstall, get_gmat_data_path)
│
├── config/
│   ├── constants.py        # Constants: orbit, inertia, time, noise
│   └── theme.py            # Theme, script_dir, roboto_prop
│
├── core/
│   ├── gmat_sim.py         # GMAT spacecraft, force model, propagator, data structures
│   └── satellite_simulator.py  # Attitude dynamics, MagneticFieldData
│
├── gui/
│   ├── common.py           # Fonts, colors, window sizes
│   ├── ui_system.py        # Layout contract (spacing, panels, forms)
│   ├── spacecraft_gui/     # Parameter window (Run, Next)
│   ├── magnetic_field_gui/ # Visualization (map, 3D, time plot)
│   └── impulsive_burn_gui.py
│
├── utils/
│   └── quaternion.py       # q_to_DCM, euler_from_quaternion, etc.
│
├── docs/                   # Architecture & contract documentation
├── requirements.txt        # Python dependencies
└── .gitignore
```

---

## Configuration

- **Simulation and spacecraft:** `config/constants.py` — class `Constants` (MU, SATELLITE_PARAMS, J_MATRIX, STEP, NUM_STEPS, SPECIFIC_TIME, etc.). See [`docs/CONFIG_CONTRACT.md`](docs/CONFIG_CONTRACT.md).
- **Theme and paths:** `config/theme.py` — `setup_theme()`, `script_dir`, `roboto_prop`. Font and theme files are resolved from project root first, then fallback.
- **UI layout:** `gui/ui_system.py` (spacing, panels, form columns); `gui/common.py` (fonts, colors, window minsize/default size).

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Components, entry points, conventions |
| [`docs/CONFIG_CONTRACT.md`](docs/CONFIG_CONTRACT.md) | config.constants, config.theme, gui.ui_system, gui.common |
| [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md) | In-memory data structures (data_*, MagneticFieldData) |
| [`docs/REFACTOR_RULES_AND_PLAN.md`](docs/REFACTOR_RULES_AND_PLAN.md) | Code wiki alignment, refactor plan, constraints |

Additional project notes: `PROJECT_STRUCTURE.md`, `UI_CHECKLIST.md`, and comparison docs in the repo root remain as supplementary material.

---

## License

Academic use. See project documentation for terms.
