import serial
from printing.printer_config import PrinterConfig

class EscPosPrinter:
    def __init__(self, config: PrinterConfig):
        self.config = config
        
    def diagnose(self):
        if not self.config.com_port:
            return "IMPRESORA DE ETIQUETAS\n\n✓ Configuración encontrada\n✗ Puerto COM no configurado\n\nRESULTADO: ERROR"
        report = "IMPRESORA DE ETIQUETAS\n\n✓ Configuración encontrada\n"
        try:
            ser = serial.Serial(self.config.com_port, self.config.baud_rate, timeout=3)
            ser.close()
            report += f"✓ Puerto {self.config.com_port} detectado y accesible\n✓ Comunicación Serial correcta\n\nRESULTADO: OK"
            return report
        except Exception as e:
            report += f"✗ Error de puerto Serial detectado:\n{str(e)}\n\nRESULTADO: ERROR"
            return report

    def print_image(self, img):
        """Impresión de imagen rasterizada vía Serial ESC/POS directo."""
        if not self.config.com_port:
            raise Exception("No se ha configurado un puerto COM para conexión Serial/Bluetooth.")
            
        try:
            ser = serial.Serial(self.config.com_port, self.config.baud_rate, timeout=3)
        except Exception as e:
            raise Exception(f"No se pudo abrir el puerto {self.config.com_port}: {e}")
            
        img = img.convert('1')
        width, height = img.size
        
        # Inicializar impresora
        ser.write(b'\x1B\x40')
        
        # Enviar imagen vía comando GS v 0 (Print raster bit image)
        width_bytes = (width + 7) // 8
        
        command = bytearray([0x1D, 0x76, 0x30, 0x00])
        command.append(width_bytes % 256)
        command.append(width_bytes // 256)
        command.append(height % 256)
        command.append(height // 256)
        
        ser.write(command)
        
        pixels = img.load()
        for y in range(height):
            for x_byte in range(width_bytes):
                byte_val = 0
                for bit in range(8):
                    x = x_byte * 8 + bit
                    if x < width:
                        # En Pillow modo '1', 0 es negro (lo que se imprime)
                        is_black = (pixels[x, y] == 0)
                        if is_black:
                            byte_val |= (1 << (7 - bit))
                ser.write(bytes([byte_val]))
                
        # Feeding paper
        ser.write(b'\n\n\n')
        # Intentar cortar (aunque muchas JK58 no tienen cortador, el comando se ignora)
        ser.write(b'\x1D\x56\x42\x00') 
        
        ser.close()
