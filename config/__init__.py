"""Configuration package: constants, theme, and paths.

Provides:
    - ``Constants``: Simulation, spacecraft, and GUI constants.
    - ``setup_theme``: Font and theme setup (call once before creating GUI).
    - ``script_dir``: Project root directory for resolving assets.

Pure configuration and theme setup; no GMAT or disk I/O on import.
"""

from config.constants import Constants
from config.theme import setup_theme, script_dir

__all__ = ["Constants", "setup_theme", "script_dir"]
