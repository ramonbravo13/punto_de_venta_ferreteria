from PIL import Image, ImageDraw, ImageFont
from printing.printer_config import PrinterConfig
from printing.barcode_generator import BarcodeGenerator

class LabelRenderer:
    def __init__(self, config: PrinterConfig):
        self.config = config
        self.mm_to_px = lambda mm: int(mm * self.config.dpi / 25.4)
        
        self.width_px = self.mm_to_px(self.config.label_width_mm)
        self.height_px = self.mm_to_px(self.config.label_height_mm)
        
        self.margin_left_px = self.mm_to_px(self.config.margin_left_mm)
        self.margin_right_px = self.mm_to_px(self.config.margin_right_mm)
        self.margin_top_px = self.mm_to_px(self.config.margin_top_mm)
        self.margin_bottom_px = self.mm_to_px(self.config.margin_bottom_mm)
        
        self.usable_width = self.width_px - self.margin_left_px - self.margin_right_px
        
    def get_font(self, size_pt, bold=False):
        try:
            font_name = "arialbd.ttf" if bold else "arial.ttf"
            return ImageFont.truetype(font_name, size_pt)
        except IOError:
            return ImageFont.load_default()
            
    def render_product_label(self, name: str, sku: str, price: float = None) -> Image.Image:
        """Renderiza la etiqueta completa monocromática."""
        img = Image.new("1", (self.width_px, self.height_px), color=1) # 1 = Monocromático (blanco y negro puro)
        draw = ImageDraw.Draw(img)
        
        y = self.margin_top_px
        
        font_title = self.get_font(24, bold=True)
        # Mostrar el nombre del producto, limitarlo a un número razonable de caracteres
        draw.text((self.width_px / 2, y), name[:22], font=font_title, fill=0, anchor="mt")
        
        bbox = draw.textbbox((self.width_px / 2, y), name[:22], font=font_title, anchor="mt")
        y = bbox[3] + 15
        
        if price is not None:
            font_price = self.get_font(22, bold=True)
            price_str = f"${price:,.2f}"
            draw.text((self.width_px / 2, y), price_str, font=font_price, fill=0, anchor="mt")
            bbox_price = draw.textbbox((self.width_px / 2, y), price_str, font=font_price, anchor="mt")
            y = bbox_price[3] + 30
            
        # Altura restante para el código de barras
        available_height = self.height_px - self.margin_bottom_px - y
        barcode_height = min(available_height, int(self.height_px * 0.45))
        barcode_width = min(self.usable_width, int(self.width_px * 0.8))
        
        if barcode_height > 20: # Solo pintar si hay espacio
            barcode_img = BarcodeGenerator.generate(sku, barcode_width, barcode_height)
            barcode_x = self.margin_left_px + (self.usable_width - barcode_width) // 2
            img.paste(barcode_img, (barcode_x, y))
            
        return img

    def render_test_label(self) -> Image.Image:
        """Renderiza una etiqueta de prueba con bordes para verificar márgenes."""
        img = Image.new("1", (self.width_px, self.height_px), color=1)
        draw = ImageDraw.Draw(img)
        
        # Dibujar área útil (bordes) para comprobar que la impresora imprime en toda el área especificada
        draw.rectangle(
            [self.margin_left_px, self.margin_top_px, 
             self.width_px - self.margin_right_px - 1, 
             self.height_px - self.margin_bottom_px - 1],
            outline=0, width=2
        )
        
        font_title = self.get_font(24, bold=True)
        draw.text((self.width_px / 2, self.margin_top_px + 10), "PRUEBA JK58PL", font=font_title, fill=0, anchor="mt")
        
        font_sub = self.get_font(18)
        info = f"{self.config.label_width_mm}x{self.config.label_height_mm}mm - {self.config.dpi} DPI"
        
        bbox = draw.textbbox((self.width_px / 2, self.margin_top_px + 10), "PRUEBA JK58PL", font=font_title, anchor="mt")
        y = bbox[3] + 10
        draw.text((self.width_px / 2, y), info, font=font_sub, fill=0, anchor="mt")
        
        available_height = self.height_px - self.margin_bottom_px - (y + 30)
        barcode_height = min(available_height, int(self.height_px * 0.35))
        barcode_width = min(self.usable_width, int(self.width_px * 0.8))
        
        if barcode_height > 20:
            barcode_img = BarcodeGenerator.generate("TEST123456", barcode_width, barcode_height)
            y += 30
            barcode_x = self.margin_left_px + (self.usable_width - barcode_width) // 2
            img.paste(barcode_img, (barcode_x, y))
            
        return img
