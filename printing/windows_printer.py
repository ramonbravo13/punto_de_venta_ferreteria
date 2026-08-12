import io
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPainter, QImage, QPageSize, QPageLayout
from PyQt6.QtCore import QSizeF, QMarginsF
from printing.printer_config import PrinterConfig

class WindowsPrinter:
    def __init__(self, config: PrinterConfig):
        self.config = config
        
    def print_image(self, img):
        """Envía la imagen generada a la impresora de Windows forzando el tamaño exacto en milímetros."""
        printer_name = self.config.printer_name
        if not printer_name:
            raise Exception("No se ha seleccionado ninguna impresora de Windows en la configuración.")
            
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPrinterName(printer_name)
        
        # Forzar el tamaño de la etiqueta en milímetros
        page_size = QPageSize(QSizeF(self.config.label_width_mm, self.config.label_height_mm), QPageSize.Unit.Millimeter)
        printer.setPageSize(page_size)
        
        # Quitar todos los márgenes del driver para que el control lo tenga nuestra imagen
        margins = QMarginsF(0, 0, 0, 0)
        printer.setPageMargins(margins, QPageLayout.Unit.Millimeter)
        
        # Convertir PIL Image a QImage
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        qimg = QImage.fromData(buf.getvalue())
        
        painter = QPainter()
        if not painter.begin(printer):
            raise Exception("No se pudo inicializar el pintor de Qt para esta impresora.")
            
        # Dibujar la imagen ajustada exactamente al área imprimible (viewport)
        rect = painter.viewport()
        painter.drawImage(rect, qimg)
        painter.end()

