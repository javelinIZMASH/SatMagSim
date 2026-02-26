# Config contract

What each config and UI-config module provides: constants, units, and layout rules. No code behavior changed.

---

## config.constants (Constants)

**Role:** Simulation and spacecraft parameters: gravity, orbit, inertia, noise, time, impulsive burn defaults, and derived quantities.

| Symbol | Unit / type | Description |
|--------|-------------|-------------|
| **MU** | km³/s² | Earth gravitational parameter (WGS84) |
| **R_RADIUS** | km | Earth radius reference |
| **TRUE_ANOMALIES** | degrees | List of true anomalies (e.g. [270]) |
| **ALTITUDE** | km | Reference altitude |
| **q** | — | Initial quaternion (e.g. [0,0,0,1]) |
| **w** | rad/s | Initial angular velocity (e.g. [0.03, 0.04, 0.05]) |
| **SATELLITE_PARAMS** | mixed | sma (km), ecc, inc, ra, aop, ta (deg), srp_area (m²), cr, cd, dry_mass (kg), drag_area (m²) |
| **impulsive_spherical_params** | — | magnitude, azimuth, elevation (defaults for impulsive burn) |
| **impulsive_local_params** | — | element1, element2, element3 (defaults for Local Delta-V) |
| **T_PERIOD** | s | Orbital period from Kepler (ceil) |
| **DISTURBANCE_TORQUES** | N·m | 3-vector disturbance torque |
| **PROPORTIONAL_CONSTANT** | — | Magnetic control gain (e.g. 0.007) |
| **J_MATRIX** | kg·m² | 3×3 inertia matrix |
| **W_NOISE_SCALE**, **BTOT_NOISE_SCALE** | — | Noise scaling factors |
| **STEP** | s | Integration/propagation step size |
| **NUM_STEPS** | — | Number of steps (e.g. 3600) |
| **INTERVAL_DELAY** | ms | Animation frame delay |
| **W_NOISE**, **BTOT_NOISE** | — | Applied noise (from scale) |
| **SPECIFIC_TIME_STR** | — | Epoch string (e.g. "20 Jul 2020 12:00:00.000") |
| **SPECIFIC_TIME** | datetime (UTC) | Parsed epoch |
| **INITIAL_UT** | s | Seconds since 1970-01-01 UTC for SPECIFIC_TIME |
| **CUBE_SIZE**, **CUBE_ORIGIN** | mixed | CubeSat geometry for 3D visualization |
| **RESOLUTION_SCALE**, **RESOLUTION** | — | Figure/grid resolution |
| **KP_IDX** | — | Kp index for T89 (e.g. 6) |
| **CURRENT_TIME** | datetime | Set during run |
| **SEPERATION_TIME** | s | Time before attitude integration starts |
| **DEPLOYMENT_TIMER** | min | Minutes before full magnetic torque enabled |

---

## config.theme

**Role:** Theme and font setup for the GUI; project root path for assets.

| Symbol | Description |
|--------|-------------|
| **script_dir** | Project root (directory containing `config`). Used for `Roboto-Regular.ttf`, `dark-blue.json`. |
| **roboto_prop** | `matplotlib.font_manager.FontProperties` for Roboto (set by `setup_theme()`). |
| **setup_theme()** | Call once before creating main window: sets CustomTkinter dark mode and color theme; resolves font/theme paths (project first, then legacy fallback). |

---

## gui.ui_system

**Role:** Single source of truth for layout: spacing, panels, form rows, sections, actions. No arbitrary numbers in UI code.

| Symbol | Description |
|--------|-------------|
| **SPACE_1** … **SPACE_4** | Spacing scale (4, 8, 12, 16). Use only these. |
| **PAD**, **COL_GAP**, **ROW_GAP**, **SECTION_GAP** | Panel and section spacing |
| **BORDER_WIDTH**, **BORDER_COLOR**, **PANEL_BG**, **CANVAS_BG** | Panel/canvas appearance |
| **LABEL_COL_MINSIZE**, **ENTRY_MIN_WIDTH**, **ENTRY_COL_MAX**, **RIGHT_COL_ENTRY_WIDTH**, **MIDDLE_COL_ENTRY_WIDTH** | Form column widths |
| **FORM_ROW_PADX** | Horizontal gap between label and control |
| **SECTION_HEADER_PADY** | Section header vertical padding |
| **ACTION_BUTTON_WIDTH**, **ACTION_BUTTON_HEIGHT**, **ACTION_GAP** | Action button layout |
| **BOTTOM_BAR_ROW_HEIGHT**, **BOTTOM_BAR_PAD_V** | Bottom bar layout |
| **PREVIEW_ROW_MINSIZE**, **MAP_ROW_MINSIZE** | Minimum row sizes for preview/map |

---

## gui.common

**Role:** Shared fonts, colors, and window default sizes for all GUIs.

| Symbol | Description |
|--------|-------------|
| **FONT_FAMILY**, **FONT_FAMILY_FIXED** | Century Gothic, Fixedsys |
| **get_default_font()**, **get_default_font_small()**, **get_button_font()** | CTkFont instances (call after root exists) |
| **FIGURE_FACECOLOR**, **AXIS_GRID_COLOR**, **TEXT_COLOR**, **LEGEND_FRAME_*** | Matplotlib and CTk colors |
| **SECTION_HEADER_BG**, **SECTION_HEADER_HOVER** | Section header colors |
| **UI_SPACING**, **UI_PAD_SMALL** | From ui_system (SPACE_2, SPACE_1) |
| **SPACECRAFT_WINDOW_MIN_***, **SPACECRAFT_WINDOW_DEFAULT_*** | SpacecraftGUI window size |
| **MAGNETIC_WINDOW_MIN_*** | MagneticFieldGUI minimum size |
