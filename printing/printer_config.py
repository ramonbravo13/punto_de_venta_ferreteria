import json
import os

CONFIG_FILE = "printer_config.json"

class PrinterConfig:
    def __init__(self):
        self.printer_name = ""
        self.connection_type = "windows"  # windows, serial, bluetooth
        self.label_width_mm = 58
        self.label_height_mm = 30
        self.dpi = 203
        self.margin_left_mm = 2
        self.margin_right_mm = 2
        self.margin_top_mm = 2
        self.margin_bottom_mm = 2
        self.com_port = "COM1"
        self.baud_rate = 9600
        
        self.load()
        
    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.printer_name = data.get("printer_name", self.printer_name)
                    self.connection_type = data.get("connection_type", self.connection_type)
                    self.label_width_mm = data.get("label_width_mm", self.label_width_mm)
                    self.label_height_mm = data.get("label_height_mm", self.label_height_mm)
                    self.dpi = data.get("dpi", self.dpi)
                    self.margin_left_mm = data.get("margin_left_mm", self.margin_left_mm)
                    self.margin_right_mm = data.get("margin_right_mm", self.margin_right_mm)
                    self.margin_top_mm = data.get("margin_top_mm", self.margin_top_mm)
                    self.margin_bottom_mm = data.get("margin_bottom_mm", self.margin_bottom_mm)
                    self.com_port = data.get("com_port", self.com_port)
                    self.baud_rate = data.get("baud_rate", self.baud_rate)
            except Exception as e:
                print(f"Error loading printer config: {e}")

    def save(self):
        data = {
            "printer_name": self.printer_name,
            "connection_type": self.connection_type,
            "label_width_mm": self.label_width_mm,
            "label_height_mm": self.label_height_mm,
            "dpi": self.dpi,
            "margin_left_mm": self.margin_left_mm,
            "margin_right_mm": self.margin_right_mm,
            "margin_top_mm": self.margin_top_mm,
            "margin_bottom_mm": self.margin_bottom_mm,
            "com_port": self.com_port,
            "baud_rate": self.baud_rate
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving printer config: {e}")
