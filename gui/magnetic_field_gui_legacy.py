import tkinter as tk
import time
import threading
import numpy as np
import serial
import serial.tools.list_ports
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import customtkinter as ctk
from customtkinter import CTkButton, CTkEntry, CTkFont, CTkCheckBox
from config.constants import Constants
from config.theme import roboto_prop

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
                # Bir sonraki frame hedef zamanı: hedef aralık sonrası (gecikmeyi telafi etmek için sabit periyot kullanıyoruz)
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

