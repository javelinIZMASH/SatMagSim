# GMAT API loader for SatMagSim (run from any folder).
# Configure GmatInstall to your GMAT top-level folder.
# See GMAT_R2025a/api/API_README.txt for setup (run BuildApiStartupFile.py once).

import sys
from os import path

def _get_short_path(long_path):
    """On Windows, return 8.3 short path (ASCII) for C++ APIs that may not handle Unicode."""
    if sys.platform != "win32":
        return long_path.replace("\\", "/")
    try:
        import ctypes
        from ctypes import wintypes
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        if ctypes.windll.kernel32.GetShortPathNameW(long_path, buf, len(buf)):
            return buf.value.replace("\\", "/")
    except Exception:
        pass
    return long_path.replace("\\", "/")

apistartup = "api_startup_file.txt"
# GMAT R2025a top-level folder (same machine as this project)
GmatInstall = path.normpath(r"C:\Users\balki\OneDrive\Masaüstü\spacehodrome\GMAT_R2025a")
GmatBinPath = path.join(GmatInstall, "bin")
Startup = path.join(GmatBinPath, apistartup)

if path.exists(Startup):
    sys.path.insert(1, GmatBinPath)
    import gmatpy as gmat
    startup_path = _get_short_path(Startup)
    gmat.Setup(startup_path)
else:
    raise FileNotFoundError(
        f"Cannot find {Startup}. Run GMAT api/BuildApiStartupFile.py once, "
        "and set GmatInstall in this file to your GMAT folder."
    )

def get_gmat_data_path(*parts):
    """Return absolute path under GMAT data folder (e.g. get_gmat_data_path('gravity','earth','EGM96.cof')).
    On Windows uses 8.3 short path so the C++ API receives ASCII."""
    p = path.join(GmatInstall, "data", *parts)
    return _get_short_path(p)

__all__ = ["gmat", "GmatInstall", "get_gmat_data_path"]
