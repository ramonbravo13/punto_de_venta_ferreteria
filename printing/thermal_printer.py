from printing.printer_config import PrinterConfig
from printing.label_renderer import LabelRenderer

class ThermalLabelPrinter:
    def __init__(self):
        self.config = PrinterConfig()
        self.renderer = LabelRenderer(self.config)
        
    def print_test_label(self):
        img = self.renderer.render_test_label()
        self._dispatch_print(img)
        
    def print_product_label(self, name: str, sku: str, price: float = None):
        img = self.renderer.render_product_label(name, sku, price)
        self._dispatch_print(img)
        
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
