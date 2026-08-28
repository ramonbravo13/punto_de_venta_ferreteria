import io
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPainter, QImage, QPageSize, QPageLayout
from PyQt6.QtCore import QSizeF, QMarginsF
from printing.printer_config import PrinterConfig

class WindowsPrinter:
    def __init__(self, config: PrinterConfig):
        self.config = config
        
    def _validate_printer_status(self, printer_name: str):
        """Verifica el estado real de la impresora usando la API de Spooler de Windows."""
        try:
            import win32print
        except ImportError:
            # Si no está instalado pywin32, omitimos la validación estricta
            return

        # 1. Verificar si la impresora está instalada en Windows
        printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        if printer_name not in printers:
            raise Exception(f"La impresora '{printer_name}' no existe o fue desinstalada de Windows.")

        # 2. Intentar abrir la impresora
        try:
            hprinter = win32print.OpenPrinter(printer_name)
        except Exception as e:
            raise Exception(f"Windows denegó el acceso a la impresora '{printer_name}'. Detalles: {str(e)}")

        # 3. Obtener el estado detallado
        try:
            printer_info = win32print.GetPrinter(hprinter, 2)
            status_code = printer_info['Status']
            cjobs = printer_info['cJobs']

            # Banderas de estado de win32print
            status_errors = []
            if status_code & win32print.PRINTER_STATUS_ERROR: status_errors.append("En estado de Error")
            if status_code & win32print.PRINTER_STATUS_PAPER_OUT: status_errors.append("Sin Papel")
            if status_code & win32print.PRINTER_STATUS_PAPER_JAM: status_errors.append("Papel atascado")
            if status_code & win32print.PRINTER_STATUS_DOOR_OPEN: status_errors.append("Tapa abierta")
            if status_code & win32print.PRINTER_STATUS_OFFLINE: status_errors.append("Apagada / Fuera de línea")
            if status_code & win32print.PRINTER_STATUS_NOT_AVAILABLE: status_errors.append("No disponible")
            if status_code & win32print.PRINTER_STATUS_NO_TONER: status_errors.append("Sin Toner")
            
            if status_errors:
                errors_str = ", ".join(status_errors)
                raise Exception(f"La impresora reporta un problema físico o de conexión:\n• {errors_str}")

            if cjobs > 5:
                raise Exception(f"La cola de impresión tiene {cjobs} trabajos atascados. Por favor, limpia la cola de impresión de Windows antes de continuar.")

        finally:
            win32print.ClosePrinter(hprinter)

    def print_image(self, img):
        """Envía la imagen generada a la impresora de Windows forzando el tamaño exacto en milímetros."""
        printer_name = self.config.printer_name
        if not printer_name:
            raise Exception("No se ha seleccionado ninguna impresora de Windows en la configuración.")
            
        # Validación profunda del hardware/spooler antes de enviar el trabajo a Qt
        self._validate_printer_status(printer_name)
            
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
            raise Exception("Windows rechazó el trabajo de impresión. Asegúrate de que la impresora esté conectada, encendida y configurada correctamente.")
            
        # Dibujar la imagen ajustada exactamente al área imprimible (viewport)
        rect = painter.viewport()
        painter.drawImage(rect, qimg)
        painter.end()
