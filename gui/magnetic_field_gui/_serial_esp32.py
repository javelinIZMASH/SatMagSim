"""ESP32 serial communication: port discovery, start/pause/stop, send_data_to_esp32."""

import time
import threading
import numpy as np
import serial
import serial.tools.list_ports

from config.constants import Constants


class MagneticFieldGUISerialMixin:
    """Mixin: get_available_ports, start_esp32_communication, pause/stop_esp32_communication, send_data_to_esp32."""

    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def start_esp32_communication(self):
        selected_data = self.combobox_data.get()
        selected_baud = self.combobox_baud.get()
        selected_port = self.combobox_port.get()

        if self.body_additional_entries_checkbox.get():
            selected_data = "Btot_Body"

        if (
            selected_data == "Select Data Field"
            or selected_baud == "Baud Rate"
            or selected_port == "Port"
        ):
            print("Lütfen tüm alanları doldurunuz.")
            return

        print(f"Selected Data: {selected_data}, Baud: {selected_baud}, Port: {selected_port}")
        self.esp32_pause_event.clear()
        self.esp32_stop_event.clear()
        self.import_button_pressed = True
        esp32_thread = threading.Thread(
            target=self.send_data_to_esp32,
            args=(selected_port, selected_baud, selected_data),
        )
        esp32_thread.start()

    def pause_esp32_communication(self):
        try:
            print("Pausing ESP32 communication...")
            self.esp32_pause_event.set()
        except Exception as e:
            print(f"Error pausing ESP32 communication: {e}")

    def stop_esp32_communication(self):
        try:
            print("Stopping ESP32 communication and resetting...")
            self.esp32_stop_event.set()
            self.esp32_pause_event.clear()
            self.esp32_was_stopped = True
            self.esp32_paused_frame = 0
            self.import_button_pressed = False
        except Exception as e:
            print(f"Error stopping ESP32 communication: {e}")

    def send_data_to_esp32(self, port, baud_rate, data_type):
        baud_rate = int(baud_rate)
        data_mapping = {
            "Btot_ECEF": self.data.Btot_ECEF_data / 1000,
            "Btot_ECI": self.data.Btot_ECI_data / 1000,
            "Btot_Body": self.data.Btot_body_data / 1000,
            "Btot_ECEF Magnitude": self.data.Btot_ECEF_mag / 1000,
            "Btot_ECI Magnitude": self.data.Btot_ECI_mag / 1000,
            "Btot_Body Magnitude": self.data.Btot_body_mag / 1000,
            "Btot_ECEF Normalized": self.data.Btot_ECEF_norm,
            "Btot_ECI Normalized": self.data.Btot_ECI_norm,
            "Btot_Body Normalized": self.data.Btot_body_norm,
        }
        data_to_send = data_mapping.get(data_type)
        if data_to_send is None:
            print(f"Error: Data type '{data_type}' is not valid.")
            return

        ser = None
        try:
            ser = serial.Serial(port, baud_rate)
            time.sleep(2)
            if ser.in_waiting > 0:
                startup_message = ser.readline().decode("utf-8").rstrip()
                print(f"Başlangıç mesajı atlandı: {startup_message}")

            start_frame = 0 if self.esp32_was_stopped else self.esp32_paused_frame
            interval_sec = Constants.INTERVAL_DELAY / 1000.0
            next_send_time = time.time()

            for i, row in enumerate(data_to_send[start_frame:], start=start_frame):
                if self.esp32_stop_event.is_set() or not self.import_button_pressed:
                    print("ESP32 communication stopped or not started.")
                    if ser.is_open:
                        ser.close()
                    self.esp32_was_stopped = True
                    return

                if self.esp32_pause_event.is_set():
                    print(f"Paused at row {i + 1}. Waiting for resume or stop...")
                    self.esp32_paused_frame = i
                    ser.close()
                    return

                now = time.time()
                if now < next_send_time:
                    time.sleep(next_send_time - now)

                row_float32 = row.astype(np.float32)
                print(f"Sending row {i + 1}: {row}")

                t_send_start = time.time()
                ser.write(row_float32.tobytes())
                ser.flush()

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
                    response = ser.readline().decode("utf-8").rstrip()
                    print(f"Received response: {response}")

                t_send_end = time.time()
                elapsed = t_send_end - t_send_start
                next_send_time = next_send_time + interval_sec
                if t_send_end > next_send_time:
                    next_send_time = t_send_end

            if ser.is_open:
                ser.close()
            print("Data successfully sent to ESP32.")
            self.esp32_was_stopped = False
        except Exception as e:
            print(f"Error: {e}")
            if ser is not None and ser.is_open:
                ser.close()
