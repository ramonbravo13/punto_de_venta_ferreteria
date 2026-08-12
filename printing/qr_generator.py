import qrcode
from PIL import Image

class QRGenerator:
    @staticmethod
    def generate(text: str, size: int) -> Image.Image:
        """Genera un código QR y lo ajusta al tamaño especificado."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=1,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("1")
        return img.resize((size, size), Image.Resampling.LANCZOS)
