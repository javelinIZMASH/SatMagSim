"""Impulsive burn window: Local/Spherical Delta-V, Apply, Run, LoadScript, update Keplerian from file."""

import math
import os
import threading

import customtkinter as ctk

from config.constants import Constants
from gui.common import get_default_font, get_button_font
from load_gmat import gmat


class ImpulsiveBurnGUI:
    """GUI for impulsive burn parameters (Local or Spherical) and GMAT script run."""

    def __init__(self, root, spacecraft_gui_instance):
        self.spacecraft_gui = spacecraft_gui_instance

        ctk.set_appearance_mode("dark")
        root.minsize(480, 320)
        root.geometry("500x325")
        root.title("ImpulsiveBurn")
        root.resizable(True, True)

        self.center_window(root, 500, 325)
        root.lift()
        root.focus_force()

        coordinate_frame = ctk.CTkFrame(master=root)
        coordinate_frame.pack(pady=10, padx=10, fill="x")

        coordinate_label = ctk.CTkLabel(master=coordinate_frame, text="Coordinate System")
        coordinate_label.grid(row=0, column=0, padx=10, pady=5)

        self.coordinate_system = ctk.CTkComboBox(
            master=coordinate_frame, values=["Local", "Spherical"], command=self.update_labels
        )
        self.coordinate_system.grid(row=1, column=0, padx=10)
        self.coordinate_system.set("Local")

        origin_label = ctk.CTkLabel(master=coordinate_frame, text="Origin")
        origin_label.grid(row=0, column=1, padx=10, pady=5)
        origin_combo = ctk.CTkComboBox(master=coordinate_frame, values=["Earth"])
        origin_combo.grid(row=1, column=1, padx=10)

        axes_label = ctk.CTkLabel(master=coordinate_frame, text="Axes")
        axes_label.grid(row=0, column=2, padx=10, pady=5)
        axes_combo = ctk.CTkComboBox(master=coordinate_frame, values=["VNB"])
        axes_combo.grid(row=1, column=2, padx=10)

        deltav_frame = ctk.CTkFrame(master=root)
        deltav_frame.pack(pady=10, padx=10, fill="x")

        deltav_label = ctk.CTkLabel(master=deltav_frame, text="Delta-V Vector")
        deltav_label.grid(row=0, column=0, padx=10, pady=5)

        self.element1_label = ctk.CTkLabel(master=deltav_frame, text="Element 1 (m/s)")
        self.element1_label.grid(row=1, column=0, padx=10)
        self.element1_entry = ctk.CTkEntry(master=deltav_frame)
        self.element1_entry.insert(0, Constants.impulsive_local_params["element1"])
        self.element1_entry.grid(row=1, column=1, padx=10)

        self.element2_label = ctk.CTkLabel(master=deltav_frame, text="Element 2 (m/s)")
        self.element2_label.grid(row=2, column=0, padx=10)
        self.element2_entry = ctk.CTkEntry(master=deltav_frame)
        self.element2_entry.insert(0, Constants.impulsive_local_params["element2"])
        self.element2_entry.grid(row=2, column=1, padx=10)

        self.element3_label = ctk.CTkLabel(master=deltav_frame, text="Element 3 (m/s)")
        self.element3_label.grid(row=3, column=0, padx=10)
        self.element3_entry = ctk.CTkEntry(master=deltav_frame)
        self.element3_entry.insert(0, Constants.impulsive_local_params["element3"])
        self.element3_entry.grid(row=3, column=1, padx=10)

        run_button = ctk.CTkButton(master=root, text="Run", command=self.impulsive_start_simulation_thread)
        run_button.pack(side="left", padx=10, pady=10)
        apply_button = ctk.CTkButton(master=root, text="Apply", command=self.impulsive_apply_values)
        apply_button.pack(side="left", padx=10, pady=10)
        cancel_button = ctk.CTkButton(master=root, text="Cancel", command=root.destroy)
        cancel_button.pack(side="left", padx=10, pady=10)

    def update_labels(self, choice):
        """Update labels and entry placeholders based on the selected coordinate system."""
        if choice == "Spherical":
            self.element1_label.configure(text="Magnitude (m/s)")
            self.element2_label.configure(text="Azimuth (deg)")
            self.element3_label.configure(text="Elevation (deg)")
            self.element1_entry.delete(0, "end")
            self.element1_entry.insert(0, Constants.impulsive_spherical_params["magnitude"])
            self.element2_entry.delete(0, "end")
            self.element2_entry.insert(0, Constants.impulsive_spherical_params["azimuth"])
            self.element3_entry.delete(0, "end")
            self.element3_entry.insert(0, Constants.impulsive_spherical_params["elevation"])
        else:
            self.element1_label.configure(text="Element 1 (m/s)")
            self.element2_label.configure(text="Element 2 (m/s)")
            self.element3_label.configure(text="Element 3 (m/s)")
            self.element1_entry.delete(0, "end")
            self.element1_entry.insert(0, Constants.impulsive_local_params["element1"])
            self.element2_entry.delete(0, "end")
            self.element2_entry.insert(0, Constants.impulsive_local_params["element2"])
            self.element3_entry.delete(0, "end")
            self.element3_entry.insert(0, Constants.impulsive_local_params["element3"])

    def impulsive_apply_values(self):
        """Apply GUI values to Constants (Spherical or Local) based on coordinate system."""
        try:
            coord_system = self.coordinate_system.get()
            if coord_system == "Spherical":
                magnitude = float(self.element1_entry.get())
                azimuth = float(self.element2_entry.get())
                elevation = float(self.element3_entry.get())
                if not (0 <= elevation <= 180):
                    raise ValueError("Elevation (polar angle) must be between 0 and 180 degrees.")
                if not (0 <= azimuth <= 360):
                    raise ValueError("Azimuth must be between 0 and 360 degrees.")
                Constants.impulsive_spherical_params["magnitude"] = magnitude
                Constants.impulsive_spherical_params["azimuth"] = azimuth
                Constants.impulsive_spherical_params["elevation"] = elevation
                print("Values applied to Constants (Spherical):")
                print("Spherical:", Constants.impulsive_spherical_params)
            else:
                element1 = float(self.element1_entry.get())
                element2 = float(self.element2_entry.get())
                element3 = float(self.element3_entry.get())
                Constants.impulsive_local_params["element1"] = element1
                Constants.impulsive_local_params["element2"] = element2
                Constants.impulsive_local_params["element3"] = element3
                print("Values applied to Constants (Local):")
                print("Local:", Constants.impulsive_local_params)
        except ValueError as e:
            print(f"Error: {e}")

    def update_satellite_params_from_file(self):
        """Read last line of initial_Kepler.txt and update Constants.SATELLITE_PARAMS and main GUI."""
        file_path = "C:\\Users\\GumushAerospace\\Desktop\\GMAT\\output\\initial_Kepler.txt"
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        with open(file_path, "r") as file:
            lines = file.readlines()
        if not lines:
            print(f"File is empty: {file_path}")
            return
        last_line = lines[-1].strip().split()
        if len(last_line) < 6:
            print("Unexpected data format in the file.")
            return
        try:
            Constants.SATELLITE_PARAMS["sma"] = float(last_line[0])
            Constants.SATELLITE_PARAMS["ecc"] = float(last_line[1])
            Constants.SATELLITE_PARAMS["inc"] = float(last_line[2])
            Constants.SATELLITE_PARAMS["aop"] = float(last_line[3])
            Constants.SATELLITE_PARAMS["ra"] = float(last_line[4])
            Constants.SATELLITE_PARAMS["ta"] = float(last_line[5])
            print("SATELLITE_PARAMS updated from the file:")
            print(Constants.SATELLITE_PARAMS)
            self.spacecraft_gui.update_keplerian_elements()
        except ValueError as e:
            print(f"Error parsing data from file: {e}")

    def impulsive_start_simulation_thread(self):
        self.simulation_thread = threading.Thread(target=self.impulsive_run_simulation)
        self.simulation_thread.start()

    def impulsive_run_simulation(self):
        """Run GMAT script with applied impulsive burn and update satellite params from file."""
        coord_system = self.coordinate_system.get()
        if coord_system == "Spherical":
            magnitude_kms = Constants.impulsive_spherical_params["magnitude"] / 1000
            azimuth = Constants.impulsive_spherical_params["azimuth"]
            elevation = Constants.impulsive_spherical_params["elevation"]
            element1_kms = magnitude_kms * math.cos(math.radians(elevation)) * math.cos(math.radians(azimuth))
            element2_kms = magnitude_kms * math.sin(math.radians(elevation)) * math.sin(math.radians(azimuth))
            element3_kms = magnitude_kms * math.cos(math.radians(elevation))
        else:
            element1_kms = Constants.impulsive_local_params["element1"] / 1000
            element2_kms = Constants.impulsive_local_params["element2"] / 1000
            element3_kms = Constants.impulsive_local_params["element3"] / 1000

        gmat.LoadScript("C:\\Users\\GumushAerospace\\Desktop\\GMAT\\api\\Ex_ForceModels_Full.script")
        RocketTime = gmat.GetObject("RocketTime")
        RocketTime.SetField("Value", Constants.SEPERATION_TIME)
        Thruster = gmat.GetObject("DefaultIB")
        Thruster.SetField("Element1", element1_kms)
        Thruster.SetField("Element2", element2_kms)
        Thruster.SetField("Element3", element3_kms)
        gmat.RunScript()

        print(
            f"Simulation started with Element1={element1_kms} km/s, "
            f"Element2={element2_kms} km/s, Element3={element3_kms} km/s"
        )
        self.update_satellite_params_from_file()

    def center_window(self, root, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
