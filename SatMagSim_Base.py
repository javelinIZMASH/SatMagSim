import math
import numpy as np
import pymap3d
import gc
import datetime
import time
import threading
import matplotlib.pyplot as plt
import serial
import serial.tools.list_ports
from tkinter import ttk  # Import Combobox from ttk
from geopack import geopack, t89
from spacepy import coordinates as coord
from spacepy.time import Ticktock
from scipy.integrate import solve_ivp
from matplotlib.animation import FuncAnimation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import tkinter as tk
from customtkinter import CTk, CTkLabel, CTkProgressBar, CTkFrame, CTkButton, CTkEntry, CTkFont, set_appearance_mode, set_default_color_theme, CTkCheckBox
import ctypes
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageTk
import os
# Load GMAT into memory
from load_gmat import *
# Font and theme: prefer project folder, then fallback to default
_script_dir = os.path.dirname(os.path.abspath(__file__))
roboto_font_path = os.path.join(_script_dir, "Roboto-Regular.ttf")
if not os.path.isfile(roboto_font_path):
    roboto_font_path = "C:/Users/GumushAerospace/Desktop/taurus/Roboto-Regular.ttf"
theme_path = os.path.join(_script_dir, "dark-blue.json")
if not os.path.isfile(theme_path):
    theme_path = "C:/Users/GumushAerospace/Desktop/taurus/dark-blue.json"
set_appearance_mode("dark")
set_default_color_theme(theme_path if os.path.isfile(theme_path) else "dark-blue")
roboto_prop = FontProperties(fname=roboto_font_path) if os.path.isfile(roboto_font_path) else FontProperties()

class Constants:
    # Gravitational constant (GM) for Earth (WGS84 model)
    MU = 398600.4418  # [km^3/s^2]
    
    # True anomalies (in degrees)
    TRUE_ANOMALIES = [270]  # [degrees]
    
    ALTITUDE = 500
    
    R_RADIUS = 6378.1363
    
    q = np.array([0, 0, 0, 1])
    w = np.array([0.3, 0.4, 0.5]) 

    # Satellite parameters to be input later
    SATELLITE_PARAMS = {
        "sma": 6878.1363,
        "ecc": 9.4080e-04,
        "inc": 97.8,  # [degrees]
        "ra": 102,  # [degrees]
        "aop": 0,  # [degrees]
        "ta": 270,
        "srp_area": 0.01,  # [m^2]
        "cr": 1.8,
        "cd": 2.2,
        "dry_mass": 0.8,  # [kg]
        "drag_area": 0.01  # [m^2]
    }
    # Orbital period (in seconds)
    T_PERIOD = math.ceil((2 * math.pi * math.sqrt(SATELLITE_PARAMS["sma"]**3 / MU)))
    # Force model constants to be input later
    DISTURBANCE_TORQUES = np.array([3e-07, 3e-07, 3e-07])  # To be input later [Nm]

    # Proportional constant for control law to be input later
    PROPORTIONAL_CONSTANT = 0.007  # To be input later

    # # Inertia matrix (J) to be input later
    # J_MATRIX = np.array([
    #     [0.000826, 0.000001, 0.0000000619],
    #     [0.000001, 0.000425, -0.000002],
    #     [0.0000000619, -0.000002, 0.0012]
    # ])  # To be input later
    
    # Inertia matrix (J) to be input later
    J_MATRIX = np.array([
        [0.000826, 0, 0],
        [0, 0.000425,0 ],
        [0, 0, 0.0012]
    ])  # To be input later

    # Noise constants to be input later for scaling factors
    W_NOISE_SCALE = 1e-5  # Scaling factor for W_NOISE [rad/s]
    BTOT_NOISE_SCALE = 100  # Scaling factor for BTOT_NOISE [nT]
    # Time constants
    STEP = 1  # [seconds]
    NUM_STEPS = 3600
    INTERVAL_DELAY = 100
    # The random noise generation with the scaling factors applied after input
    W_NOISE = W_NOISE_SCALE  # Angular velocity noise scaled by input
    BTOT_NOISE = BTOT_NOISE_SCALE  # Magnetic field noise scaled by input

      # SPECIFIC_TIME string format to be input and converted to datetime
    SPECIFIC_TIME_STR = "20 Jul 2020 12:00:00.000"  # Example input string

    # Convert the input date string to a datetime object in UTC
    SPECIFIC_TIME = datetime.datetime.strptime(SPECIFIC_TIME_STR, "%d %b %Y %H:%M:%S.%f")
    SPECIFIC_TIME = SPECIFIC_TIME.replace(tzinfo=datetime.timezone.utc)

    # Define the reference time (epoch)
    T0 = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

    # Calculate INITIAL_UT
    INITIAL_UT = (SPECIFIC_TIME - T0).total_seconds()
    
    # CubeSat dimensions
    CUBE_SIZE = [0.6936, 0.6936, 0.1942]
    
    CUBE_ORIGIN = np.array([[-0.6936 / 2, -0.6936 / 2, -0.1942 / 2],
                            [0.6936 / 2, -0.6936 / 2, -0.1942 / 2],
                            [0.6936 / 2, 0.6936 / 2, -0.1942 / 2],
                            [-0.6936 / 2, 0.6936 / 2, -0.1942 / 2],
                            [-0.6936 / 2, -0.6936 / 2, 0.1942 / 2],
                            [0.6936 / 2, -0.6936 / 2, 0.1942 / 2],
                            [0.6936 / 2, 0.6936 / 2, 0.1942 / 2],
                            [-0.6936 / 2, 0.6936 / 2, 0.1942 / 2]])
    
    
    RESOLUTION_SCALE = 10
    RESOLUTION = RESOLUTION_SCALE
    KP_IDX = 6
    CURRENT_TIME = SPECIFIC_TIME
    
# Define the main GUI class
class SpacecraftGUI(CTk):
    def __init__(self):
        super().__init__()
        
        # Calculate ps and ticks once
        self.ps = geopack.recalc(Constants.INITIAL_UT)
        self.ticks = Ticktock(Constants.SPECIFIC_TIME, 'UTC')
        self.KP_IDX = Constants.KP_IDX
        
        self.is_calculate_button_pressed = False

        # Pencereyi kapatma olayı için 'close_window' fonksiyonunu bağla
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        # Window settings
        self.title("Spacecraft Parameters")
        self.geometry("1470x735")

        # Center the window on the screen
        self.update_idletasks()
        width = 1470
        height = 735
        x = (self.winfo_screenwidth() // 2) - (width // 2) - 15
        y = (self.winfo_screenheight() // 2) - (height // 2) - 50
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Disable resizing
        self.resizable(False, False)

        # Grid yapılandırması
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Font settings
        self.custom_font = CTkFont(family='Century Gothic', size=12)
        self.custom_font_fixedsys = CTkFont(family='Fixedsys', size=12)

        # Create main frames for left, right and third sections
        self.left_frame = CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=(10, 20), pady=10, sticky="nsew")

        self.right_frame = CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=(20, 20), pady=10, sticky="nsew")

        self.third_frame = CTkFrame(self)
        self.third_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Populate sections
        self.create_time_coord_system_frame(self.left_frame)
        self.create_keplerian_elements_frame(self.left_frame)
        self.create_physical_properties_frame(self.left_frame)
        self.create_aerodynamic_properties_frame(self.left_frame)
        self.create_spacecraft_constants_frame(self.right_frame)
        self.create_simulation_parameters_frame(self.right_frame)
        # Angular Rate (rad/s) bölümü Resolution butonunun altına ekleniyor
        self.add_angular_rate_section(self.right_frame)

        # Populate the third frame
        self.canvas1 = self.create_canvas(self.third_frame, row=4, column=0)
        self.canvas2 = self.create_canvas(self.third_frame, row=0, column=0)
                
        self.add_quaternion_section(self.third_frame)
        self.add_euler_angles_section(self.third_frame)
        self.add_altitude_section(self.third_frame)

        # Add the progress bar at the bottom across all frames
        self.create_progress_bar()
        self.create_control_buttons()
        self.bind_euler_entries()
        self.bind_quaternion_entries()
        
        # Load and display the image on both canvases
        self.display_logo(self.canvas1)
        self.display_logo(self.canvas2)
                
        # Method called when the calculate button is pressed
    def on_calculate_button_press(self):
        self.is_calculate_button_pressed = True
        # Any other actions when the button is pressed       
        
    def display_logo(self, canvas):
        image_path = os.path.join(_script_dir, "gumushlogo.png")
        if not os.path.isfile(image_path):
            image_path = "C:/Users/GumushAerospace/Desktop/taurus/gumushlogo.png"
        if not os.path.isfile(image_path):
            return
        self.logo_image = Image.open(image_path)
        self.logo_image = self.logo_image.resize((128, 115), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(self.logo_image)
        x = 400
        y = 165
        canvas.create_image(x, y, anchor='center', image=self.logo_photo)
        canvas.image = self.logo_photo
      
    def INITGUI_geodetic_to_eci(self, lat, lon, altitude):
        """Convert geodetic to ECI coordinates."""
        return pymap3d.geodetic2eci(lat, lon, altitude * 1e3, Constants.SPECIFIC_TIME, deg=True)

    def INITGUI_calc_geomagnetic_fields(self, r):
        """Calculate internal, external, and total geomagnetic fields in GSM."""
        # Convert ECI to GSM coordinates
        R_ECI = coord.Coords([r[0], r[1], r[2]], 'ECI2000', 'car')
        R_ECI.ticks = self.ticks
        R_GSM = R_ECI.convert('GSM', 'car').data.flatten()

        xgsm, ygsm, zgsm = [R_GSM[0] / 6371.2, R_GSM[1] / 6371.2, R_GSM[2] / 6371.2]

        # Internal geomagnetic field (IGRF)
        bint_xgsm, bint_ygsm, bint_zgsm = geopack.igrf_gsm(xgsm, ygsm, zgsm)

        # External geomagnetic field (T89)
        bext_xgsm, bext_ygsm, bext_zgsm = t89.t89(self.KP_IDX + 1, self.ps, xgsm, ygsm, zgsm)

        # Total geomagnetic field in GSM
        bxgsm, bygsm, bzgsm = [
            bint_xgsm + bext_xgsm,
            bint_ygsm + bext_ygsm,
            bint_zgsm + bext_zgsm
        ]

        Btot_GSM = coord.Coords([bxgsm, bygsm, bzgsm], 'GSM', 'car')
        Btot_GSM.ticks = self.ticks
        return Btot_GSM.convert('GEO', 'car').data
    
    def INITGUI_run_simulation(self):
        # Altitude bilgilerini iş parçacığını başlatmadan önce alın
        self.altitude_checked = self.altitude_check.get()
        self.altitude_value = float(self.altitude_entry.get()) if self.altitude_checked else float(self.semi_major_axis_entry.get()) - 6378.1363
        
        # Thread başlatılır
        self.run_thread = threading.Thread(target=self.run_calculations)
        self.run_thread.start()

    def start_simulation_thread(self):
        # Simülasyonun GUI donmadan çalışması için bir iş parçacığı başlatıyoruz
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.start()
        
    def run_simulation(self):
        # Simülasyon parametreleri
        time_ = 0.0
        step = Constants.STEP
        num_steps = Constants.NUM_STEPS
        specific_time = Constants.SPECIFIC_TIME
        initial_ut = Constants.INITIAL_UT
        kp_index = Constants.KP_IDX
    
        # Progress bar için parametreler
        total_steps = num_steps
        current_step = 0
    
        # Başlangıç zamanı
        start_time_sim = time.time()
    
        # Simülasyon döngüsü
        for x in range(num_steps):
            gator.Step(step)
            time_ += step
            current_time = specific_time + datetime.timedelta(seconds=time_)
            
            # SatelliteSimulator sınıfı örneği oluşturuluyor
            simulator = SatelliteSimulator(
                J=Constants.J_MATRIX,
                k=Constants.PROPORTIONAL_CONSTANT,
                N=np.random.randn(1) * Constants.DISTURBANCE_TORQUES,
                w_noise=np.random.randn(3) * Constants.W_NOISE,
                Btot_noise=np.random.randn(3) * Constants.BTOT_NOISE
            )

            # Geomagnetic field calculations at each time step
            simulator.calculate_magnetic_fields(
                satellites=satellites,
                initial_ut=initial_ut,
                current_time=current_time,
                kp_index=kp_index,
                x=x,
                num_steps=num_steps,
                step=step,
                data_dyn_kin=data_dyn_kin,
                data_PV=data_PV,
                data_geodetic=data_geodetic,
                data_magnetic=data_magnetic
            )
            initial_ut += 1
    
            # Progress bar update
            current_step += 1
            progress_value = (current_step / total_steps) * 100
            self.after(0, self.update_progress, progress_value, current_step, total_steps)  # Ana iş parçacığında çalıştırılır
    
            # Optionally force GUI to update if needed
            self.update_idletasks()  # GUI'yi zorla güncelle
    
        # Simülasyon sonu
        end_time_sim = time.time()
        total_sim_time = end_time_sim - start_time_sim
        print(f"Total Sim. Time: {total_sim_time:.1f} saniye")
    
        simulator.timing_dict["Total simulation time"] = end_time_sim - start_time_sim
    
        # Timing sonuçlarının ortalamasını göster
        average_timings = simulator.calculate_average_timings()
        print("Average timings:", average_timings)
        
        self.progress_file_label.configure(text=f"{total_sim_time:.1f}sec")
        
        self.next_button.configure(state="normal", fg_color="green", hover_color="darkgreen")
           
        # Simülasyon sonuçları geri döndürülüyor
        return simulator
       
    # def start_gui_thread(self):
    #     # Simülasyonun GUI donmadan çalışması için bir iş parçacığı başlatıyoruz
    #     self.simulation_thread = threading.Thread(target=self.start_gui)
    #     self.simulation_thread.start()

    def start_gui(self):
        # GUI penceresi oluşturma
        set_appearance_mode("dark")
        set_default_color_theme("C:/Users/GumushAerospace/Desktop/taurus/dark-blue.json")
        
        root = CTk()
        root.title("Magnetic Field Visualization")
        ctypes.windll.gdi32.AddFontResourceW(roboto_font_path)
        root.state('zoomed')
        root.resizable(False, False)
        # `MagneticFieldData` sınıfından `data` örneğini oluşturun
        data = MagneticFieldData(data_geodetic, data_magnetic, data_PV, data_dyn_kin)
              
        app2 = MagneticFieldGUI(root, data)
        
        app2.draw_figures()  # Figürleri çiz
        root.mainloop()  # GUI döngüsünü başlat      
    
    def run_calculations(self):
        latitudes_2d = np.linspace(-89, 90, Constants.RESOLUTION)  # Latitude values
        longitudes_2d = np.linspace(-180, 179, Constants.RESOLUTION) 
    
        altitude_value = self.altitude_value  # Tkinter widget'ından alınmış değeri kullan
        Constants.ALTITUDE = self.altitude_value
        # Run the simulation and calculate the geomagnetic field for each latitude and longitude
        eci_coords = np.zeros((3, len(latitudes_2d), len(longitudes_2d)))
        Btot_ECEF_data = np.zeros((3, len(latitudes_2d), len(longitudes_2d)))
    
        total_steps = len(latitudes_2d) * len(longitudes_2d)  # Total number of steps for progress bar
        current_step = 0  # Track the current step for progress
    
        for i, lat in enumerate(latitudes_2d):
            for j, lon in enumerate(longitudes_2d):
                # Geodetic to ECI conversion
                eci_coords[:, i, j] = self.INITGUI_geodetic_to_eci(lat, lon, altitude_value)
                r = eci_coords[:, i, j] * 1e-3
    
                # Calculate total geomagnetic field
                Btot_ECEF_data[:, i, j] = self.INITGUI_calc_geomagnetic_fields(r)
    
                # Progress bar update
                current_step += 1
                progress_value = (current_step / total_steps) * 100
                self.after(0, self.update_progress, progress_value, current_step, total_steps)  # Ana iş parçacığında çalıştırılır
    
                # Optionally force GUI to update if needed
                self.update_idletasks()  # GUI'yi zorla güncelle
    
        self.Btot_magnitude = np.linalg.norm(Btot_ECEF_data, axis=0)
        self.Btot_magnitude = self.Btot_magnitude[np.newaxis, :, :]
    
        # Save Btot_magnitude to a .npy file with altitude in the filename
        altitude_value_int = int(altitude_value)
        npy_filename = f'Btot_magnitude_altitude_{altitude_value_int}.npy'
        np.save(npy_filename, self.Btot_magnitude)
        
        self.progress_file_label.configure(text=f"Saved: {npy_filename}")
    
        # Once the calculations are done, create the figure
        self.create_fig1()  # This will generate the figure with the calculated data

    def q_to_DCM(self,q):
            q1, q2, q3, q4 = q
            
            q_DCM = np.array([[q4**2 + q1**2 - q2**2 - q3**2, 2*(q1*q2 + q3*q4), 2*(q1*q3 - q2*q4)],
                          [2*(q1*q2 - q3*q4), q4**2 - q1**2 + q2**2 - q3**2, 2*(q2*q3 + q1*q4)],
                          [2*(q1*q3 + q2*q4), 2*(q2*q3 - q1*q4), q4**2 - q1**2 - q2**2 + q3**2]])
    
            return q_DCM

    def euler_from_quaternion(self,q):
            """
            Convert a quaternion into euler angles (roll, pitch, yaw)
            """
            x, y, z, w = q
            t0 = +2.0 * (w * x + y * z)
            t1 = +1.0 - 2.0 * (x * x + y * y)
            roll_x = np.arctan2(t0, t1)
    
            t2 = +2.0 * (w * y - z * x)
            t2 = np.clip(t2, -1.0, 1.0)
            pitch_y = np.arcsin(t2)
    
            t3 = +2.0 * (w * z + x * y)
            t4 = +1.0 - 2.0 * (y * y + z * z)
            yaw_z = np.arctan2(t3, t4)
    
            return roll_x, pitch_y, yaw_z  # in radians
    
    def get_quaternion_from_euler(self,roll, pitch, yaw):
      """
      Convert an Euler angle to a quaternion.
       
      Input
        :param roll: The roll (rotation around x-axis) angle in degree.
        :param pitch: The pitch (rotation around y-axis) angle in degree.
        :param yaw: The yaw (rotation around z-axis) angle in degree.
     
      Output
        :return qx, qy, qz, qw: The orientation in quaternion [x,y,z,w] format
      """
      roll = roll * math.pi / 180
      pitch = pitch * math.pi / 180
      yaw = yaw * math.pi / 180
      qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
      qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
      qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
      qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
     
      return qx, qy, qz, qw

    def update_preview(self):
        try:
            # Get quaternion values from the entries
            qx = float(self.q_entries[0].get())
            qy = float(self.q_entries[1].get())
            qz = float(self.q_entries[2].get())
            qw = float(self.q_entries[3].get())
    
            # Get Euler angles from the entries to display in the figure
            roll = float(self.euler_entries[0].get())
            pitch = float(self.euler_entries[1].get())
            yaw = float(self.euler_entries[2].get())
    
            # Calculate the DCM using the quaternion
            q = [qx, qy, qz, qw]
            dcm = self.q_to_DCM(q)
    
            # Rotate the cube using the DCM
            vertices_rotated = self.rotate_cube(Constants.CUBE_ORIGIN, dcm)
    
            # Redraw the cube with the new orientation in canvas2 (fig2)
            fig2, ax2 = self.create_fig2()  # Create a new figure and 3D axes
            self.create_cube(ax2, vertices_rotated)  # Draw the rotated cube
    
            euler_text = f"(Roll: {roll:.2f}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f})"
            ax2.text2D(0.5, 0.95, euler_text, transform=ax2.transAxes, fontsize=8, color="white", fontweight="bold", ha='center')

            # Clear any existing content in canvas2 before adding new content
            for widget in self.canvas2.winfo_children():
                widget.destroy()
    
            # Link the figure to the canvas and redraw it
            self.canvas_fig2 = FigureCanvasTkAgg(fig2, self.canvas2)  # Attach the figure to the canvas
    
            # Set the figure to fully occupy the canvas, using place()
            self.canvas_fig2.get_tk_widget().place(relx=0, rely=0, relwidth=1, relheight=1)  
            self.canvas_fig2.draw()  # Redraw the figure on the canvas
    
        except ValueError as e:
            # Handle any errors (e.g., invalid input)
            self.progress_file_label.configure(text=f"Error: {str(e)}")

    def update_quaternion_from_euler(self):
        try:
            # Girilen Euler açılarını al
            roll = self.euler_entries[0].get()
            pitch = self.euler_entries[1].get()
            yaw = self.euler_entries[2].get()
    
            # Eğer herhangi bir giriş boşsa, Preview butonunu devre dışı bırak ve hata mesajını temizle
            if roll == "" or pitch == "" or yaw == "":
                self.progress_file_label.configure(text="")
                self.preview_button.configure(state="disabled", fg_color="red", hover_color="darkred")  # Kırmızıya dön ve devre dışı yap
                return
    
            # Giriş değerlerini float'a çevir
            roll = float(roll)
            pitch = float(pitch)
            yaw = float(yaw)
    
            # Euler açıları -180 ile +180 derece arasında olmalı
            if not (-180 <= roll <= 180):
                raise ValueError("Euler Angles must be between -180 and +180 degrees")
            else:
                self.progress_file_label.configure(text="")  # Eğer hata yoksa mesajı sil
    
            if not (-180 <= pitch <= 180):
                raise ValueError("Euler Angles must be between -180 and +180 degrees")
            else:
                self.progress_file_label.configure(text="")  # Eğer hata yoksa mesajı sil
    
            if not (-180 <= yaw <= 180):
                raise ValueError("Euler Angles must be between -180 and +180 degrees")
            else:
                self.progress_file_label.configure(text="")  # Eğer hata yoksa mesajı sil
    
            # Eğer tüm değerler geçerliyse, quaternion'ları hesapla
            qx, qy, qz, qw = self.get_quaternion_from_euler(roll, pitch, yaw)
    
            # Quaternion entry'lerini güncelle
            for entry, value in zip(self.q_entries, [qx, qy, qz, qw]):
                entry.configure(state="normal", fg_color="grey", text_color="white")
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.6f}")
                entry.configure(state="disabled")
    
            # Quaternion'lar başarılı şekilde hesaplandıysa Preview butonunu aktif et ve rengini yeşile çevir
            self.preview_button.configure(state="normal", fg_color="green", hover_color="darkgreen")
    
        except ValueError as e:
            # Hata mesajını göster ve Preview butonunu devre dışı bırak
            self.progress_file_label.configure(text=f"Error: {str(e)}")
            self.preview_button.configure(state="disabled", fg_color="red", hover_color="darkred")  # Hata durumunda yine kırmızı yap
    
    def bind_euler_entries(self):
        """Euler entry'lerine her değişiklikte update işlemi ekler"""
        for entry in self.euler_entries:
            entry.bind("<KeyRelease>", lambda event: self.update_quaternion_from_euler())
          
    def update_euler_from_quaternion(self):
        try:
            # Quaternion değerlerini al
            qx = self.q_entries[0].get()
            qy = self.q_entries[1].get()
            qz = self.q_entries[2].get()
            qw = self.q_entries[3].get()
            
            # Eğer herhangi bir giriş boşsa, işlemi yapma
            if qx == "" or qy == "" or qz == "" or qw == "":
                return
    
            # Quaternion değerlerini float'a çevir
            qx = float(qx)
            qy = float(qy)
            qz = float(qz)
            qw = float(qw)
    
            # Quaternion'ların normu 1 olmalı
            quaternion_norm = np.sqrt(qx**2 + qy**2 + qz**2 + qw**2)
            if not np.isclose(quaternion_norm, 1):
                raise ValueError("Quaternion norm must be 1")
                
            else:
                self.progress_file_label.configure(text="")
    
            q = [qx, qy, qz, qw]
            # Euler açılarını quaternion'dan dönüştür
            roll, pitch, yaw = self.euler_from_quaternion(q)
    
            # Euler entry'lerini güncelle (derece cinsine çevir)
            for entry, value in zip(self.euler_entries, [roll, pitch, yaw]):
                entry.configure(state="normal", fg_color="grey", text_color="white")
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.2f}")  # Radyanı dereceye çeviriyoruz
                entry.configure(state="disabled")
    
            # Eğer başarılıysa, progress_file_label temizle
            self.progress_file_label.configure(text="")
    
        except ValueError as e:
            # Hata mesajını göster
            self.progress_file_label.configure(text=f"Error: {str(e)}")
            
    def create_fig2(self):
        fig2 = Figure(figsize=(6.5, 3.5), facecolor='#2B2B2B')
        ax2 = fig2.add_subplot(111, projection='3d')
        self.setup_3d_axes(ax2)
        ax2.set_title('Normalized Vectors', fontsize=10, color='#FFFFFF', fontproperties=roboto_prop)
        return fig2, ax2

    def setup_3d_axes(self, ax):
        matrix_green = '#03A062'
        ax.set_facecolor('#2B2B2B')
        ax.xaxis.pane.set_facecolor('#2B2B2B')
        ax.yaxis.pane.set_facecolor('#2B2B2B')
        ax.zaxis.pane.set_facecolor('#2B2B2B')
        ax.xaxis.pane.set_edgecolor('white')
        ax.yaxis.pane.set_edgecolor('white')
        ax.zaxis.pane.set_edgecolor('white')
        ax.grid(True, color=matrix_green)
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.tick_params(colors='white', labelsize=10, width=2)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.zaxis.label.set_color('white')
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])
        ax.set_xticks(np.arange(-1, 1))
        ax.set_yticks(np.arange(-1, 1))
        ax.set_zticks(np.arange(-1, 1))
        ax.set_xlabel('X', labelpad=6, fontsize=8, fontweight='bold', fontproperties=roboto_prop)
        ax.set_ylabel('Y', labelpad=6, fontsize=8, fontweight='bold', fontproperties=roboto_prop)
        ax.set_zlabel('Z', labelpad=6, fontsize=8, fontweight='bold', fontproperties=roboto_prop)
      
    def rotate_cube(self, vertices, dcm):
        return dcm @ vertices.T

    def create_cube(self, ax, vertices):
        vertices = vertices.T
        faces = [[vertices[j] for j in [0, 1, 2, 3]], 
                 [vertices[j] for j in [4, 5, 6, 7]],
                 [vertices[j] for j in [0, 3, 7, 4]], 
                 [vertices[j] for j in [1, 2, 6, 5]],
                 [vertices[j] for j in [0, 1, 5, 4]], 
                 [vertices[j] for j in [2, 3, 7, 6]]]
        
        face_colors = ['cyan', 'magenta', 'yellow', 'green', 'blue', 'red']  # Her yüzeye farklı renk
    
        collection = Poly3DCollection(faces, facecolors=face_colors, linewidths=1, edgecolors='r')
        ax.add_collection3d(collection)
        return collection
    
    def bind_quaternion_entries(self):
        """Quaternion entry'lerine her değişiklikte update işlemi ekler"""
        for entry in self.q_entries:
            entry.bind("<KeyRelease>", lambda event: self.update_euler_from_quaternion())

    def add_altitude_section(self, parent):
        altitude_frame = CTkFrame(parent)
        altitude_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=(0, 0), sticky="ew")  # Yeni satır ayarlandı ve 3 sütun boyunca uzatıldı
    
        # Ana GUI'nin satır ve sütun genişliğini kontrol et
        parent.grid_rowconfigure(5, weight=0)  # Satır yüksekliği kontrol edilir
        parent.grid_columnconfigure(0, weight=1)  # Sütun genişliği kontrol edilir
    
        # Altitude başlığı sola hizalanır
        CTkButton(altitude_frame, text="Altitude (km)", font=self.custom_font).grid(row=0, column=0, pady=(0, 5), sticky="w")
    
        # Altitude entry
        self.altitude_entry = CTkEntry(altitude_frame, width=100, font=self.custom_font, state="disabled")  # Başlangıçta disabled
        self.altitude_entry.grid(row=0, column=1, padx=5, pady=(0, 5), sticky="ew")
    
        # Altitude CheckBox en sağa hizalanır
        self.altitude_check = tk.BooleanVar()
        checkbox = CTkCheckBox(altitude_frame, text="", variable=self.altitude_check, onvalue=True, offvalue=False, command=self.toggle_altitude)
        checkbox.grid(row=0, column=2, padx=(10, 5), pady=(0, 5), sticky="e")
    
        # Calculate button en sağa hizalanır (Yeşil renkte)
        self.calculate_button = CTkButton(altitude_frame,font = self.custom_font_fixedsys, text="Calculate", width=100, height=20, fg_color="green", hover_color="darkgreen", command = self.INITGUI_run_simulation)
        self.calculate_button.grid(row=0, column=3, padx=(125, 5), pady=(0, 5), sticky="e")  # Buton en sağda olacak şekilde hizalandı
           
    def add_quaternion_section(self, parent):
        quaternion_frame = CTkFrame(parent)
        quaternion_frame.grid(row=1, column=0, padx=10, pady=(0, 0), sticky="w")
        
        # Satır ve sütun genişliği kontrolü
        parent.grid_rowconfigure(1, weight=0)  # Satır yüksekliği kontrol edilir
        parent.grid_columnconfigure(0, weight=1)  # Sütun genişliği kontrol edilir
    
        CTkButton(quaternion_frame, text="Quaternion", font=self.custom_font).grid(row=0, column=0, pady=(0, 5), sticky="w")
    
        # Quaternion entry'leri
        self.q_entries = []
        for i in range(4):
            entry = CTkEntry(quaternion_frame, width=73, font=self.custom_font, state="disabled")  # Başlangıçta disabled
            entry.grid(row=0, column=i + 1, padx=5, pady=(0, 5), sticky="ew")
            self.q_entries.append(entry)
    
        # Quaternion CheckBox
        self.quaternion_check = tk.BooleanVar()
        self.quaternion_checkbox = CTkCheckBox(quaternion_frame, text="", variable=self.quaternion_check, onvalue=True, offvalue=False, command=self.toggle_quaternion)
        self.quaternion_checkbox.grid(row=0, column=5, padx=(10, 5), pady=(0, 5), sticky="e")
    
        # Preview butonu başlangıçta devre dışı (disabled), kırmızı arka plan
        self.preview_button = CTkButton(quaternion_frame, text="Preview",font = self.custom_font_fixedsys, width=40, height=20, fg_color="red", hover_color="darkred", state="disabled", command=self.update_preview)
        self.preview_button.grid(row=0, column=5, padx=(0, 5), pady=(0, 5), sticky="e")
   
    def add_euler_angles_section(self, parent):
        euler_frame = CTkFrame(parent)
        euler_frame.grid(row=2, column=0, padx=10, pady=(0, 0), sticky="w")
    
        # Satır ve sütun genişliği kontrolü
        parent.grid_rowconfigure(2, weight=0)  # Satır yüksekliği kontrol edilir
        parent.grid_columnconfigure(0, weight=1)  # Sütun genişliği kontrol edilir
    
        CTkButton(euler_frame, text='Euler Angles (deg)', font=self.custom_font).grid(row=0, column=0, pady=(0, 5), sticky="w")
    
        # Euler entries
        self.euler_entries = []
        for i in range(3):
            entry = CTkEntry(euler_frame, width=100, font=self.custom_font, state="disabled")
            entry.grid(row=0, column=i + 1, padx=5, pady=(0, 5), sticky="ew")
            self.euler_entries.append(entry)
    
        # Euler CheckBox
        self.euler_check = tk.BooleanVar()
        self.euler_checkbox = CTkCheckBox(euler_frame, text="", variable=self.euler_check, onvalue=True, offvalue=False, command=self.toggle_euler)
        self.euler_checkbox.grid(row=0, column=4, padx=(10, 5), pady=(0, 5), sticky="e")

    def toggle_quaternion(self):
        if self.quaternion_check.get():
            # Euler checkbox'ını devre dışı bırak ve entry'lerini temizle
            self.euler_check.set(False)
            self.euler_checkbox.configure(state="disabled")
            for entry in self.euler_entries:
                entry.delete(0, tk.END)  # Değerleri sil
                entry.configure(state="disabled")  # Entry'leri devre dışı bırak
                
            # Quaternion entry'lerini aktif hale getir
            for entry in self.q_entries:
                entry.configure(state="normal")
        else:
            # Quaternion checkbox'ı pasif hale getirildiğinde entry'ler temizlenir
            for entry in self.q_entries:
                entry.delete(0, tk.END)  # Değerleri sil
                entry.configure(state="disabled")
            
            # Euler checkbox'ını tekrar aktif hale getir
            self.euler_checkbox.configure(state="normal")
       
    def toggle_euler(self):
        if self.euler_check.get():
            # Quaternion checkbox'ını devre dışı bırak ve entry'lerini temizle
            self.quaternion_check.set(False)
            self.quaternion_checkbox.configure(state="disabled")
            for entry in self.q_entries:
                entry.delete(0, tk.END)  # Değerleri sil
                entry.configure(state="disabled")  # Entry'leri devre dışı bırak
                
            # Euler entry'lerini aktif hale getir
            for entry in self.euler_entries:
                entry.configure(state="normal")
        else:
            # Euler checkbox'ı pasif hale getirildiğinde entry'ler temizlenir
            for entry in self.euler_entries:
                entry.delete(0, tk.END)  # Değerleri sil
                entry.configure(state="disabled")
            
            # Quaternion checkbox'ını tekrar aktif hale getir
            self.quaternion_checkbox.configure(state="normal")
            
    def toggle_altitude(self):
        # Altitude checkbox kontrolü ve entry'nin durumu
        state = "normal" if self.altitude_check.get() else "disabled"
        self.altitude_entry.configure(state=state)
        
        # Semi-major axis entry'si devre dışı bırakılacaksa içeriği silinir
        semi_major_axis_entry_state = "disabled" if self.altitude_check.get() else "normal"
        if semi_major_axis_entry_state == "disabled":
            self.semi_major_axis_entry.delete(0, tk.END)  # Semi-major içerik silinir
        
        # Semi-major axis entry'sinin durumu ayarlanır
        self.semi_major_axis_entry.configure(state=semi_major_axis_entry_state)

    def create_fig1(self):
        # Increase the figure size slightly
        fig1 = Figure(figsize=(6.5, 3.5), facecolor='#2B2B2B')  # Increased the figure size
        ax1 = fig1.add_subplot(111, projection=ccrs.PlateCarree())
        ax1.add_feature(cfeature.COASTLINE)
        ax1.add_feature(cfeature.BORDERS, linestyle=':')
        ax1.set_global()
        ax1.set_facecolor('#2B2B2B')
    
        # Create longitudes and latitudes grid
        lon, lat = np.meshgrid(np.linspace(-180, 179, self.Btot_magnitude.shape[2]), 
                               np.linspace(-89, 90, self.Btot_magnitude.shape[1]))
    
        # Create heatmap and add a colorbar
        heatmap = ax1.contourf(lon, lat, self.Btot_magnitude[0], 60, transform=ccrs.PlateCarree(), cmap='jet')
    
        # Adjust colorbar
        cbar = fig1.colorbar(heatmap, ax=ax1, orientation='vertical', pad=0.05, shrink=0.8)
    
        # Set ticks and labels for colorbar, reducing the number of ticks and setting colors to white
        vmin, vmax = heatmap.get_clim()
        ticks = np.linspace(vmin, vmax, num=4)  # Reduced number of ticks to 4
        cbar.set_ticks(ticks)
    
        # Set the colorbar text to "times $10^4$" and adjust its position and size, bold text
        cbar.ax.text(1.02, 1.05, r'$10^4$', transform=cbar.ax.transAxes, fontsize=8, va='bottom', ha='right', 
                     color='#FFFFFF', fontproperties=roboto_prop, fontweight='bold')  # Moved above the bar and bold
    
        tick_labels = [f'{t/1e4:.1f}' for t in ticks]  # Adjusted to show "times 10^4"
        cbar.set_ticklabels(tick_labels)
        
        # Set tick labels to white and bold
        plt.setp(cbar.ax.get_yticklabels(), color='#FFFFFF', fontsize=8, fontproperties=roboto_prop, fontweight='bold')
    
        cbar.set_label('(nanoTesla)', color='#FFFFFF', fontproperties=roboto_prop, fontsize=8, fontweight='bold')
    
        # Adjust the ticks and font sizes for the x and y axes
        ax1.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
        ax1.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
    
        # Set smaller font size for axis labels and tick marks, and bold labels
        ax1.set_xlabel('Longitude (degrees)', color='#FFFFFF', fontsize=8, labelpad=3, fontproperties=roboto_prop, fontweight='bold')  # Reduced pad
        ax1.set_ylabel('Latitude (degrees)', color='#FFFFFF', fontsize=8, labelpad=3, fontproperties=roboto_prop, fontweight='bold')
        ax1.tick_params(axis='x', colors='#FFFFFF', labelsize=8, width=1.5)
        ax1.tick_params(axis='y', colors='#FFFFFF', labelsize=8, width=1.5)
    
        # Shift the figure up slightly by adjusting the gridlines position and adding padding
        ax1.gridlines(draw_labels=False, xlocs=np.arange(-180, 181, 60), ylocs=np.arange(-90, 91, 30), color='#FFFFFF')
        # Assuming Constants.ALTITUDE holds the value you want to display
        ax1.set_title(
            fr'$B_{{tot}} \, \mathrm{{Magnitude}}$ (ECEF) @{Constants.ALTITUDE} km', 
            fontsize=10, color='#FFFFFF', pad=5, fontproperties=roboto_prop, fontweight='bold'
        )
    
        # Draw the figure on the canvas
        self.canvas_fig1 = self.create_canvas_figure(fig1, self.canvas1)
        self.canvas_fig1.draw()

    def create_canvas(self, parent, row, column):
        # Canvas size adjusted to fit better (400x250)
        canvas = tk.Canvas(parent, width=20, height=330, bg='black')  
        canvas.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")  # Center the canvas dynamically
        return canvas

    def create_canvas_figure(self, fig, canvas):
        canvas_fig = FigureCanvasTkAgg(fig, master=canvas)
        
        # Set the figure to fully occupy the canvas, with no padding
        canvas_fig.get_tk_widget().place(relx=0, rely=0, relwidth=1, relheight=1)  
        
        # Update the canvas size to fit the figure perfectly
        canvas.update_idletasks()  # Make sure the canvas is fully updated before drawing
        return canvas_fig

    def close_window(self):
        """GUI kapanırken programı tamamen sonlandırır."""
        self.quit()  # Ana döngüyü sonlandır
        self.destroy()  # Pencereyi tamamen yok et

    def create_time_coord_system_frame(self, parent):
        frame1 = CTkFrame(parent)
        frame1.grid(row=0, column=0, padx=10, pady=10, sticky="we")
    
        title = CTkButton(frame1, text="Time and Coordinate System", font=self.custom_font)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))
    
        # Labels and their respective default values
        labels = ["DateFormat:", "CoordinateSystem:", "Epoch"]
        default_values = ["UTCGregorian", "EarthMJ2000Eq", Constants.SPECIFIC_TIME_STR]
    
        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            CTkButton(frame1, text=label, font=self.custom_font).grid(row=i+1, column=0, sticky="w")
            entry = CTkEntry(frame1, width=200, font=self.custom_font)
            entry.grid(row=i+1, column=1)
            entry.insert(0, default_value)  # Varsayılan değeri yazdır
    
            # Epoch entry'sini self ile tanımlayın
            if label == "Epoch":
                self.epoch_entry = entry
    
            # Disable the first two fields to prevent editing
            if label in ["DateFormat:", "CoordinateSystem:"]:
                entry.configure(state="disabled")

    def create_keplerian_elements_frame(self, parent):
        frame2 = CTkFrame(parent)
        frame2.grid(row=1, column=0, padx=10, pady=10, sticky="w")
    
        title = CTkButton(frame2, text="Keplerian Elements", font=self.custom_font)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))
    
        labels = ["Semi-major axis (km)", "Eccentricity", "Inclination (deg)", 
                  "RAAN (deg)", "AOP (deg)", "TA (deg)"]
        default_values = [Constants.SATELLITE_PARAMS["sma"], Constants.SATELLITE_PARAMS["ecc"], Constants.SATELLITE_PARAMS["inc"], Constants.SATELLITE_PARAMS["ra"], Constants.SATELLITE_PARAMS["aop"], Constants.SATELLITE_PARAMS["ta"]]
    
        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            CTkButton(frame2, text=label, font=self.custom_font).grid(row=i+1, column=0, sticky="w")
    
            # Entry widget'larını self ile tanımlıyoruz
            if label == "Semi-major axis (km)":
                self.semi_major_axis_entry = CTkEntry(frame2, width=200, font=self.custom_font)
                self.semi_major_axis_entry.grid(row=i+1, column=1)
                self.semi_major_axis_entry.insert(0, default_value)  # Varsayılan değeri yazdır
            elif label == "Eccentricity":
                self.ecc_entry = CTkEntry(frame2, width=200, font=self.custom_font)
                self.ecc_entry.grid(row=i+1, column=1)
                self.ecc_entry.insert(0, default_value)
            elif label == "Inclination (deg)":
                self.inc_entry = CTkEntry(frame2, width=200, font=self.custom_font)
                self.inc_entry.grid(row=i+1, column=1)
                self.inc_entry.insert(0, default_value)
            elif label == "RAAN (deg)":
                self.ra_entry = CTkEntry(frame2, width=200, font=self.custom_font)
                self.ra_entry.grid(row=i+1, column=1)
                self.ra_entry.insert(0, default_value)
            elif label == "AOP (deg)":
                self.aop_entry = CTkEntry(frame2, width=200, font=self.custom_font)
                self.aop_entry.grid(row=i+1, column=1)
                self.aop_entry.insert(0, default_value)
            elif label == "TA (deg)":
                self.ta_entry = CTkEntry(frame2, width=200, font=self.custom_font)
                self.ta_entry.grid(row=i+1, column=1)
                self.ta_entry.insert(0, default_value)

    def create_physical_properties_frame(self, parent):
        frame3 = CTkFrame(parent)
        frame3.grid(row=2, column=0, padx=10, pady=10, sticky="w")
    
        title = CTkButton(frame3, text="Physical Properties and Surface Areas", font=self.custom_font)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))
    
        labels = ["DryMass (kg)", "DragArea (m^2)", "SRPArea (m^2)"]
        default_values = [Constants.SATELLITE_PARAMS["dry_mass"], Constants.SATELLITE_PARAMS["drag_area"], Constants.SATELLITE_PARAMS["srp_area"]]
    
        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            CTkButton(frame3, text=label, font=self.custom_font).grid(row=i+1, column=0, sticky="w")
    
            # Entry widget'larını self ile tanımlıyoruz
            if label == "DryMass (kg)":
                self.dry_mass_entry = CTkEntry(frame3, width=200, font=self.custom_font)
                self.dry_mass_entry.grid(row=i+1, column=1)
                self.dry_mass_entry.insert(0, default_value)
            elif label == "DragArea (m^2)":
                self.drag_area_entry = CTkEntry(frame3, width=200, font=self.custom_font)
                self.drag_area_entry.grid(row=i+1, column=1)
                self.drag_area_entry.insert(0, default_value)
            elif label == "SRPArea (m^2)":
                self.srp_area_entry = CTkEntry(frame3, width=200, font=self.custom_font)
                self.srp_area_entry.grid(row=i+1, column=1)
                self.srp_area_entry.insert(0, default_value)

    def create_aerodynamic_properties_frame(self, parent):
        frame4 = CTkFrame(parent)
        frame4.grid(row=3, column=0, padx=10, pady=10, sticky="w")
    
        title = CTkButton(frame4, text="Aerodynamic and Solar Radiation Properties", font=self.custom_font)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))
    
        labels = ["Cr", "Cd", "MagneticIndex (0-6)"]
        default_values = [Constants.SATELLITE_PARAMS["cr"], Constants.SATELLITE_PARAMS["cd"], "6"]
    
        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            CTkButton(frame4, text=label, font=self.custom_font).grid(row=i+1, column=0, sticky="w")
    
            # Entry widget'larını self ile tanımlıyoruz
            if label == "Cr":
                self.cr_entry = CTkEntry(frame4, width=200, font=self.custom_font)
                self.cr_entry.grid(row=i+1, column=1)
                self.cr_entry.insert(0, default_value)
            elif label == "Cd":
                self.cd_entry = CTkEntry(frame4, width=200, font=self.custom_font)
                self.cd_entry.grid(row=i+1, column=1)
                self.cd_entry.insert(0, default_value)
            elif label == "MagneticIndex (0-6)":
                self.mag_index_entry = CTkEntry(frame4, width=200, font=self.custom_font)
                self.mag_index_entry.grid(row=i+1, column=1)
                self.mag_index_entry.insert(0, default_value)

    def create_spacecraft_constants_frame(self, parent):
        frame5 = CTkFrame(parent)
        frame5.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    
        # Disturbance Torques
        CTkButton(frame5, text="Disturbance Torques (Nm)", font=self.custom_font).grid(row=0, column=0, columnspan=3, pady=(10, 10))
        
        # Torque entries'lerini self ile tanımlıyoruz
        self.torque_entries = []
        torque_values = [Constants.DISTURBANCE_TORQUES[0], Constants.DISTURBANCE_TORQUES[1], Constants.DISTURBANCE_TORQUES[2]]
        for i, value in enumerate(torque_values):
            entry = CTkEntry(frame5, width=100, font=self.custom_font)
            entry.grid(row=1, column=i, padx=5)
            entry.insert(0, value)
            self.torque_entries.append(entry)  # Entry'leri listeye ekliyoruz
    
        # Inertia Matrix
        inertia_title = CTkButton(frame5, text="Inertia Matrix (kg*m^2)", font=self.custom_font)
        inertia_title.grid(row=2, column=0, columnspan=3, pady=(10, 10))
    
        # Inertia matrix girişlerini self ile tanımlıyoruz
        self.inertia_matrix_entries = []
        # inertia_matrix_values = [["0.000826", "0", "0"],
        #                          ["0", "0.000425", "0"],
        #                          ["0", "0", "0.0012"]]
        inertia_matrix_values = Constants.J_MATRIX
    
        for i in range(3):
            row_entries = []
            for j in range(3):
                entry = CTkEntry(frame5, width=100, font=self.custom_font)
                entry.grid(row=i+3, column=j, padx=5)
                entry.insert(0, inertia_matrix_values[i][j])
                row_entries.append(entry)
            self.inertia_matrix_entries.append(row_entries)
    
        # Proportional Constant
        CTkButton(frame5, text="Proportional Constant for control law", font=self.custom_font).grid(row=6, column=0, columnspan=3, pady=(20, 10))
        self.prop_const_entry = CTkEntry(frame5, width=100, font=self.custom_font)
        self.prop_const_entry.grid(row=7, column=1)
        self.prop_const_entry.insert(0, "0.007")
    
        # W_Noise ve B_Noise
        CTkButton(frame5, text="W-Noise (rad/s)", font=self.custom_font).grid(row=10, column=0, pady=(20, 10))
        self.w_noise_entry = CTkEntry(frame5, width=100, font=self.custom_font)
        self.w_noise_entry.grid(row=11, column=0, padx=5)
        self.w_noise_entry.insert(0, Constants.W_NOISE_SCALE)  # Sabit olmayan, rastgele bir değer
    
        CTkButton(frame5, text="B-Noise (nT)", font=self.custom_font).grid(row=10, column=2, pady=(20, 10))
        self.b_noise_entry = CTkEntry(frame5, width=100, font=self.custom_font)
        self.b_noise_entry.grid(row=11, column=2, padx=5)
        self.b_noise_entry.insert(0, Constants.BTOT_NOISE_SCALE)

    def create_simulation_parameters_frame(self, parent):
        frame6 = CTkFrame(parent)
        frame6.grid(row=1, column=0, columnspan=3, padx=10, pady=(3, 3), sticky="n")
    
        title = CTkButton(frame6, text="Simulation Parameters", font=self.custom_font)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 5))
    
        labels = ["Total Simulation Time (sec)", "Time Step (sec)", "Interval (ms)", "Resolution"]
        default_values = [Constants.NUM_STEPS, Constants.STEP, Constants.INTERVAL_DELAY, Constants.RESOLUTION_SCALE]
    
        # Entry widget'larını self ile tanımlıyoruz
        self.simulation_time_entry = None
        self.time_step_entry = None
        self.interval_entry = None
        self.resolution_entry = None
    
        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            CTkButton(frame6, text=label, font=self.custom_font, width=200).grid(row=i+1, column=0, sticky="w", pady=(10, 10))
            entry = CTkEntry(frame6, width=184, font=self.custom_font)
            entry.grid(row=i+1, column=1, pady=(5, 5))
            entry.insert(0, default_value)
    
            # Entry'leri self ile tanımlayın
            if label == "Total Simulation Time (sec)":
                self.simulation_time_entry = entry
            elif label == "Time Step (sec)":
                self.time_step_entry = entry
            elif label == "Interval (ms)":
                self.interval_entry = entry
            elif label == "Resolution":
                self.resolution_entry = entry              
                
    def add_angular_rate_section(self, parent):
        angular_rate_frame = CTkFrame(parent)
        angular_rate_frame.grid(row=6, column=0, padx=10, pady=(0, 0), sticky="w")
    
        # Satır ve sütun genişliği kontrolü
        parent.grid_rowconfigure(6, weight=0)  # Satır yüksekliği kontrol edilir
        parent.grid_columnconfigure(0, weight=1)  # Sütun genişliği kontrol edilir
        
        # Başlık
        CTkButton(angular_rate_frame, text='Angular Rate (rad/s)', font=self.custom_font).grid(row=0, column=0, pady=(0, 5), sticky="w")
    
        # Angular Rate entries
        self.angular_rate_entries = []
        # Default Angular Rate değerleri
        angular_rate_values = [Constants.w[0], Constants.w[1], Constants.w[2]]
        for i, value in enumerate(angular_rate_values):
            entry = CTkEntry(angular_rate_frame, width=60, font=self.custom_font)
            entry.grid(row=0, column=i + 1, padx=5, pady=(0, 5), sticky="w")
            entry.insert(0, value)  # Default değeri ekle
            self.angular_rate_entries.append(entry)  # Entry'leri listeye ekliyoruz 

    # Progress bar creation
    def create_progress_bar(self):
        # Create a new frame spanning both the left and right frame at the bottom
        self.progress_frame = CTkFrame(self)  # self.progress_frame global olarak tanımlandı
        self.progress_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")  # Tüm bölümler için ortak progress bar
        
        # Add progress bar spanning across both frames
        self.progress_bar = CTkProgressBar(self.progress_frame, width=750)
        self.progress_bar.grid(row=0, column=0, pady=(1, 1), sticky="ew")  # Progress bar ile üstündeki label arasındaki boşluk azaltıldı
        
        # Create label for displaying percentage in the center of the progress bar with a smaller font size
        self.progress_label = CTkLabel(self.progress_frame, text="0.0%", font=CTkFont(family="Roboto", size=9))  # Font size reduced to 9
        self.progress_label.grid(row=0, column=0, sticky="n")
        
        # Add label to display Step / Num_Step to the right of the progress bar
        self.step_label = CTkLabel(self.progress_frame, text="0 / 0", font=CTkFont(family="Roboto", size=9))  # Step/Num_Step label
        self.step_label.grid(row=0, column=1, padx=(20, 10), sticky="ns")  # Positioned to the right of the progress bar
        
        # Create label for file saved message (initially empty)
        self.progress_file_label = CTkLabel(self.progress_frame, text="", font=CTkFont(family="Roboto", size=9))
        self.progress_file_label.grid(row=0, column=2, padx=(20, 10), sticky="wns")
        
        # Set initial value for demonstration (this will be dynamic later)
        self.update_progress(0.0, step=0, num_step=0)
        
    # Function to create the control buttons
    def create_control_buttons(self):
        # Butonları progress_frame içinde en sağa hizalayalım
        button_frame = CTkFrame(self.progress_frame)  # self.progress_frame kullanılıyor
        button_frame.grid(row=0, column=2, padx=(200, 5), pady=(0, 0), sticky="e")  # Frame sağa hizalanmış
    
        # Butonlar için genişlik ve yükseklik ayarları
        button_width = 100
        button_height = 20  # Progress bar yüksekliği ile uyumlu
        
        # next button (Solda boşluk için padx ayarlandı)
        self.next_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Next", width=button_width, height=button_height,fg_color="red", hover_color="darkred", state="disabled", command = self.start_gui)
        self.next_button.grid(row=0, column=0, padx=(5, 5), pady=(5, 0))  # Solda 5 birim boşluk, buton arası 5 birim
    
    
        # Cancel button (Solda boşluk için padx ayarlandı)
        self.cancel_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Cancel", width=button_width, height=button_height, command=self.close_window)
        self.cancel_button.grid(row=0, column=1, padx=(5, 5), pady=(5, 0))  # Solda 5 birim boşluk, buton arası 5 birim
    
        # Apply button (Buton aralarında boşluk ayarlandı)
        self.apply_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Apply", width=button_width, height=button_height, command=self.apply_values)
        self.apply_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 0))  # Solda ve sağda 5 birim boşluk
    
        # Run button with green background (Sağda boşluk için padx ayarlandı)
        self.run_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Run", width=button_width, height=button_height, fg_color="green", hover_color="darkgreen", command=self.start_simulation_thread)
        self.run_button.grid(row=0, column=3, padx=(5, 5), pady=(5, 0))  # Sağda 5 birim boşluk

    def apply_values(self):
        try:
            # Girdi alanlarından değerleri oku ve Constants sınıfına ata
            # Altitude checkbox aktifse, sma değerini altitude ile güncelle
            if self.altitude_check.get():
                Constants.ALTITUDE = int(self.altitude_entry.get())
                Constants.R_RADIUS = 6378.1363  # R_RADIUS sabiti
                altitude_value = float(self.altitude_entry.get())
                Constants.SATELLITE_PARAMS["sma"] = Constants.R_RADIUS + altitude_value
            else:
                # Altitude devre dışıysa normal sma değerini kullan
                Constants.SATELLITE_PARAMS["sma"] = float(self.semi_major_axis_entry.get())
                
            # Semi-major axis should be greater than 6478.1363
            if Constants.SATELLITE_PARAMS["sma"] <= 6478.1363:
                raise ValueError("Semi-major axis must be greater than 6478.1363 km")
            else:
                self.progress_file_label.configure(text="")  # Clear any previous error message
            
            Constants.SATELLITE_PARAMS["ecc"] = float(self.ecc_entry.get())  # Eccentricity entry
            
            # Eccentricity should be either less than 0.9999999 or greater than 1
            if not (Constants.SATELLITE_PARAMS["ecc"] < 0.9999999 or Constants.SATELLITE_PARAMS["ecc"] > 1.0):
                raise ValueError("Eccentricity must be less than 0.9999999 or greater than 1")
            else:
                self.progress_file_label.configure(text="")  # Clear any previous error message
            
            Constants.SATELLITE_PARAMS["inc"] = float(self.inc_entry.get())  # Inclination entry
            
            # Inclination should be between 0 and 180 degrees
            if not (0 <= Constants.SATELLITE_PARAMS["inc"] <= 180):
                raise ValueError("Inclination must be between 0 and 180 degrees")
            else:
                self.progress_file_label.configure(text="")  # Clear any previous error message
            
            Constants.SATELLITE_PARAMS["ra"] = float(self.ra_entry.get())  # RAAN entry
            Constants.SATELLITE_PARAMS["aop"] = float(self.aop_entry.get())  # AOP entry
            Constants.SATELLITE_PARAMS["ta"] = float(self.ta_entry.get())  # True Anomaly entry
                
            # Fiziksel ve aerodinamik parametreleri oku
            Constants.SATELLITE_PARAMS["dry_mass"] = float(self.dry_mass_entry.get())
            Constants.SATELLITE_PARAMS["drag_area"] = float(self.drag_area_entry.get())
            Constants.SATELLITE_PARAMS["srp_area"] = float(self.srp_area_entry.get())
            # Aerodinamik parametreler
            Constants.SATELLITE_PARAMS["cr"] = float(self.cr_entry.get())
            Constants.SATELLITE_PARAMS["cd"] = float(self.cd_entry.get())
                
            
            # Disturbance torques için değerleri oku ve ata
            Constants.DISTURBANCE_TORQUES[0] = float(self.torque_entries[0].get())
            Constants.DISTURBANCE_TORQUES[1] = float(self.torque_entries[1].get())
            Constants.DISTURBANCE_TORQUES[2] = float(self.torque_entries[2].get())
            
            # Inertia matrix için değerleri oku ve ata
            for i in range(3):
                for j in range(3):
                    Constants.J_MATRIX[i][j] = float(self.inertia_matrix_entries[i][j].get())
            
            # Proportional constant için değerleri oku ve ata
            Constants.PROPORTIONAL_CONSTANT = float(self.prop_const_entry.get())
            
            # Noise scaling faktörleri için değerleri oku ve ata
            Constants.W_NOISE_SCALE = float(self.w_noise_entry.get())
            Constants.BTOT_NOISE_SCALE = int(self.b_noise_entry.get())
            Constants.SPECIFIC_TIME_STR = self.epoch_entry.get()
            Constants.KP_IDX = int(self.mag_index_entry.get())
            Constants.TRUE_ANOMALIES = int(self.ta_entry.get())
            Constants.NUM_STEPS = int(self.simulation_time_entry.get())
            Constants.STEP = int(self.time_step_entry.get())
            Constants.INTERVAL_DELAY = int(self.interval_entry.get())
            Constants.RESOLUTION = int(self.resolution_entry.get())
            
            qx = float(self.q_entries[0].get())
            qy = float(self.q_entries[1].get())
            qz = float(self.q_entries[2].get())
            qw = float(self.q_entries[3].get())
            
            Constants.q = np.array([qx, qy, qz, qw])
            
            wx = float(self.angular_rate_entries[0].get())
            wy = float(self.angular_rate_entries[1].get())
            wz = float(self.angular_rate_entries[2].get())
            
            # Değerleri Constants.w'ye ata
            Constants.w = np.array([wx, wy, wz])
            
            # Test amacıyla değişen değerleri yazdır
            print("Updated Constants:")
            print("Altitude (km):", Constants.ALTITUDE)
            print("Satellite Parameters:", Constants.SATELLITE_PARAMS)
            print("Disturbance Torques (Nm):", Constants.DISTURBANCE_TORQUES)
            print("Inertia Matrix (kg*m2):", Constants.J_MATRIX)
            print("Proportional Constant:", Constants.PROPORTIONAL_CONSTANT)
            print("W Noise Scale (rad/s):", Constants.W_NOISE_SCALE)
            print("BTOT Noise Scale (nT):", Constants.BTOT_NOISE_SCALE)
            print("Specific Time String (UTC):", Constants.SPECIFIC_TIME_STR)
            print("Kp:", Constants.KP_IDX)
            print("NUM_STEPS (s):", Constants.NUM_STEPS)
            print("STEP (s):", Constants.STEP)
            print("INTERVAL_DELAY (ms):", Constants.INTERVAL_DELAY)
            print("Resolution:", Constants.RESOLUTION)
            print("quaternion:", Constants.q)
            print("Angular Rate (rad/s):", Constants.w)
            
            self.progress_file_label.configure(text="Initial Values Saved.")
            
        except ValueError as e:
            # Hata mesajını göster
            self.progress_file_label.configure(text=f"Error: {str(e)}")

    # Method to update progress bar, percentage label, and step label
    def update_progress(self, value, step, num_step):
        # Update progress bar value
        self.progress_bar.set(value / 100.0)  # progress bar expects value between 0 and 1
    
        # Update the label to show the percentage with 1 decimal and % sign
        self.progress_label.configure(text=f"{value:.1f}%")
    
        if self.is_calculate_button_pressed:
            # Update the step label to show current step and total number of steps
            self.step_label.configure(text=f"{step} / {self.total_steps}")
        else:
            # Update the step label to show current step and total number of steps
            self.step_label.configure(text=f"{step} / {num_step}")

    #     return q_DCM, Btot_body
def q_to_DCM(q, Btot_ECI):
        q1, q2, q3, q4 = q
        
        q_DCM = np.array([[q4**2 + q1**2 - q2**2 - q3**2, 2*(q1*q2 + q3*q4), 2*(q1*q3 - q2*q4)],
                      [2*(q1*q2 - q3*q4), q4**2 - q1**2 + q2**2 - q3**2, 2*(q2*q3 + q1*q4)],
                      [2*(q1*q3 + q2*q4), 2*(q2*q3 - q1*q4), q4**2 - q1**2 - q2**2 + q3**2]])
        Btot_ECI_flat = Btot_ECI.flatten()
        Btot_body = q_DCM @ Btot_ECI_flat
        return q_DCM, Btot_body
def euler_from_quaternion(q):
            """
            Convert a quaternion into euler angles (roll, pitch, yaw)
            """
            x, y, z, w = q
            t0 = +2.0 * (w * x + y * z)
            t1 = +1.0 - 2.0 * (x * x + y * y)
            roll_x = np.arctan2(t0, t1)
    
            t2 = +2.0 * (w * y - z * x)
            t2 = np.clip(t2, -1.0, 1.0)
            pitch_y = np.arcsin(t2)
    
            t3 = +2.0 * (w * z + x * y)
            t4 = +1.0 - 2.0 * (y * y + z * z)
            yaw_z = np.arctan2(t3, t4)
    
            return roll_x, pitch_y, yaw_z  # in radians
    
def get_quaternion_from_euler(roll, pitch, yaw):
  """
  Convert an Euler angle to a quaternion.
   
  Input
    :param roll: The roll (rotation around x-axis) angle in radians.
    :param pitch: The pitch (rotation around y-axis) angle in radians.
    :param yaw: The yaw (rotation around z-axis) angle in radians.
 
  Output
    :return qx, qy, qz, qw: The orientation in quaternion [x,y,z,w] format
  """
  qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
  qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
  qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
  qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
 
  return qx, qy, qz, qw

class Satellite:
    def __init__(self, name, sma, ecc, inc, ra, aop, ta, srp_area, cr, cd, dry_mass, drag_area):
        # Create spacecraft object
        self.spacecraft = gmat.Construct("Spacecraft", name)
        self.setup_spacecraft(sma, ecc, inc, ra, aop, ta, srp_area, cr, cd, dry_mass, drag_area)
        
    def setup_spacecraft(self, sma, ecc, inc, ra, aop, ta, srp_area, cr, cd, dry_mass, drag_area):
        # Set fields for the spacecraft
        self.spacecraft.SetField("DateFormat", "UTCGregorian")
        self.spacecraft.SetField("Epoch", "20 Jul 2020 12:00:00.000")
        self.spacecraft.SetField("CoordinateSystem", "EarthMJ2000Eq")
        self.spacecraft.SetField("DisplayStateType", "Keplerian")
        self.spacecraft.SetField("SMA", sma)
        self.spacecraft.SetField("ECC", ecc)
        self.spacecraft.SetField("INC", inc)
        self.spacecraft.SetField("RAAN", ra)
        self.spacecraft.SetField("AOP", aop)
        self.spacecraft.SetField("TA", ta)
        self.spacecraft.SetField("SRPArea", srp_area)
        self.spacecraft.SetField("Cr", cr)
        self.spacecraft.SetField("Cd", cd)
        self.spacecraft.SetField("DryMass", dry_mass)
        self.spacecraft.SetField("DragArea", drag_area)
        
    def get_state(self, gator):
        # Get the state of the spacecraft
        return gator.GetState()
    
    def get_name(self):
        return self.spacecraft.GetName()

def create_satellite(name, ta):
    params = Constants.SATELLITE_PARAMS
    return Satellite(
        name=name,
        sma=params["sma"],
        ecc=params["ecc"],
        inc=params["inc"],
        ra=params["ra"],
        aop=params["aop"],
        ta=ta,  # True anomaly
        srp_area=params["srp_area"],
        cr=params["cr"],
        cd=params["cd"],
        dry_mass=params["dry_mass"],
        drag_area=params["drag_area"]
    )

# Initialize a list to hold Satellite objects
satellites = []

# Create four satellites with different true anomalies
for k, ta in enumerate(Constants.TRUE_ANOMALIES):
    satellite = create_satellite(name=f"Taurus{k+1}", ta=ta)
    satellites.append(satellite)
    
# Define the force model
fm = gmat.Construct("ForceModel", "FM")

# Gravity model
earthgrav = gmat.Construct("GravityField")
earthgrav.SetField("BodyName", "Earth")
earthgrav.SetField("PotentialFile", get_gmat_data_path("gravity", "earth", "EGM96.cof"))
earthgrav.SetField("Degree", 8)
earthgrav.SetField("Order", 8)

# Point mass forces
moongrav = gmat.Construct("PointMassForce")
moongrav.SetField("BodyName", "Luna")
sungrav = gmat.Construct("PointMassForce")
sungrav.SetField("BodyName", "Sun")

# Drag force
jrdrag = gmat.Construct("DragForce")
jrdrag.SetField("AtmosphereModel", "JacchiaRoberts")
jrdrag.SetField("MagneticIndex", 6)
atmos = gmat.Construct("JacchiaRoberts")
jrdrag.SetReference(atmos)

# Solar radiation pressure
srp = gmat.Construct("SolarRadiationPressure", "SRP")

# Add forces to the force model
fm.AddForce(earthgrav)
fm.AddForce(jrdrag)
fm.AddForce(moongrav)
fm.AddForce(sungrav)
fm.AddForce(srp)

# Initialize GMAT
gmat.Initialize()

# Build the propagation container class
pdprop = gmat.Construct("Propagator", "PDProp")

# Create and assign a numerical integrator for use in the propagation
gator = gmat.Construct("PrinceDormand78", "Gator")
pdprop.SetReference(gator)

# Assign the force model
pdprop.SetReference(fm)

# Set fields for the integration
pdprop.SetField("InitialStepSize", 60)
pdprop.SetField("Accuracy", 1.0e-12)
pdprop.SetField("MinStep", 0.0)
pdprop.SetField("MaxStep", 2700)

# Setup the spacecraft that is propagated
for satellite in satellites:
    pdprop.AddPropObject(satellite.spacecraft)
pdprop.PrepareInternals()

# Refresh the 'gator' reference
gator = pdprop.GetPropagator()

def initialize_data_structures(satellites):
    data_magnetic = {
        sc.get_name(): {
            "Bint_ECI": [],
            "Bext_ECI": [],
            "Btot_ECI": [],
            "Btot_body": [],
            "Btot_ECEF": []
        } for sc in satellites
    }

    data_dyn_kin = {
        sc.get_name(): {
            "w": [],
            "q": [],
            "DCM": [],
            "euler": [],
            "quat_turn":[],
        } for sc in satellites
    }

    data_PV = {
        sc.get_name(): {
            "R_ECI": [],
            "R_Body": [],
            "velocity": []
        } for sc in satellites
    }

    data_geodetic = {
        sc.get_name(): {
            "latitude": [],
            "longitude": [],
            "altitude": []
        } for sc in satellites
    }

    return data_magnetic, data_dyn_kin, data_PV, data_geodetic

# Sözlükleri başlatmak için fonksiyonu çağırın
data_magnetic, data_dyn_kin, data_PV, data_geodetic = initialize_data_structures(satellites)

class SatelliteSimulator:
    def __init__(self, J, k, N, w_noise, Btot_noise):
        self.J = J
        self.k = k
        self.N = N
        self.w_noise = w_noise
        self.Btot_noise = Btot_noise
        self.timing_dict = {}
        self.J_inv = np.linalg.inv(J)  # Inverse of J calculated once
           
    def calculate_average_timings(self):
           """
            Zamanlamaların ortalamalarını hesaplar ve döner.
           """
           average_timings = {key: np.mean(times) for key, times in self.timing_dict.items()}
           return average_timings

    @staticmethod
    def skew_symmetric(v):
        """
        Create a skew-symmetric (cross product) matrix from a 3D vector.
        """
        return np.array([
            [0, -v[2], v[1]],
            [v[2], 0, -v[0]],
            [-v[1], v[0], 0]
        ])
    
    def w_and_q(self, t, y, Btot_body):
        start_time = time.time()  # Start timing
        w = y[0:3]
        q = y[3:7]
        Btot_body = Btot_body + self.Btot_noise
        # Btot_body dışarıdan input olarak alındı
        H_RG = self.J @ w  # Angular momentum
        M_RG = np.cross((1e-9) * Btot_body, -self.k * H_RG) / (np.linalg.norm((1e-9) * Btot_body) ** 2)
        M_RG = np.clip(M_RG, -0.017, 0.017)
    
        # Torque calculation
        torque_RG = self.skew_symmetric(M_RG) @ (Btot_body * 1e-9)
        torque_RG[2] = 0  # Set torque on Z axis to zero
        # Angular velocity derivative (w_dot)
        w_dot = self.J_inv @ (self.N  - np.cross(w, H_RG) + torque_RG)
    
        # Quaternion derivative (q_dot)
        omega1, omega2, omega3 = w
        
        Omega_br = np.array([[0, omega3, -omega2, omega1],
                     [-omega3, 0, omega1, omega2],
                     [omega2, -omega1, 0, omega3],
                     [-omega1, -omega2, -omega3, 0]])
    
        q_dot = 0.5 * Omega_br @ q
    
        end_time = time.time()  # End timing
        self.timing_dict.setdefault("w_and_q", []).append(end_time - start_time)
    
        return np.concatenate((w_dot, q_dot))

    def integrate_w_and_q(self, w, q, Btot_body, step):
        start_time = time.time()  # Start timing
        y0 = np.concatenate((w, q))
    
        # solve_ivp ile w_and_q fonksiyonu çağrılıyor
        sol = solve_ivp(self.w_and_q, [0, step], y0, args=(Btot_body,), method='DOP853', rtol=1e-9, atol=1e-9, t_eval=[step])
    
        # Sonuçları çıkar
        w_sol = sol.y[0:3, -1] + self.w_noise
        q_sol = sol.y[3:7, -1]
    
        end_time = time.time()  # End timing
        self.timing_dict.setdefault("integrate_w_and_q", []).append(end_time - start_time)
    
        return w_sol, q_sol


    def calculate_magnetic_fields(self, satellites, initial_ut, current_time, kp_index, x, num_steps, step, data_dyn_kin, data_PV, data_geodetic, data_magnetic):
        start_time = time.time()  # Start timing
        satellite = satellites[0]
        state = satellite.get_state(gator)
        r = state[:3]
        v = state[3:]
        spacecraft_name = satellite.get_name()
    
        ecllat, ecllon, alt = pymap3d.eci2geodetic(r[0] * 1e3, r[1] * 1e3, r[2] * 1e3, current_time)
        ps = geopack.recalc(initial_ut)
        ticks = Ticktock(current_time, 'UTC')
    
        R_ECI = coord.Coords([r[0], r[1], r[2]], 'ECI2000', 'car')
        data_PV[spacecraft_name]["R_ECI"].append(r)
        data_PV[spacecraft_name]["velocity"].append(v)
        R_ECI.ticks = ticks
        R_GSM = R_ECI.convert('GSM', 'car').data.flatten()
    
        xgsm, ygsm, zgsm = [R_GSM[0]/6371.2, R_GSM[1]/6371.2, R_GSM[2]/6371.2]
        bint_xgsm, bint_ygsm, bint_zgsm = geopack.igrf_gsm(xgsm, ygsm, zgsm)
        bext_xgsm, bext_ygsm, bext_zgsm = t89.t89(kp_index + 1, ps, xgsm, ygsm, zgsm)
    
        bxgsm, bygsm, bzgsm = [bint_xgsm + bext_xgsm, bint_ygsm + bext_ygsm, bint_zgsm + bext_zgsm]
        Btot_GSM = coord.Coords([bxgsm, bygsm, bzgsm], 'GSM', 'car')
        Btot_GSM.ticks = ticks
    
        Btot_ECI = Btot_GSM.convert('J2000', 'car').data
        Btot_ECI_flat = Btot_ECI.flatten()
        Btot_ECEF = Btot_GSM.convert('GEO', 'car').data
    
        if x == 0:
            # İlk adımda initial değerler kullanılıyor
            w = Constants.w # Initial angular velocity
            q = Constants.q  # Initial quaternion
            q_DCM, Btot_body = q_to_DCM(q, Btot_ECI_flat)
            eu_ang = euler_from_quaternion(q)
            quat_turn = get_quaternion_from_euler(eu_ang[0],eu_ang[1],eu_ang[1])
            data_dyn_kin[spacecraft_name]["w"] = [w]
            data_dyn_kin[spacecraft_name]["q"] = [q]
            data_dyn_kin[spacecraft_name]["DCM"] = [q_DCM]
            data_dyn_kin[spacecraft_name]["euler"] = [eu_ang]
            data_dyn_kin[spacecraft_name]["quat_turn"] = [quat_turn]
        else:
            # Sonraki adımlarda yeni hesaplanan değerler kullanılıyor
            w = data_dyn_kin[spacecraft_name]["w"][-1]
            q = data_dyn_kin[spacecraft_name]["q"][-1]
            
            # Yeni quaternion ile DCM ve Btot_body hesaplanıyor
            q_DCM, Btot_body = q_to_DCM(q, Btot_ECI_flat)
            # Sadece yeni quaternion ile hesaplanan DCM'yi kaydet
            data_dyn_kin[spacecraft_name]["DCM"][-1] = q_DCM  # Son kaydedilen DCM'yi güncelle
    
        # w_sol ve q_sol değerleri her adımda güncelleniyor
        w_sol, q_sol = self.integrate_w_and_q(w, q, Btot_body, step)
    
        # Sonraki adımlar için yeni hesaplanan değerler kaydediliyor
        if x < num_steps - 1:
            eu_ang = euler_from_quaternion(q_sol)
            quat_turn = get_quaternion_from_euler(eu_ang[0],eu_ang[1],eu_ang[2])
            
            data_dyn_kin[spacecraft_name]["euler"].append(eu_ang)
            data_dyn_kin[spacecraft_name]["w"].append(w_sol)
            data_dyn_kin[spacecraft_name]["q"].append(q_sol)
            data_dyn_kin[spacecraft_name]["DCM"].append(q_DCM)
            data_dyn_kin[spacecraft_name]["quat_turn"].append(quat_turn)
            
        R_Body = q_DCM @ r
    
        data_PV[spacecraft_name]["R_Body"].append(R_Body)
        data_magnetic[spacecraft_name]["Btot_ECI"].append(Btot_ECI_flat)
        data_magnetic[spacecraft_name]["Btot_body"].append(Btot_body)
        data_magnetic[spacecraft_name]["Btot_ECEF"].append(Btot_ECEF)
        data_geodetic[spacecraft_name]["latitude"].append(ecllat)
        data_geodetic[spacecraft_name]["longitude"].append(ecllon)
        data_geodetic[spacecraft_name]["altitude"].append(alt)
        
        
        end_time = time.time()  # End timing
        self.timing_dict.setdefault("calculate_magnetic_fields", []).append(end_time - start_time)

# Veri Sınıfı: Tüm veri işlemleri burada gerçekleştirilecek
class MagneticFieldData:
    def __init__(self, data_geodetic, data_magnetic, data_PV, data_dyn_kin):
        self.satellite_name = list(data_magnetic.keys())[0]
        self.latitude_data = data_geodetic[self.satellite_name]['latitude']
        self.longitude_data = data_geodetic[self.satellite_name]['longitude']
        self.altitude_data = data_geodetic[self.satellite_name]['altitude']

        self.Btot_ECEF_data = np.squeeze(np.array(data_magnetic[self.satellite_name]["Btot_ECEF"])) / 1000
        self.Btot_ECI_data = np.array(data_magnetic[self.satellite_name]["Btot_ECI"]) / 1000
        self.Btot_body_data = np.array(data_magnetic[self.satellite_name]["Btot_body"]) / 1000

        self.Btot_ECI_mag = np.linalg.norm(self.Btot_ECI_data, axis=1)[:, np.newaxis]
        self.Btot_ECEF_mag = np.linalg.norm(self.Btot_ECEF_data, axis=1)[:, np.newaxis]
        self.Btot_body_mag = np.linalg.norm(self.Btot_body_data, axis=1)[:, np.newaxis]

        self.Btot_ECI_norm = self.Btot_ECI_data / self.Btot_ECI_mag
        self.Btot_body_norm = self.Btot_body_data / self.Btot_body_mag
        self.Btot_ECEF_norm = self.Btot_ECEF_data / self.Btot_ECEF_mag

        self.R_ECI_data = np.array(data_PV[self.satellite_name]["R_ECI"])
        self.R_ECI_mag = np.linalg.norm(self.R_ECI_data, axis=1)[:, np.newaxis]
        self.R_ECI_norm = self.R_ECI_data / self.R_ECI_mag

        self.V_ECI_data = np.array(data_PV[self.satellite_name]["velocity"])
        self.V_ECI_mag = np.linalg.norm(self.V_ECI_data, axis=1)[:, np.newaxis]
        self.V_ECI_norm = self.V_ECI_data / self.V_ECI_mag

        self.R_Body_data = np.array(data_PV[self.satellite_name]["R_Body"])
        self.R_Body_mag = np.linalg.norm(self.R_Body_data, axis=1)[:, np.newaxis]
        self.R_Body_norm = self.R_Body_data / self.R_Body_mag

        self.euler_angles = np.array(data_dyn_kin[self.satellite_name]["euler"]) * (180/math.pi)
        self.angular_vel = np.array(data_dyn_kin[self.satellite_name]["w"]) * (180/math.pi)
        self.q_DCM = np.array(data_dyn_kin[self.satellite_name]["DCM"])

# GUI Sınıfı: Tüm GUI işlemleri burada gerçekleştirilecek
class MagneticFieldGUI:
    def __init__(self, root, data):
        # Btot_ECEF_ verisini yükleyin
        self.Btot_ECEF_ = np.load(f"Btot_magnitude_altitude_{Constants.ALTITUDE}.npy")
        # Btot_magnitude hesaplaması
        self.Btot_magnitude = np.linalg.norm(self.Btot_ECEF_, axis=0)
        self.Btot_magnitude = self.Btot_magnitude[np.newaxis, :, :]
        self.was_stopped = False  # Başlangıçta durdurulmadı
        self.pause_flag = False  # Duraklatma bayrağı
        self.stopped_flag = False

        self.esp32_pause_event = threading.Event()  # Pause için Event
        self.esp32_stop_event = threading.Event()   # Stop için Event
        self.esp32_paused_frame = 0  # Duraklatıldığında kaldığı satırı saklamak için
        self.esp32_was_stopped = False  # Stop durumunda bayrak
        self.import_button_pressed =False

        self.root = root
        self.data = data
        self.roboto_font = CTkFont(family="Century Gothic", size=12)  # roboto_font tanımlaması
        self.roboto_font2 = CTkFont(family="Century Gothic", size=10)
        self.custom_font_fixedsys = CTkFont(family='Fixedsys', size=12)
        self.cube_origin = np.array([[-0.6936 / 2, -0.6936 / 2, -0.1942 / 2],  # cube_origin tanımlaması
                                     [0.6936 / 2, -0.6936 / 2, -0.1942 / 2],
                                     [0.6936 / 2, 0.6936 / 2, -0.1942 / 2],
                                     [-0.6936 / 2, 0.6936 / 2, -0.1942 / 2],
                                     [-0.6936 / 2, -0.6936 / 2, 0.1942 / 2],
                                     [0.6936 / 2, -0.6936 / 2, 0.1942 / 2],
                                     [0.6936 / 2, 0.6936 / 2, 0.1942 / 2],
                                     [-0.6936 / 2, 0.6936 / 2, 0.1942 / 2]])
    
        self.setup_gui()
   
    def create_canvas(self, **kwargs):
       canvas = tk.Canvas(self.root, bg="white")
       canvas.place(**kwargs)
       return canvas

    def create_fig1(self):
       fig1 = Figure(figsize=(19.2, 10.8), facecolor='#2B2B2B')
       ax1 = fig1.add_subplot(111, projection=ccrs.PlateCarree())
       ax1.add_feature(cfeature.COASTLINE)
       ax1.add_feature(cfeature.BORDERS, linestyle=':')
       ax1.set_global()
       ax1.set_facecolor('#2B2B2B')
   
       # longitudes and latitudes verilerinin oluşturulması
       lon, lat = np.meshgrid(np.linspace(-180, 179, self.Btot_magnitude.shape[2]), 
                              np.linspace(-89, 90, self.Btot_magnitude.shape[1]))
   
       # Heatmap oluşturulması ve colorbar eklenmesi
       heatmap = ax1.contourf(lon, lat, self.Btot_magnitude[0], 60, transform=ccrs.PlateCarree(), cmap='jet')
       cbar = fig1.colorbar(heatmap, ax=ax1, orientation='horizontal', pad=0.15, shrink=0.8)
       
       vmin, vmax = heatmap.get_clim()
       ticks = np.linspace(vmin, vmax, num=6)
       tick_labels = [f'{t/1e4:.1f}' for t in ticks]
       cbar.set_ticks(ticks)
       cbar.set_ticklabels(tick_labels)
       cbar.ax.text(1.05, -0.7, r'$\times 10^{4}$', transform=cbar.ax.transAxes, fontsize=10, va='bottom', ha='left', color='#FFFFFF', fontproperties=roboto_prop)
       cbar.set_label('(nanoTesla)', fontweight='bold', color='#FFFFFF', fontproperties=roboto_prop)
       plt.setp(cbar.ax.get_xticklabels(), color='#FFFFFF', fontsize=10, fontweight='bold', fontproperties=roboto_prop)
   
       ax1.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
       ax1.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
       ax1.set_xlabel('Longitude (degrees)', color='#FFFFFF', fontproperties=roboto_prop)
       ax1.set_ylabel('Latitude (degrees)', color='#FFFFFF', fontproperties=roboto_prop)
       ax1.gridlines(draw_labels=False, xlocs=np.arange(-180, 181, 60), ylocs=np.arange(-90, 91, 30), color='#FFFFFF')
       ax1.tick_params(axis='x', colors='#FFFFFF')
       ax1.tick_params(axis='y', colors='#FFFFFF')
       # Assuming Constants.ALTITUDE holds the value you want to display
       ax1.set_title(
            fr'$B_{{tot}} \, \mathrm{{Magnitude}}$ (ECEF) @{Constants.ALTITUDE} km', 
            fontsize=10, color='#FFFFFF', pad=5, fontproperties=roboto_prop, fontweight='bold'
        )       
       return fig1, ax1

    def create_fig2(self):
       fig2 = Figure(figsize=(19.2, 10.8), facecolor='#2B2B2B')
       ax2 = fig2.add_subplot(111, projection='3d')
       self.setup_3d_axes(ax2)
       ax2.set_title('Normalized Vectors', fontsize=12, color='#FFFFFF', fontproperties=roboto_prop)
       return fig2, ax2

    def setup_3d_axes(self, ax):
       matrix_green = '#03A062'
       ax.set_facecolor('#2B2B2B')
       ax.xaxis.pane.set_facecolor('#2B2B2B')
       ax.yaxis.pane.set_facecolor('#2B2B2B')
       ax.zaxis.pane.set_facecolor('#2B2B2B')
       ax.xaxis.pane.set_edgecolor('white')
       ax.yaxis.pane.set_edgecolor('white')
       ax.zaxis.pane.set_edgecolor('white')
       ax.grid(True, color=matrix_green)
       ax.xaxis.pane.fill = False
       ax.yaxis.pane.fill = False
       ax.zaxis.pane.fill = False
       ax.tick_params(colors='white', labelsize=10, width=2)
       ax.xaxis.label.set_color('white')
       ax.yaxis.label.set_color('white')
       ax.zaxis.label.set_color('white')
       ax.set_xlim([-1, 1])
       ax.set_ylim([-1, 1])
       ax.set_zlim([-1, 1])
       ax.set_xticks(np.arange(-1, 1))
       ax.set_yticks(np.arange(-1, 1))
       ax.set_zticks(np.arange(-1, 1))
       ax.set_xlabel('X', labelpad=10, fontsize=10, fontweight='bold', fontproperties=roboto_prop)
       ax.set_ylabel('Y', labelpad=10, fontsize=10, fontweight='bold', fontproperties=roboto_prop)
       ax.set_zlabel('Z', labelpad=10, fontsize=10, fontweight='bold', fontproperties=roboto_prop)

    def create_fig3(self):
       fig3 = Figure(figsize=(8, 4), facecolor='#2B2B2B')
       ax3 = fig3.add_subplot(111)
       self.setup_2d_axes(ax3)
       fig3.subplots_adjust(left=0.07, right=0.97, top=0.97, bottom=0.17)
       return fig3, ax3

    def setup_2d_axes(self, ax):
       ax.set_facecolor('#2B2B2B')
       ax.grid(True, color='white')
       ax.tick_params(colors='white', labelsize=6, width=0.8)
       ax.xaxis.label.set_color('white')
       ax.yaxis.label.set_color('white')
       ax.set_xlabel('Time (s)', labelpad=1, fontsize=6, fontproperties=roboto_prop, color='white')
       ax.set_ylabel(r'$\omega$ (deg/s)', labelpad=1, fontsize=6, fontproperties=roboto_prop, color='white')
       ax.spines['top'].set_color('white')
       ax.spines['bottom'].set_color('white')
       ax.spines['left'].set_color('white')
       ax.spines['right'].set_color('white')
       ax.legend(loc='upper right', fontsize=1, prop=roboto_prop)

    def create_canvas_figure(self, fig, canvas):
       canvas_fig = FigureCanvasTkAgg(fig, master=canvas)
       canvas_fig.get_tk_widget().place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=1.0, relheight=1.0)
       return canvas_fig

    def create_checkboxes(self, checkbox_data):
        for text, variable, rel_x, rel_y in checkbox_data:
            checkbox = CTkCheckBox(self.root, text=text, variable=variable, onvalue=True, offvalue=False, bg_color="#2B2B2B", 
                                command=self.update_checkbox_quivers)  # Checkbox değiştiğinde quiver'ları güncelle
            checkbox.place(relx=rel_x, rely=rel_y, anchor="w")
            
    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def toggle_body_extra_fields(self):
        """Bu fonksiyon checkbox durumuna göre B.Body ek alanlarını aktif/pasif yapar."""
        state = tk.NORMAL if self.body_additional_entries_checkbox.get() else tk.DISABLED
        # Ekstra B.Body alanlarını kontrol et
        for entry in self.entries["B.Body ="][4:]:
            entry.configure(state=state)

    def update_checkbox_quivers(self):
        # Eğer pause modundaysa mevcut frame'i kullan
        if self.pause_flag:
            frame = self.current_frame_fig2 - 1 # Pause modunda mevcut kareyi kullan
        else:
            frame = len(self.data.latitude_data) - 1  # Aksi takdirde son kareyi kullan
    
        # Quiver'ları güncelle
        self.update_fig2(frame, self.data)
        self.canvas_fig2.draw()  # Güncellemeden sonra figürü yeniden çiz

    def setup_gui(self):
        # Checkbox değişkenlerini tanımlama
        self.eci_visible = tk.BooleanVar(value=False)
        self.body_visible = tk.BooleanVar(value=False)
        self.r_eci_visible = tk.BooleanVar(value=False)
        self.v_eci_visible = tk.BooleanVar(value=False)
        self.sat_body_visible = tk.BooleanVar(value=False)
        self.body_additional_entries_checkbox = tk.BooleanVar(value=False)
        self.init_ui()
        self.draw_figures()

    def init_ui(self):
        # Canvas ve Figürleri Tanımlama
        self.canvas1 = self.create_canvas(relx=0.02, rely=0.02, relwidth=0.46, relheight=0.70)
        self.canvas2 = self.create_canvas(relx=0.52, rely=0.02, relwidth=0.46, relheight=0.70)
        self.canvas3 = self.create_canvas(relx=0.52, rely=0.73, relwidth=0.46, relheight=0.25)

        self.fig1, self.ax1 = self.create_fig1()
        self.fig2, self.ax2 = self.create_fig2()
        self.fig3, self.ax3 = self.create_fig3()

        self.create_fields()
        self.create_checkboxes([
            ("B.ECI", self.eci_visible, 0.53, 0.3),
            ("B.Body", self.body_visible, 0.53, 0.35),
            ("R.ECI", self.r_eci_visible, 0.53, 0.25),
            ("V.ECI", self.v_eci_visible, 0.53, 0.4),
            ("Sat.Body", self.sat_body_visible, 0.53, 0.45)
        ])

        self.canvas_fig1 = self.create_canvas_figure(self.fig1, self.canvas1)
        self.canvas_fig2 = self.create_canvas_figure(self.fig2, self.canvas2)
        self.canvas_fig3 = self.create_canvas_figure(self.fig3, self.canvas3)

        # Combobox için veri alanı seçeneklerini tanımla
        combobox_options = [
            "Btot_ECI",
            "Btot_ECEF",
            "Btot_Body",
            "Btot_ECEF Magnitude",
            "Btot_ECI Magnitude",
            "Btot_Body Magnitude",
            "Btot_ECEF Normalized",
            "Btot_ECI Normalized",
            "Btot_Body Normalized"
        ]
        # COM port seçimi için combobox (artık otomatik portları yükleyecek)
        available_ports = self.get_available_ports()
        if available_ports:
            self.combobox_port = ttk.Combobox(self.root, values=available_ports, state="readonly", width=5)
            self.combobox_port.set(available_ports[0])  # İlk bulunan portu varsayılan olarak ayarla
        else:
            self.combobox_port = ttk.Combobox(self.root, values=["No Ports Found"], state="readonly", width=5)
            self.combobox_port.set("No Ports Found")  # Eğer port bulunmazsa mesaj göster
        self.combobox_port.place(relx=0.44, rely=0.765, anchor="w") 

        # Tek bir combobox içinde seçenekleri göster
        self.combobox_data = ttk.Combobox(self.root, values=combobox_options, state="readonly", width=10)
        self.combobox_data.set("Select Data Field")  # Varsayılan değeri ayarla
        self.combobox_data.place(relx=0.32, rely=0.765, anchor="w")  # Combobox'ın konumunu ayarla

        # Baud rate seçimi için combobox
        self.combo_values_baud = ["921600", "115200", "256000", "230400", "512000"]
        self.combobox_baud = ttk.Combobox(self.root, values=self.combo_values_baud, state="readonly", width=10)
        self.combobox_baud.set("Baud Rate")  # Set default value
        self.combobox_baud.place(relx=0.38, rely=0.765, anchor="w")


        
    def update_gui(self, index):
        """
        GUI elemanlarını günceller ve yeni değerleri gösterir.
        """
        
        # Eğer durdurulduysa güncellemeyi durdur
        if self.stopped_flag:
            print("GUI update stopped.")  # Debugging print statement
            return
        # Eğer duraklatıldıysa güncellemeyi durdur
        if self.pause_flag:
            print("GUI update paused.")  # Debugging print statement
            return
        
            
        for i in range(3):
            # B.ECEF verilerini güncelleme
            self.entries["B.ECEF ="][i].delete(0, tk.END)
            self.entries["B.ECEF ="][i].insert(0, f"{self.data.Btot_ECEF_data[index, i]:.2f}")
            
            # B.ECI verilerini güncelleme
            self.entries["B.ECI ="][i].delete(0, tk.END)
            self.entries["B.ECI ="][i].insert(0, f"{self.data.Btot_ECI_data[index, i]:.2f}")
            
            # B.Body verilerini güncelleme
            self.entries["B.Body ="][i].delete(0, tk.END)
            self.entries["B.Body ="][i].insert(0, f"{self.data.Btot_body_data[index, i]:.2f}")
    
        # Magnitude değerlerini güncelleme
        self.entries["B.ECEF ="][3].delete(0, tk.END)
        self.entries["B.ECEF ="][3].insert(0, f"{self.data.Btot_ECEF_mag[index, 0]:.2f}")
        
        self.entries["B.ECI ="][3].delete(0, tk.END)
        self.entries["B.ECI ="][3].insert(0, f"{self.data.Btot_ECI_mag[index, 0]:.2f}")
        
        self.entries["B.Body ="][3].delete(0, tk.END)
        self.entries["B.Body ="][3].insert(0, f"{self.data.Btot_body_mag[index, 0]:.2f}")

        self.altitude_data_entry.delete(0, tk.END)  # Önce mevcut metni temizleyin
        self.altitude_data_entry.insert(0, f"{self.data.altitude_data[index]/1000:.2f}")  # Yeni altitude verisini yazdırın (km cinsinden)

        # Eğer daha fazla güncellenecek veri varsa GUI güncellemeye devam eder
        if index < (Constants.NUM_STEPS - 1):
            self.root.after(Constants.INTERVAL_DELAY, self.update_gui, index + 1)
            
    def create_fields(self):
        fields = ["B.ECEF =", "B.ECI =", "B.Body ="]
        self.entries = {}
        for i, field in enumerate(fields):
            button = CTkButton(self.root, text=field, width=70, font=self.roboto_font, anchor=tk.CENTER)
            button.place(relx=0.02, rely=0.8 + i * 0.05, anchor="w")
            self.entries[field] = []
            for j in range(4):
                entry = CTkEntry(self.root, width=75, font=self.roboto_font)
                entry.place(relx=0.08 + j * 0.06, rely=0.8 + i * 0.05, anchor="w")
                self.entries[field].append(entry)

            # Eğer B.Body ise 3 ek entry ve bir checkbox ekle
            if field == "B.Body =":
                # Ek entry'ler, genişlikleri 50, aralarındaki boşluk 0.03 olacak
                for j in range(4, 7):  # İlk 4 entry'den sonra 3 ek entry
                    entry = CTkEntry(self.root, width=50, font=self.roboto_font)
                    entry.place(relx=0.08 + 4 * 0.06 + (j - 4) * 0.04, rely=0.8 + i * 0.05, anchor="w")
                    self.entries[field].append(entry)
                    entry.configure(state=tk.DISABLED)  # İlk başta devre dışı yapıyoruz

                # Checkbox ekle, görünür bir arka plan olmadan
                self.body_additional_entries_checkbox = tk.BooleanVar()
                self.body_additional_entries_checkbox = CTkCheckBox(self.root, text="", fg_color=None, command=self.toggle_body_extra_fields)
                self.body_additional_entries_checkbox.place(relx=0.08 + 4 * 0.06 + 3 * 0.04, rely=0.8 + i * 0.05, anchor="w")

            axes = ["X(μT)", "Y(μT)", "Z(μT)", "Magnitude"]
        for i, axis in enumerate(axes):
            button = CTkButton(self.root, text=axis, width=75, height=10, font=self.roboto_font2)
            button.place(relx=0.08 + i * 0.06, rely=0.765, anchor="w")
            
        # Adding the Start, Pause, Stop buttons under B.Body
        button_start = CTkButton(self.root, fg_color="green", hover_color="darkgreen",font = self.custom_font_fixedsys, text="Start", width=100,
                                 command=lambda: [self.update_gui(0), self.start_animations()])
        button_start.place(relx=0.08, rely=0.8 + len(fields) * 0.05, anchor="w")
    
        # Pause butonunun tanımlanması
        button_pause = CTkButton(self.root, font=self.custom_font_fixedsys, text="Pause", width=100, 
                                command=lambda: self.pause_esp32_communication() if self.import_button_pressed else self.pause_animations())
        button_pause.place(relx=0.16, rely=0.8 + len(fields) * 0.05, anchor="w")

        # Stop butonunun tanımlanması
        button_stop = CTkButton(self.root, fg_color="red", hover_color="darkred", font=self.custom_font_fixedsys, text="Stop", width=100,
                                command=lambda: self.stop_esp32_communication() if self.import_button_pressed else self.stop_animations())
        button_stop.place(relx=0.24, rely=0.8 + len(fields) * 0.05, anchor="w")

        # Adding the Import button next to Stop
        button_import = CTkButton(self.root, text="Import", width=100, fg_color="black",font = self.custom_font_fixedsys, command=self.start_esp32_communication)
        button_import.place(relx=0.32, rely=0.8 + len(fields) * 0.05, anchor="w")

        button_altitude_data = CTkButton(self.root, text="Altitude (km):", width=100, fg_color="#2B2B2B",bg_color="#2B2B2B",border_color="#2B2B2B",font = self.roboto_font)
        button_altitude_data.place(relx=0.02, rely=0.04, anchor="w")

        self.altitude_data_entry = CTkEntry(self.root, width=75, fg_color="#2B2B2B",bg_color="#2B2B2B",border_color="#2B2B2B",font=self.roboto_font)  # İlk 4 entry genişliği 75 olacak
        self.altitude_data_entry.place(relx=0.08, rely=0.04, anchor="w")

  # Import fonksiyonu - Comboboxlardan seçilen değerleri alıp işleyecek    
    def start_esp32_communication(self):
        """
        ESP32 ile olan iletişimi başlatır.
        """
        selected_data = self.combobox_data.get()
        selected_baud = self.combobox_baud.get()
        selected_port = self.combobox_port.get()

        if self.body_additional_entries_checkbox.get():
            selected_data = "Btot_Body"

        if selected_data == "Select Data Field" or selected_baud == "Baud Rate" or selected_port == "Port":
            print("Lütfen tüm alanları doldurunuz.")
            return

        print(f"Selected Data: {selected_data}, Selected Baud Rate: {selected_baud}, Selected Port: {selected_port}")

        # Bayrakları sıfırla
        self.esp32_pause_event.clear()
        self.esp32_stop_event.clear()

        # Import butonunun basıldığını belirtiyoruz
        self.import_button_pressed = True

        # Yeni bir thread başlatarak ESP32 ile iletişimi başlatıyoruz
        esp32_thread = threading.Thread(target=self.send_data_to_esp32, args=(selected_port, selected_baud, selected_data))
        esp32_thread.start()


    def pause_esp32_communication(self):
        """
        ESP32 ile olan iletişimi duraklatır.
        """
        try:
            print("Pausing ESP32 communication...")
            self.esp32_pause_event.set()  # Pause sinyali ver
        except Exception as e:
            print(f"Error occurred while pausing ESP32 communication: {e}")



    def stop_esp32_communication(self):
        """
        ESP32 ile olan iletişimi sıfırlar.
        """
        try:
            print("Stopping ESP32 communication and resetting...")
            self.esp32_stop_event.set()  # Stop sinyali ver
            self.esp32_pause_event.clear()  # Duraklamayı sıfırla
            self.esp32_was_stopped = True  # Stop edildiğini belirle
            self.esp32_paused_frame = 0  # Duraklama satırını sıfırla
            self.import_button_pressed = False  # Import butonunun bayrağını sıfırla
        except Exception as e:
            print(f"Error occurred while stopping ESP32 communication: {e}")
    
    def send_data_to_esp32(self, port, baud_rate, data_type):
        baud_rate = int(baud_rate)  # Baud rate'i int olarak ayarlıyoruz

        data_mapping = {
            "Btot_ECEF": self.data.Btot_ECEF_data / 1000,
            "Btot_ECI": self.data.Btot_ECI_data / 1000,
            "Btot_Body": self.data.Btot_body_data / 1000,
            "Btot_ECEF Magnitude": self.data.Btot_ECEF_mag / 1000,
            "Btot_ECI Magnitude": self.data.Btot_ECI_mag / 1000,
            "Btot_Body Magnitude": self.data.Btot_body_mag / 1000,
            "Btot_ECEF Normalized": self.data.Btot_ECEF_norm,
            "Btot_ECI Normalized": self.data.Btot_ECI_norm,
            "Btot_Body Normalized": self.data.Btot_body_norm
        }

        data_to_send = data_mapping.get(data_type, None)
        if data_to_send is None:
            print(f"Error: Data type '{data_type}' is not valid.")
            return

        try:
            ser = serial.Serial(port, baud_rate)
            time.sleep(2)  # ESP32'nin hazır olmasını bekliyoruz

            if ser.in_waiting > 0:
                startup_message = ser.readline().decode('utf-8').rstrip()
                print(f"Başlangıç mesajı atlandı: {startup_message}")

            # Eğer stop edilmişse en baştan başla
            start_frame = 0 if self.esp32_was_stopped else self.esp32_paused_frame

            # Adaptif zamanlama: her frame INTERVAL_DELAY (ms) arayla gönderilsin; araya giren gecikme ölçülür, bir sonraki gönderim zamanı buna göre hesaplanır
            interval_sec = Constants.INTERVAL_DELAY / 1000.0
            next_send_time = time.time()

            for i, row in enumerate(data_to_send[start_frame:], start=start_frame):
                # Stop kontrolü
                if self.esp32_stop_event.is_set() or not self.import_button_pressed:
                    print("ESP32 communication stopped or not started.")
                    if ser.is_open:
                        ser.close()
                    self.esp32_was_stopped = True
                    return

                # Pause kontrolü
                if self.esp32_pause_event.is_set():
                    print(f"Paused at row {i+1}. Waiting for resume or stop...")
                    self.esp32_paused_frame = i
                    ser.close()
                    return

                # Bu frame'in gönderim zamanı gelene kadar bekle (aynı zaman aralıklarıyla gönderim)
                now = time.time()
                if now < next_send_time:
                    time.sleep(next_send_time - now)

                row_float32 = row.astype(np.float32)
                print(f"Sending row {i+1}: {row}")

                t_send_start = time.time()
                ser.write(row_float32.tobytes())
                ser.flush()

                # ESP32'den yanıt gelene kadar bekle; araya giren süre ölçülür
                timeout = time.time() + 5
                while ser.in_waiting == 0:
                    if time.time() > timeout:
                        print("Error: ESP32 did not respond in time.")
                        if ser.is_open:
                            ser.close()
                        return
                    if self.esp32_stop_event.is_set():
                        if ser.is_open:
                            ser.close()
                        return

                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').rstrip()
                    print(f"Received response: {response}")

                t_send_end = time.time()
                elapsed = t_send_end - t_send_start  # Bu frame'deki gecikme (gönderim + yanıt)
                # Bir sonraki frame hedef zamanı: hedef aralık sonrası
                next_send_time = next_send_time + interval_sec
                if t_send_end > next_send_time:
                    next_send_time = t_send_end  # Çok geride kaldıysak bir sonraki gönderimi şimdiden planla

            if ser.is_open:
                ser.close()  # Bağlantı açık ise kapat
            print("Data successfully sent to ESP32.")
            self.esp32_was_stopped = False  # İşlem başarıyla tamamlandığında sıfırla

        except Exception as e:
            print(f"Error: {e}")
            if ser.is_open:
                ser.close()  # Hata olursa bağlantıyı kapat

               
    def stop_animations(self):
        """
        Tüm animasyonları durdurur ve başlangıç durumuna döndürür.
        """
        try:
            print("Stopping animations and resetting GUI...")  # Debugging print statement
            self.pause_flag = False
            self.stopped_flag = True  # Stop durumunu etkinleştirin
            self.was_stopped = True  # Stop edildiğini belirten bayrağı etkinleştirin
    
            if self.ani_fig1 is not None:
                self.ani_fig1.event_source.stop()
            if self.ani_fig2 is not None:
                self.ani_fig2.event_source.stop()
            if self.ani_fig3 is not None:
                self.ani_fig3.event_source.stop()

    
            # Çizimleri kaldırma: Line, Point ve Label için sıfırlama
            if self.line in self.ax1.lines:
                self.line.remove()  # Çizgiyi tamamen kaldır
            if self.point in self.ax1.collections:
                self.point.remove()  # Noktayı tamamen kaldır
            self.satellite_label.set_text('')  # Etiketi sıfırla
    
            # Çizimleri sıfırlama: Line, Point ve Label için sıfırlama
            self.line.set_data([], [])
            self.point.set_data([], [])
            self.satellite_label.set_position((0, 0))
            self.satellite_label.set_text('')
    
            # Quivers (oklar) sıfırlama
            for quiver in self.quivers:
                if quiver in self.ax2.collections:  # Quiver hala eksende mevcut mu?
                    quiver.remove()
            self.quivers = [
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color='y'),
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color='b'),
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color='r'),
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color='w')
            ]
            for quiver in self.normal_quivers:
                if quiver in self.ax2.collections:

                    quiver.remove()
                
            normal_colors = ['g', 'r', 'm']  # Green for X+, Red for Y+, Magenta for Z+
            
            # Başlangıçta normal vektörler çizilmeyecek (sat_body kontrolüne bağlı)
            self.normal_quivers = [
                self.ax2.quiver(0, 0, 0, 0, 0, 0, color=color) for color in normal_colors
            ]
    
            # Küpü sıfırlama (Cube)
            if hasattr(self, 'cube_collection') and self.cube_collection is not None:
                self.cube_collection.remove()
            rotated_vertices = self.rotate_cube(self.cube_origin, self.data.q_DCM[0])
            self.cube_collection = self.create_cube(self.ax2, rotated_vertices)
    
            if self.line_wx in self.ax3.lines:
                self.line_wx.set_data([], [])
            if self.line_wy in self.ax3.lines:
                self.line_wy.set_data([], [])
            if self.line_wz in self.ax3.lines:
                self.line_wz.set_data([], [])

    
            # GUI girişlerini sıfırlama
            for key in self.entries:
                for entry in self.entries[key]:
                    entry.delete(0, tk.END)
                    entry.insert(0, '')
    
            # CheckBox'ları sıfırlama
            self.eci_visible.set(False)
            self.body_visible.set(False)
            self.r_eci_visible.set(False)
            self.v_eci_visible.set(False)
            self.sat_body_visible.set(False)
            self.body_additional_entries_checkbox = tk.BooleanVar(value=False)
    
            # Yeniden çizim yaparak günceller
            self.draw_figures()
            print("Animations and GUI reset.")  # Debugging print statement
    
        except Exception as e:
            print(f"Error occurred while stopping animations: {e}")
           
    def pause_animations(self):
        """
        Tüm animasyonları ve GUI güncellemelerini duraklatır.
        """
        try:
            print("Pausing animations and GUI updates...")  # Debugging print statement
            
            # Duraklatma bayrağını aktif hale getir
            self.pause_flag = True
            self.was_stopped = False  # Pause, stop anlamına gelmez
            self.stopped_flag = False  # Stop durumunu etkinleştirin

        
            # Animasyonları durdur ve mevcut kareyi kaydet
            self.current_frame_fig1 = self.ani_fig1.frame_seq.__next__()
            self.current_frame_fig2 = self.ani_fig2.frame_seq.__next__()
            self.current_frame_fig3 = self.ani_fig3.frame_seq.__next__()
        
            self.ani_fig1.event_source.stop()
            self.ani_fig2.event_source.stop()
            self.ani_fig3.event_source.stop()
        
            print("Animations and GUI updates paused.")  # Debugging print statement
        except Exception as e:
            print(f"Error occurred while pausing: {e}")
    
        
    def start_animations(self):
                    
        try:
            print("Starting animations...")
    
            # Pause edilmişse çizimleri temizleyip kaldığı yerden devam et
            if self.pause_flag:
                print("Resuming from pause...")  # Debugging print statement
                start_frame_fig1 = getattr(self, 'current_frame_fig1', 0)
                start_frame_fig2 = getattr(self, 'current_frame_fig2', 0)
                start_frame_fig3 = getattr(self, 'current_frame_fig3', 0)
    
                # Pause edilmişse çizimleri kaldır
                if hasattr(self, 'line'):
                    try:
                        self.line.remove()  # Çizgiyi kaldır
                        print("Line removed.")
                    except ValueError:
                        pass  # Eğer çizim ekseninde değilse hatayı yoksay
                if hasattr(self, 'point'):
                    try:
                        self.point.remove()  # Noktayı kaldır
                        print("Point removed.")
                    except ValueError:
                        pass  # Eğer nokta ekseninde değilse hatayı yoksay
                self.satellite_label.set_text('')  # Etiketi sıfırla
                print("Cleared old lines, points, and labels after pause.")
                if hasattr(self, 'quivers'):
                     for quiver in self.quivers:
                         try:
                             quiver.remove()  # Quiver'ları kaldır
                             print("Quiver removed.")
                         except ValueError:
                             pass  # Eğer quiver eksende değilse hatayı yoksay
                if hasattr(self, 'normal_quivers'):
                     for quiver in self.normal_quivers:
                         try:
                             quiver.remove()  # Normal quiver'ları kaldır
                             print("Normal quivers removed.")
                         except ValueError:
                             pass  # Eğer quiver eksende değilse hatayı yoksay
                    
            # Eğer stop edilmişse animasyonu baştan başlat ve çizimleri temizle
            elif self.was_stopped:
                print("Starting from the beginning after stop...")  # Debugging print statement
                start_frame_fig1 = 0
                start_frame_fig2 = 0
                start_frame_fig3 = 0
                
                # Eğer stop edildiğinde çizimler ve etiketler varsa temizle
                if hasattr(self, 'line'):
                    try:
                        self.line.remove()  # Çizgiyi kaldır
                        print("Line removed.")
                    except ValueError:
                        pass  # Eğer çizim ekseninde değilse hatayı yoksay
                if hasattr(self, 'point'):
                    try:
                        self.point.remove()  # Noktayı kaldır
                        print("Point removed.")
                    except ValueError:
                        pass  # Eğer nokta ekseninde değilse hatayı yoksay
                self.satellite_label.set_text('')  # Etiketi sıfırla
                
                if hasattr(self, 'quivers'):
                    for quiver in self.quivers:
                        try:
                            quiver.remove()  # Quiver'ları kaldır
                            print("Quiver removed.")
                        except ValueError:
                            pass  # Eğer quiver eksende değilse hatayı yoksay
                if hasattr(self, 'normal_quivers'):
                    for quiver in self.normal_quivers:
                        try:
                            quiver.remove()  # Normal quiver'ları kaldır
                            print("Normal quivers removed.")
                        except ValueError:
                            pass  # Eğer quiver eksende değilse hatayı yoksay
    
            # Eğer ne stop edilmiş ne de pause edilmişse animasyonu baştan başlat
            else:
                print("Starting from the beginning...")  # Debugging print statement
                start_frame_fig1 = 0
                start_frame_fig2 = 0
                start_frame_fig3 = 0
    
            # Pause ve stop bayraklarını sıfırla
            self.pause_flag = False
            self.stopped_flag = False
    
            # Initialize the figures before starting the animation
            self.init_fig1()
            self.init_fig2()
            self.init_fig3()
    
            # Start animations from the current or initial frame
            self.ani_fig1 = FuncAnimation(
                self.fig1, 
                self.update_fig1, 
                frames=range(start_frame_fig1, len(self.data.latitude_data)), 
                init_func=self.init_fig1, 
                blit=False, interval=Constants.INTERVAL_DELAY,
                fargs=(self.data.longitude_data, self.data.latitude_data, self.line, self.point, self.satellite_label),repeat = False,
            )
    
            self.ani_fig2 = FuncAnimation(
                self.fig2, 
                self.update_fig2, 
                frames=range(start_frame_fig2, len(self.data.latitude_data)), 
                init_func=self.init_fig2, 
                blit=False, interval=Constants.INTERVAL_DELAY,repeat = False,
                fargs=(self.data,)
            )
    
            self.ani_fig3 = FuncAnimation(
                self.fig3, 
                self.update_fig3, 
                frames=range(start_frame_fig3, len(self.data.latitude_data)), 
                blit=False, interval=Constants.INTERVAL_DELAY, repeat = False
            )
    
            # Explicitly start the animations
            self.ani_fig1.event_source.start()
            self.ani_fig2.event_source.start()
            self.ani_fig3.event_source.start()
    
            self.draw_figures()
    
            # GUI güncellemelerini yeniden başlat
            self.update_gui(0)  # Başlangıç index'i 0 olarak ayarlanır
    
            print("Animations started.")
        except Exception as e:
            print(f"Error occurred: {e}")

    def init_fig1(self):
        self.line, = self.ax1.plot([], [], color='white', linewidth=1.5)
        self.point, = self.ax1.plot([], [], marker='o', color='white')
        self.satellite_label = self.ax1.text(0, 0, '', color='white', fontsize=8, ha='right', fontproperties=roboto_prop)
        return self.line, self.point, self.satellite_label

    def update_fig1(self, frame, longitude_data, latitude_data, line, point, satellite_label):
        self.line.set_data(longitude_data[:frame], latitude_data[:frame])
        self.point.set_data(longitude_data[frame], latitude_data[frame])
        self.satellite_label.set_position((longitude_data[frame], latitude_data[frame]))
        self.satellite_label.set_text('Taurus  ')
        return self.line, self.point, self.satellite_label

    def init_fig2(self):
        # Initialize the quivers with empty data
        if hasattr(self, 'cube_collection') and self.cube_collection is not None:
            self.cube_collection.remove()  # Önceki küpü kaldır
    
        self.quivers = [
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color='y', label='B_ECI'),
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color='b', label='B_Body'),
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color='#FFA500', label='R_ECI'),
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color='w', label='V_ECI')
        ]
    
        # Initialize the cube and store its reference
        rotated_vertices = self.rotate_cube(self.cube_origin, self.data.q_DCM[0])
        self.cube_collection = self.create_cube(self.ax2, rotated_vertices)
        
        # Create and add normal vectors for X+, Y+, Z+
        normals = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # X+, Y+, Z+ yönleri
        normal_colors = ['g', 'r', 'm']  # Green for X+, Red for Y+, Magenta for Z+
        
        # Başlangıçta normal vektörler çizilmeyecek (sat_body kontrolüne bağlı)
        self.normal_quivers = [
            self.ax2.quiver(0, 0, 0, 0, 0, 0, color=color) for color in normal_colors
        ]
        
        # Set up the legend
        self.legend_labels = ['B_ECI', 'B_Body', 'R_ECI', 'V_ECI']
        self.legend_colors = ['y', 'b', '#FFA500', 'w']
        self.legend_handles = [plt.Line2D([0], [0], color=color, lw=4) for color in self.legend_colors]
        self.legend = self.ax2.legend(handles=self.legend_handles, labels=self.legend_labels, loc='upper right', fontsize=10, prop=roboto_prop, bbox_to_anchor=(1.1, 1.05))
        plt.setp(self.legend.get_texts(), color='#03A062')
        
        # Change the background color of the right-side legend
        self.legend.get_frame().set_facecolor('#f0f0f0')  # Açık gri arka plan
        self.legend.get_frame().set_edgecolor('#000000')  # Siyah çerçeve
        
        # Set up the left-side legend for SatBodyX, SatBodyY, SatBodyZ
        satbody_labels = ['SatBodyX', 'SatBodyY', 'SatBodyZ']
        satbody_colors = ['g', 'r', 'm']  # Green, Red, Magenta
        satbody_handles = [plt.Line2D([0], [0], color=color, lw=4) for color in satbody_colors]
        
        # Legend sol tarafa yerleştirilecek
        self.satbody_legend = self.ax2.legend(handles=satbody_handles, labels=satbody_labels, loc='upper left', fontsize=10, prop=roboto_prop, bbox_to_anchor=(-0.1, 1.05))
        plt.setp(self.satbody_legend.get_texts(), color='#03A062')
        
        # Change the background color of the left-side legend
        self.satbody_legend.get_frame().set_facecolor('#f0f0f0')  # Açık gri arka plan
        self.satbody_legend.get_frame().set_edgecolor('#000000')  # Siyah çerçeve
        
        # Add the legends to the plot (hem sağdaki hem soldaki)
        self.ax2.add_artist(self.legend)  # Sağdaki legend
        self.ax2.add_artist(self.satbody_legend)  # Soldaki legend
   
        return self.quivers
 
    def update_fig2(self, frame, data):
        # Remove the existing quivers
        for quiver in self.quivers:
            quiver.remove()
            
        for quiver in self.normal_quivers:
            quiver.remove()
    
        # Update quiver for Btot_ECI
        if self.eci_visible.get():
            self.quivers[0] = self.ax2.quiver(0, 0, 0, 
                                              data.Btot_ECI_norm[frame, 0], 
                                              data.Btot_ECI_norm[frame, 1], 
                                              data.Btot_ECI_norm[frame, 2], 
                                              color='y', label='B_ECI')
        else:
            self.quivers[0] = self.ax2.quiver([], [], [], [], [], [])
    
        # Update quiver for Btot_body
        if self.body_visible.get():
            self.quivers[1] = self.ax2.quiver(0, 0, 0, 
                                              data.Btot_body_norm[frame, 0], 
                                              data.Btot_body_norm[frame, 1], 
                                              data.Btot_body_norm[frame, 2], 
                                              color='b', label='B_Body')
        else:
            self.quivers[1] = self.ax2.quiver([], [], [], [], [], [])
            
        # Update quiver for R_ECI
        if self.r_eci_visible.get():
            self.quivers[2] = self.ax2.quiver(0, 0, 0, 
                                              data.R_ECI_norm[frame, 0], 
                                              data.R_ECI_norm[frame, 1], 
                                              data.R_ECI_norm[frame, 2], 
                                              color='#FFA500', label='R_ECI')
        else:
            self.quivers[2] = self.ax2.quiver([], [], [], [], [], []) 
            
        # Update quiver for V_ECI
        if self.v_eci_visible.get():
            self.quivers[3] = self.ax2.quiver(0, 0, 0, 
                                              data.V_ECI_norm[frame, 0], 
                                              data.V_ECI_norm[frame, 1], 
                                              data.V_ECI_norm[frame, 2], 
                                              color='w', label='V_ECI')
        else:
            self.quivers[3] = self.ax2.quiver([], [], [], [], [], [])
    
        # Update cube's rotation based on DCM
        if hasattr(self, 'cube_collection') and self.cube_collection is not None:
            self.cube_collection.remove()  # Önceki küpü kaldır
    
        rotated_vertices = self.rotate_cube(self.cube_origin, data.q_DCM[frame])
        self.cube_collection = self.create_cube(self.ax2, rotated_vertices)  # Yeni küp oluştur
        
        # Checkbox'a göre normal vektörleri göster
        if self.sat_body_visible.get():  # sat_body checkbox'u etkin mi?
            # Update the quivers for X+, Y+, Z+ directions
            normals = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # X+, Y+, Z+ yönleri
            normal_colors = ['g', 'r', 'm']  # Green for X+, Red for Y+, Magenta for Z+
            
            self.normal_quivers = [
                self.update_quiver(self.rotate_cube(norm, data.q_DCM[frame]), color) for norm, color in zip(normals, normal_colors)
            ]
        else:
            # Eğer checkbox kapalıysa boş vektörler çiz (quiver kaldır)
            self.normal_quivers = [
                self.ax2.quiver([], [], [], [], [], []) for _ in range(3)
            ]

        self.canvas_fig2.draw()
    
        return self.quivers

    def update_quiver(self, norm_data, color):
        return self.ax2.quiver(0, 0, 0, norm_data[0], norm_data[1], norm_data[2], color=color)
    
    def rotate_cube(self, vertices, dcm):
        return dcm @ vertices.T

    def create_cube(self, ax, vertices):
        vertices = vertices.T
        faces = [[vertices[j] for j in [0, 1, 2, 3]], 
                 [vertices[j] for j in [4, 5, 6, 7]],
                 [vertices[j] for j in [0, 3, 7, 4]], 
                 [vertices[j] for j in [1, 2, 6, 5]],
                 [vertices[j] for j in [0, 1, 5, 4]], 
                 [vertices[j] for j in [2, 3, 7, 6]]]
        
        face_colors = ['cyan', 'magenta', 'yellow', 'green', 'blue', 'red']  # Her yüzeye farklı renk
    
        collection = Poly3DCollection(faces, facecolors=face_colors, linewidths=1, edgecolors='r')
        ax.add_collection3d(collection)
        return collection

    def init_fig3(self):

        self.ax3.set_xlim(0, len(self.data.angular_vel))
        self.ax3.set_ylim(np.min(self.data.angular_vel), np.max(self.data.angular_vel))

        # Eğer var olan bir legend varsa kaldırma işlemi
        if not hasattr(self, 'legend_created'):
            self.line_wx, = self.ax3.plot([], [], color='r', label=r'$\omega_x$')
            self.line_wy, = self.ax3.plot([], [], color='g', label=r'$\omega_y$')
            self.line_wz, = self.ax3.plot([], [], color='b', label=r'$\omega_z$')
    
            # Legend yalnızca bir kez oluşturulur
            self.ax3.legend(loc='upper right', fontsize=10, prop=roboto_prop)
            self.legend_created = True  # Legend oluşturulduğunda bayrağı işaretle
        return self.line_wx, self.line_wy, self.line_wz

    def update_fig3(self, frame):
        x_data = np.arange(frame)
        self.line_wx.set_data(x_data, self.data.angular_vel[:frame, 0])
        self.line_wy.set_data(x_data, self.data.angular_vel[:frame, 1])
        self.line_wz.set_data(x_data, self.data.angular_vel[:frame, 2])
        return self.line_wx, self.line_wy, self.line_wz

    def draw_figures(self):
        self.canvas_fig1.draw()
        self.canvas_fig2.draw()
        self.canvas_fig3.draw()
            
# Run the GUI application
if __name__ == "__main__":
    app = SpacecraftGUI()

    app.mainloop()