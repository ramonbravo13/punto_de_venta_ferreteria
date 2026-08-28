import win32print
import os
import json
import textwrap
import threading
from datetime import datetime

CONFIG_FILE = "printer_config.json"

class PrinterConfigManager:
    def __init__(self):
        self.config = {
            "printer_name": "",
            "paper_width": 58,  # 58 o 80
            "copies": 1,
            "auto_cut": True,
            "cash_drawer": True
        }
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Error loading printer config: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving printer config: {e}")

class TicketPrinter:
    def __init__(self):
        self.config_manager = PrinterConfigManager()
        
    def get_config(self):
        return self.config_manager.config
        
    def set_config(self, key, value):
        self.config_manager.config[key] = value
        self.config_manager.save()

    def obtener_impresoras(self):
        try:
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            return [printer[2] for printer in printers]
        except Exception as e:
            print(f"Error enumerando impresoras: {e}")
            return []

    def _validate_printer_status(self, printer_name: str):
        try:
            printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            if printer_name not in printers:
                raise Exception(f"La impresora '{printer_name}' no existe o fue desinstalada de Windows.")

            hprinter = win32print.OpenPrinter(printer_name)
            try:
                printer_info = win32print.GetPrinter(hprinter, 2)
                status_code = printer_info['Status']
                cjobs = printer_info['cJobs']

                status_errors = []
                if status_code & win32print.PRINTER_STATUS_ERROR: status_errors.append("En estado de Error")
                if status_code & win32print.PRINTER_STATUS_PAPER_OUT: status_errors.append("Sin Papel")
                if status_code & win32print.PRINTER_STATUS_PAPER_JAM: status_errors.append("Papel atascado")
                if status_code & win32print.PRINTER_STATUS_DOOR_OPEN: status_errors.append("Tapa abierta")
                if status_code & win32print.PRINTER_STATUS_OFFLINE: status_errors.append("Apagada / Fuera de línea")
                if status_code & win32print.PRINTER_STATUS_NOT_AVAILABLE: status_errors.append("No disponible")
                
                if status_errors:
                    errors_str = ", ".join(status_errors)
                    raise Exception(f"La impresora reporta un problema físico o de conexión:\n• {errors_str}")

                if cjobs > 5:
                    raise Exception(f"La cola de impresión tiene {cjobs} trabajos atascados. Por favor, limpia la cola.")
            finally:
                win32print.ClosePrinter(hprinter)
        except Exception as e:
            if "acceso" in str(e).lower() or "denegado" in str(e).lower() or "denegó" in str(e).lower():
                raise Exception(f"Windows denegó el acceso a la impresora '{printer_name}'. Detalles: {str(e)}")
            else:
                raise Exception(str(e))

    def print_raw_data(self, data: bytes):
        printer_name = self.config_manager.config.get("printer_name")
        if not printer_name:
            raise Exception("No hay impresora configurada.")
            
        self._validate_printer_status(printer_name)
            
        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket RIOS TOOLS", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, data)
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            raise Exception(f"No fue posible imprimir en {printer_name}: {e}")

    def formatear_ticket(self, venta_data, is_test=False, is_reprint=False):
        # ESC/POS Commands
        ESC = b'\x1b'
        GS = b'\x1d'
        INIT = ESC + b'@'
        BOLD_ON = ESC + b'E\x01'
        BOLD_OFF = ESC + b'E\x00'
        CENTER = ESC + b'a\x01'
        LEFT = ESC + b'a\x00'
        RIGHT = ESC + b'a\x02'
        SIZE_DOUBLE = GS + b'!\x11'
        SIZE_NORMAL = GS + b'!\x00'
        CUT = GS + b'V\x42\x00'
        DRAWER = ESC + b'p\x00\x19\xfa'
        
        def enc(text):
            try:
                return text.encode('cp850', errors='replace')
            except:
                return text.encode('ascii', errors='replace')
                
        width = 32 if self.config_manager.config.get("paper_width") == 58 else 48
        
        output = INIT
        
        output += CENTER + BOLD_ON + SIZE_DOUBLE
        output += enc("RIOS TOOLS\n")
        output += SIZE_NORMAL + BOLD_OFF
        
        if is_test:
            output += enc("\nIMPRESION DE PRUEBA\n")
        if is_reprint:
            output += enc("\n*** REIMPRESION ***\n")
            
        output += enc("\n")
        
        if is_test:
            output += enc(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            output += enc("Caracteres: a e i o u n N $\n")
            output += BOLD_ON + enc("Texto en negrita\n") + BOLD_OFF
            output += SIZE_DOUBLE + enc("Texto Grande\n") + SIZE_NORMAL
            output += enc("-" * width + "\n")
            output += enc("Fin de prueba.\n\n\n\n\n")
        else:
            output += LEFT
            output += enc(f"Ticket: {venta_data.get('ticket', '')}\n")
            output += enc(f"Fecha: {venta_data.get('fecha', '')}\n")
            output += enc(f"Cliente: {venta_data.get('cliente', '')}\n")
            output += enc("-" * width + "\n")
            
            col_qty = 4
            col_precio = 8
            col_imp = 8
            col_name = width - col_qty - col_precio - col_imp - 3
            
            if col_name < 8: col_name = 8 
            
            cabecera = "Prod".ljust(col_name) + " " + "Cant".rjust(col_qty) + " " + "Precio".rjust(col_precio) + " " + "Importe".rjust(col_imp)
            output += enc(cabecera + "\n")
            
            subtotal = 0.0
            
            for item in venta_data.get('items', []):
                name, qty, price, amount = item
                subtotal += amount
                
                name_lines = textwrap.wrap(name, col_name)
                for i, line in enumerate(name_lines):
                    if i == 0:
                        row = line.ljust(col_name) + " " + str(qty).rjust(col_qty) + " " + f"${price:,.2f}".rjust(col_precio) + " " + f"${amount:,.2f}".rjust(col_imp)
                    else:
                        row = line
                    output += enc(row + "\n")
            
            output += enc("-" * width + "\n")
            
            descuento = venta_data.get('descuento', 0.0)
            total = venta_data.get('total', 0.0)
            
            output += RIGHT
            output += enc(f"Subtotal: ${subtotal:,.2f}\n")
            if descuento > 0:
                output += enc(f"Descuento: -${descuento:,.2f}\n")
                
            output += BOLD_ON + SIZE_DOUBLE
            output += enc(f"TOTAL: ${total:,.2f}\n")
            output += SIZE_NORMAL + BOLD_OFF
            
            output += enc("-" * width + "\n")
            
            output += LEFT
            output += enc(f"Pago: {venta_data.get('metodo_pago', '').upper()}\n")
            
            recibido = venta_data.get('recibido')
            cambio = venta_data.get('cambio')
            
            if recibido is not None and recibido > 0:
                output += enc(f"Recibido: ${recibido:,.2f}\n")
                output += enc(f"Cambio: ${cambio:,.2f}\n")
            
            output += CENTER
            output += enc("\n!GRACIAS POR SU COMPRA!\n\n\n\n\n")

        if self.config_manager.config.get("cash_drawer"):
            output += DRAWER
            
        if self.config_manager.config.get("auto_cut"):
            output += CUT
            
        return output

    def imprimir_ticket_sync(self, venta_data, is_reprint=False):
        for _ in range(self.config_manager.config.get("copies", 1)):
            data = self.formatear_ticket(venta_data, is_test=False, is_reprint=is_reprint)
            self.print_raw_data(data)
            
    def imprimir_ticket_prueba_sync(self):
        data = self.formatear_ticket({}, is_test=True)
        self.print_raw_data(data)

# Instancia global
printer = TicketPrinter()
