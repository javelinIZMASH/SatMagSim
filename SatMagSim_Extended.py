# SatMagSim Extended - legacy single-file entry point.
# Application is implemented in modular packages: config, utils, core, gui.
# Run: python SatMagSim_Extended.py   or   python main.py

from config.theme import setup_theme
from gui import SpacecraftGUI

setup_theme()

if __name__ == "__main__":
    app = SpacecraftGUI()
    app.mainloop()
