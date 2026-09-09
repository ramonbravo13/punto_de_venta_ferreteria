import io
import barcode
from barcode.writer import ImageWriter
from PIL import Image

class BarcodeGenerator:
    @staticmethod
    def generate(text: str, width: int, height: int) -> Image.Image:
        """Genera un código de barras (EAN-13 o Code128) y lo ajusta al tamaño especificado."""
        try:
            if text.isdigit() and len(text) in (12, 13):
                barcode_class = barcode.get_barcode_class('ean13')
            else:
                barcode_class = barcode.get_barcode_class('code128')
        except Exception:
            barcode_class = barcode.get_barcode_class('code128')
            
        rv = io.BytesIO()
        options = {
            'module_width': 0.4,
            'module_height': 12.0,
            'font_size': 12,
            'text_distance': 4,
            'quiet_zone': 3,
            'font_path': 'arial.ttf'
        }
        
        # En ean13, si se pasa un string de 12 dígitos, la librería calcula el checksum (13) automáticamente
        barcode_instance = barcode_class(text, writer=ImageWriter())
        barcode_instance.write(rv, options=options)
        
        rv.seek(0)
        # Importante: NEAREST evita que las barras se difuminen en grises y se pierda el grosor original al redimensionar.
        img = Image.open(rv).convert("1")
        return img.resize((width, height), Image.Resampling.NEAREST)
