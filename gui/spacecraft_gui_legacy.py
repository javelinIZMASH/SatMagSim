"""Main spacecraft parameters window: Keplerian, run sim, deploy, magnetic field viz."""

import math
import os
import threading
import time
import datetime

import numpy as np
import pymap3d
import customtkinter as ctk
import tkinter as tk
import ctypes
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from PIL import Image, ImageTk

from customtkinter import (
    CTk,
    CTkLabel,
    CTkProgressBar,
    CTkFrame,
    CTkButton,
    CTkEntry,
    CTkFont,
    CTkCheckBox,
)
from geopack import geopack, t89
from spacepy import coordinates as coord
from spacepy.time import Ticktock

from config.theme import script_dir, roboto_prop
from config.constants import Constants
from utils.quaternion import q_to_DCM, euler_from_quaternion, get_quaternion_from_euler
from core.gmat_sim import satellites, gator, initialize_data_structures
from core.satellite_simulator import SatelliteSimulator, MagneticFieldData

# Shared data structures for simulation and MagneticFieldGUI
data_magnetic, data_dyn_kin, data_PV, data_geodetic = initialize_data_structures(satellites)


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
        self.geometry("1500x800")

        # Center the window on the screen
        self.update_idletasks()
        # Update width and height for centering the window
        width = 1500
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2) - 15
        y = (self.winfo_screenheight() // 2) - (height // 2) - 40
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
        self.create_deployment_properties_frame(self.left_frame)
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
        image_path = os.path.join(script_dir, "gumushlogo.png")
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
        total_steps = int(num_steps / step)
        current_step = 0
    
        # Başlangıç zamanı
        start_time_sim = time.time()
    
        # Simülasyon döngüsü
        for x in range(int(num_steps / step)):
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
            initial_ut += Constants.STEP
    
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
        from gui.magnetic_field_gui import MagneticFieldGUI
        root = CTk()
        root.title("Magnetic Field Visualization")
        roboto_font_path = os.path.join(script_dir, "Roboto-Regular.ttf")
        if not os.path.isfile(roboto_font_path):
            roboto_font_path = "C:/Users/GumushAerospace/Desktop/taurus/Roboto-Regular.ttf"
        if os.path.isfile(roboto_font_path):
            ctypes.windll.gdi32.AddFontResourceW(roboto_font_path)
        root.state("zoomed")
        root.resizable(False, False)
        data = MagneticFieldData(data_geodetic, data_magnetic, data_PV, data_dyn_kin)
        app2 = MagneticFieldGUI(root, data)
        app2.draw_figures()
        root.mainloop()      
    
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

            # --- Cyan yüzeye dik olacak şekilde bir yön vektörü oluştur ---
            cyan_normal = np.dot(dcm, np.array([0, 0, -1]))  # Cyan yüzeyine dik vektör

            # --- Cyan yüzeyine dik vektörün azimuth ve elevation açılarını hesapla ---
            azimuth, elevation = self.cartesian_to_spherical(cyan_normal[0], cyan_normal[1], cyan_normal[2])

            Constants.impulsive_spherical_params["azimuth"] = azimuth
            Constants.impulsive_spherical_params["elevation"] = elevation

            print(f"Azimuth: {azimuth:.2f}°, Elevation: {elevation:.2f}°")

            # --- Azimuth ve elevation açılarına göre yeni bir vektör hesapla ---
            vx = np.sin(np.radians(elevation)) * np.cos(np.radians(azimuth))
            vy = np.sin(np.radians(elevation)) * np.sin(np.radians(azimuth))
            vz = np.cos(np.radians(elevation))

            # --- İki vektörü normalize et ---
            cyan_normal /= np.linalg.norm(cyan_normal)
            new_vector = np.array([vx, vy, vz])
            new_vector /= np.linalg.norm(new_vector)

            # --- İki vektör arasındaki farkı hesapla ve print et ---
            vector_diff = cyan_normal - new_vector
            diff_norm = np.linalg.norm(vector_diff)  # Vektör farkının büyüklüğü
            print(f"Cyan Normal: {cyan_normal}")
            print(f"New Vector (from azimuth/elevation): {new_vector}")
            print(f"Difference between vectors: {vector_diff}")
            print(f"Norm of difference: {diff_norm}")
            
            # Cyan yüzeye dik vektörü çizdir
            ax2.quiver(0, 0, 0, cyan_normal[0], cyan_normal[1], cyan_normal[2], color='white', linewidth=2, arrow_length_ratio=0.1, label='Cyan Normal')

            # Azimuth ve elevation ile oluşturulan vektörü çizdir
            ax2.quiver(0, 0, 0, new_vector[0], new_vector[1], new_vector[2], color='red', linewidth=2, arrow_length_ratio=0.01, label='Azimuth/Elevation Vector')

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

    # Küresel koordinatlara dönüşüm (Kartezyen'den küresel'e)
    # Küresel koordinatlara dönüşüm (Kartezyen'den küresel'e)
    def cartesian_to_spherical(self, x, y, z):
        r = np.sqrt(x**2 + y**2 + z**2)  # Vektörün büyüklüğü
        elevation = math.degrees(np.arccos(z / r))  # θ açısı, polar angle
        azimuth = math.degrees(np.arctan2(y, x))   # φ açısı, azimuth
        
        return azimuth, elevation



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
        frame2.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    
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
                
    def update_keplerian_elements(self):
        """
        Updates the Keplerian elements in the GUI with the latest values from Constants.SATELLITE_PARAMS.
        """
        # Güncellenen değerleri Entry alanlarına aktar
        self.semi_major_axis_entry.delete(0, 'end')
        self.semi_major_axis_entry.insert(0, Constants.SATELLITE_PARAMS["sma"])
    
        self.ecc_entry.delete(0, 'end')
        self.ecc_entry.insert(0, Constants.SATELLITE_PARAMS["ecc"])
    
        self.inc_entry.delete(0, 'end')
        self.inc_entry.insert(0, Constants.SATELLITE_PARAMS["inc"])
    
        self.ra_entry.delete(0, 'end')
        self.ra_entry.insert(0, Constants.SATELLITE_PARAMS["ra"])
    
        self.aop_entry.delete(0, 'end')
        self.aop_entry.insert(0, Constants.SATELLITE_PARAMS["aop"])
    
        self.ta_entry.delete(0, 'end')
        self.ta_entry.insert(0, Constants.SATELLITE_PARAMS["ta"])
        

    def create_physical_properties_frame(self, parent):
        frame3 = CTkFrame(parent)
        frame3.grid(row=2, column=0, padx=10, pady=5, sticky="w")
    
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

    def create_deployment_properties_frame(self, parent):
        # Yeni frame oluşturuluyor
        frame5 = CTkFrame(parent)
        frame5.grid(row=4, column=0, padx=10, pady=10, sticky="w")  # Aerodynamic frame'in altına konumlandırılıyor

        # Başlık butonu
        title = CTkButton(frame5, text="Deployment Scenario", font=self.custom_font)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Buton ve entry widget'ları için etiketler ve varsayılan değerler
        labels = ["Before Seperation (sec)", "Deployment Timer (min)"]
        default_values = [Constants.SEPERATION_TIME, Constants.DEPLOYMENT_TIMER]  # Varsayılan değerler başlangıçta sıfır

        for i, (label, default_value) in enumerate(zip(labels, default_values)):
            CTkButton(frame5, text=label, font=self.custom_font).grid(row=i+1, column=0, sticky="ew")

            # Entry widget'larını self ile tanımlıyoruz
            if label == "Before Seperation (sec)":
                self.seperation_entry = CTkEntry(frame5, width=200, font=self.custom_font)
                self.seperation_entry.grid(row=i+1, column=1)
                self.seperation_entry.insert(0, default_value)
            elif label == "Deployment Timer (min)":
                self.deployment_timer_entry = CTkEntry(frame5, width=200, font=self.custom_font)
                self.deployment_timer_entry.grid(row=i+1, column=1)
                self.deployment_timer_entry.insert(0, default_value)


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

        # Add grid configuration to allow responsiveness
        self.progress_frame.grid_columnconfigure(0, weight=1)  # Progress bar column stretches
        self.progress_frame.grid_columnconfigure(1, weight=0)  # Step label takes fixed space
        self.progress_frame.grid_columnconfigure(2, weight=0)  # File label takes fixed space

        # Add progress bar spanning across both frames
        self.progress_bar = CTkProgressBar(self.progress_frame, width=750)
        self.progress_bar.grid(row=0, column=0, pady=(1, 1), sticky="ew")  # Progress bar ile üstündeki label arasındaki boşluk azaltıldı

        # Create label for displaying percentage in the center of the progress bar with a smaller font size
        self.progress_label = CTkLabel(self.progress_frame, text="0.0%", font=CTkFont(family="Roboto", size=9))  # Font size reduced to 9
        self.progress_label.grid(row=0, column=0, sticky="n")

        # Add label to display Step / Num_Step to the right of the progress bar
        self.step_label = CTkLabel(self.progress_frame, text="0 / 0", font=CTkFont(family="Roboto", size=9), anchor="e")  # Step/Num_Step label with right alignment
        self.step_label.grid(row=0, column=1, padx=(10, 10), sticky="ns")  # Positioned to the right of the progress bar with padding

        # Add label for file saved message (initially empty)
        self.progress_file_label = CTkLabel(self.progress_frame, text="", font=CTkFont(family="Roboto", size=9))
        self.progress_file_label.grid(row=0, column=2, padx=(10, 10), sticky="wns")  # Adjust padding here as needed

        # Set initial value for demonstration (this will be dynamic later)
        self.update_progress(0.0, step=0, num_step=0)

    # Function to open ImpulsiveBurn window in a new Toplevel window# Function to open ImpulsiveBurn window in a new Toplevel window
    def open_deployment_window(self):
        from gui.impulsive_burn_gui import ImpulsiveBurnGUI
        burn_window = ctk.CTkToplevel(self)
        ImpulsiveBurnGUI(burn_window, self)
        
    # Function to create the control buttons
    def create_control_buttons(self):
        # Butonları progress_frame içinde en sağa hizalayalım
        button_frame = CTkFrame(self.progress_frame)  # self.progress_frame kullanılıyor
        button_frame.grid(row=0, column=2, padx=(200, 5), pady=(0, 0), sticky="e")  # Frame sağa hizalanmış
    
        # Butonlar için genişlik ve yükseklik ayarları
        button_width = 100
        button_height = 20  # Progress bar yüksekliği ile uyumlu
        # Buton çerçevesi için grid yapılandırması (her buton için ayrı sütun)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)
        button_frame.grid_columnconfigure(4, weight=1)
        # Deploy butonu (Next butonunun soluna gelecek)
        self.deployment_button = CTkButton(button_frame, font=self.custom_font_fixedsys, text="Deploy", width=button_width, height=button_height, command=self.open_deployment_window)
        self.deployment_button.grid(row=0, column=0, padx=(5, 5), pady=(5, 0))  # Sol tarafa hizalanır

        # next button (Solda boşluk için padx ayarlandı)
        self.next_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Next", width=button_width, height=button_height,fg_color="red", hover_color="darkred", state="disabled", command = self.start_gui)
        self.next_button.grid(row=0, column=1, padx=(5, 5), pady=(5, 0))  # Solda 5 birim boşluk, buton arası 5 birim
    
    
        # Cancel button (Solda boşluk için padx ayarlandı)
        self.cancel_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Cancel", width=button_width, height=button_height, command=self.close_window)
        self.cancel_button.grid(row=0, column=2, padx=(5, 5), pady=(5, 0))  # Solda 5 birim boşluk, buton arası 5 birim
    
        # Apply button (Buton aralarında boşluk ayarlandı)
        self.apply_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Apply", width=button_width, height=button_height, command=self.apply_values)
        self.apply_button.grid(row=0, column=3, padx=(5, 5), pady=(5, 0))  # Solda ve sağda 5 birim boşluk
    
        # Run button with green background (Sağda boşluk için padx ayarlandı)
        self.run_button = CTkButton(button_frame,font = self.custom_font_fixedsys, text="Run", width=button_width, height=button_height, fg_color="green", hover_color="darkgreen", command=self.start_simulation_thread)
        self.run_button.grid(row=0, column=4, padx=(5, 5), pady=(5, 0))  # Sağda 5 birim boşluk

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
            Constants.TRUE_ANOMALIES = float(self.ta_entry.get())
            Constants.NUM_STEPS = int(self.simulation_time_entry.get())
            Constants.STEP = int(self.time_step_entry.get())
            Constants.INTERVAL_DELAY = int(self.interval_entry.get())
            Constants.RESOLUTION = int(self.resolution_entry.get())
            Constants.DEPLOYMENT_TIMER = int(self.deployment_timer_entry.get())
            Constants.SEPERATION_TIME = int(self.seperation_entry.get())
            # Seperation Time must be less than 60 seconds
            if Constants.SEPERATION_TIME > 60:
                raise ValueError("Seperation Time Must be less than 1 min")
            else:
                self.progress_file_label.configure(text="")  # Clear any previous error message

            # Deployment Timer cannot exceed half of NUM_STEP
            if Constants.DEPLOYMENT_TIMER * 60 > (Constants.NUM_STEPS / 2):
                raise ValueError("Deployment Timer cannot exceed half of NUM_STEP")
            else:
                self.progress_file_label.configure(text="")  # Clear any previous error message
            
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

# SatelliteSimulator and MagneticFieldData imported from core.satellite_simulator