from printing.printer_config import PrinterConfig
from printing.label_renderer import LabelRenderer
import logging

print_logger = logging.getLogger("PrintSystem")
if not print_logger.handlers:
    print_logger.setLevel(logging.INFO)
    fh = logging.FileHandler("print_logs.txt", encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s\n%(message)s\n' + '-'*40))
    print_logger.addHandler(fh)

class ThermalLabelPrinter:
    def __init__(self):
        self.config = PrinterConfig()
        self.renderer = LabelRenderer(self.config)
        
    def diagnose(self):
        if self.config.connection_type == "windows":
            from printing.windows_printer import WindowsPrinter
            printer = WindowsPrinter(self.config)
            return printer.diagnose()
        elif self.config.connection_type in ["serial", "bluetooth"]:
            from printing.escpos_printer import EscPosPrinter
            printer = EscPosPrinter(self.config)
            return printer.diagnose()
        else:
            return f"IMPRESORA DE ETIQUETAS\n\n✗ Tipo de conexión no soportada: {self.config.connection_type}\n\nRESULTADO: ERROR"

    def print_test_label(self):
        try:
            img = self.renderer.render_test_label()
            self._dispatch_print(img)
            print_logger.info(f"Tipo: ETIQUETA\nImpresora: {self.config.printer_name}\nDocumento: Prueba\nResultado: SUCCESS")
        except Exception as e:
            print_logger.info(f"Tipo: ETIQUETA\nImpresora: {self.config.printer_name}\nDocumento: Prueba\nResultado: ERROR\nDetalle: {str(e)}")
            raise
        
    def print_product_label(self, name: str, sku: str, price: float = None):
        try:
            img = self.renderer.render_product_label(name, sku, price)
            self._dispatch_print(img)
            print_logger.info(f"Tipo: ETIQUETA\nImpresora: {self.config.printer_name}\nProducto: {sku}\nCantidad: 1\nResultado: SUCCESS")
        except Exception as e:
            print_logger.info(f"Tipo: ETIQUETA\nImpresora: {self.config.printer_name}\nProducto: {sku}\nCantidad: 1\nResultado: ERROR\nDetalle: {str(e)}")
            raise
        
    def _dispatch_print(self, img):
        if self.config.connection_type == "windows":
            from printing.windows_printer import WindowsPrinter
            printer = WindowsPrinter(self.config)
            printer.print_image(img)
        elif self.config.connection_type in ["serial", "bluetooth"]:
            from printing.escpos_printer import EscPosPrinter
            printer = EscPosPrinter(self.config)
            printer.print_image(img)
        else:
            raise Exception(f"Tipo de conexión no soportada: {self.config.connection_type}")
