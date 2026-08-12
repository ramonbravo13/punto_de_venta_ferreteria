import os
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')

class BusinessLogic:
    """
    Contiene la lógica de negocio, cálculos y procesamiento de imágenes.
    """
    
    @staticmethod
    def resize_product_image(image_path, output_folder="data/images"):
        """
        Redimensiona una imagen a 128x128px para optimizar memoria.
        """
        if not image_path or not os.path.exists(image_path):
            return None
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        try:
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_folder, filename)
            
            with Image.open(image_path) as img:
                img = img.resize((128, 128), Image.Resampling.LANCZOS)
                img.save(output_path)
                return output_path
        except Exception as e:
            print(f"Error al procesar imagen: {e}")
            return None

    @staticmethod
    def calculate_investment(products):
        """
        Calcula el total de inversión basado en el stock actual y costo.
        products: Lista de tuplas o diccionarios con (current_stock, cost_price)
        """
        total = sum((item['current_stock'] * item['cost_price']) for item in products)
        return total

    @staticmethod
    def get_stock_status(current_stock, min_stock):
        """
        Determina el color del 'semáforo' de stock.
        """
        if current_stock <= 0:
            return "Red" # Agotado
        elif current_stock <= min_stock:
            return "Amber" # Stock Bajo
        return "Green" # Saludable

    @staticmethod
    def calculate_change(total_amount, amount_paid):
        """Calcula el cambio para el POS."""
        if amount_paid < total_amount:
            return 0
        return round(amount_paid - total_amount, 2)

    @staticmethod
    def calculate_niche_metrics(sales, purchases):
        """
        Calcula Ganancia Bruta y Neta.
        Ganancia Bruta = Sum(Ventas) - Sum(Costo de lo vendido)
        Ganancia Neta = Ganancia Bruta - Gastos/Devoluciones
        """
        # Implementación simplificada para el dashboard
        total_sales = sum(s['total_amount'] for s in sales)
        # Esto se expandirá al integrar con la DB
        return total_sales

class MplCanvas(FigureCanvas):
    """Lienzo para renderizar gráficas de Matplotlib en PyQt6."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Configuración de estética para modo oscuro
        plt.style.use('dark_background')
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_alpha(0) # Fondo transparente
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('#1E293B')
        super().__init__(fig)
        self.setParent(parent)

    def plot_sales(self, data):
        """Grafica las ventas: data es lista de (fecha, total)."""
        self.axes.clear()
        if not data:
            self.axes.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
            self.draw()
            return
            
        dates = [d[0] for d in data]
        totals = [d[1] for d in data]
        
        self.axes.plot(dates, totals, color='#0EA5E9', marker='o', linewidth=2)
        self.axes.fill_between(dates, totals, color='#0EA5E9', alpha=0.2)
        self.axes.set_title("Ventas Diarias (Últimos 7 días)", color='#F8FAFC', pad=15)
        self.axes.tick_params(axis='x', rotation=45, colors='#94A3B8', labelsize=8)
        self.axes.tick_params(axis='y', colors='#94A3B8')
        
        for spine in self.axes.spines.values():
            spine.set_color('#334155')
            
        self.figure.tight_layout()
        self.draw()

    def plot_investment_vs_profit(self, investment, profit):
        """Grafica comparativa de Inversión vs Ganancia Neta."""
        self.axes.clear()
        
        labels = ['Inversión', 'Ganancia Neta']
        values = [investment, profit]
        colors = ['#0EA5E9', '#10B981'] # Azul y Verde
        
        bars = self.axes.bar(labels, values, color=colors, width=0.5)
        self.axes.set_title("Inversión vs Ganancia", color='#F8FAFC', pad=15)
        self.axes.tick_params(axis='y', colors='#94A3B8')
        self.axes.tick_params(axis='x', colors='#F8FAFC', labelsize=10)
        
        # Ocultar bordes innecesarios
        for spine in self.axes.spines.values():
            spine.set_color('#334155')
            
        # Añadir las etiquetas de valor arriba de cada barra
        max_val = max(values) if max(values) > 0 else 1
        for bar in bars:
            height = bar.get_height()
            self.axes.text(bar.get_x() + bar.get_width()/2., height + (max_val*0.02),
                    f'${height:,.0f}', ha='center', va='bottom', color='#F8FAFC', fontweight='bold')
            
        self.figure.tight_layout()
        self.draw()

    def plot_bar_chart(self, data, title="Top Productos"):
        """Grafica barras horizontales: data es lista de (nombre, cantidad)."""
        self.axes.clear()
        if not data:
            self.axes.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
            self.draw()
            return
            
        names = [d[0] for d in data][::-1] # Invertir para que el mejor esté arriba
        values = [d[1] for d in data][::-1]
        
        self.axes.barh(names, values, color='#10B981')
        self.axes.set_title(title, color='#F8FAFC', pad=15)
        self.axes.tick_params(axis='x', colors='#94A3B8')
        self.axes.tick_params(axis='y', colors='#94A3B8')
        
        for spine in self.axes.spines.values():
            spine.set_color('#334155')
            
        self.figure.tight_layout()
        self.draw()

    def plot_financial_comparison(self, investment, sales):
        """Gráfica de barras comparativa de salud financiera."""
        self.axes.clear()
        labels = ['Inversión', 'Ventas']
        values = [investment, sales]
        colors = ['#F59E0B', '#0EA5E9']
        
        bars = self.axes.bar(labels, values, color=colors)
        self.axes.set_title("Salud Financiera (Total)", color='#F8FAFC', pad=15)
        self.axes.tick_params(axis='y', colors='#94A3B8')
        self.axes.tick_params(axis='x', colors='#F8FAFC')
        
        # Añadir etiquetas de valor encima de las barras
        for bar in bars:
            height = bar.get_height()
            self.axes.annotate(f'${height:,.0f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', color='#F8FAFC', fontsize=9)
        
        for spine in self.axes.spines.values():
            spine.set_color('#334155')
            
        self.figure.tight_layout()
        self.draw()

    def plot_profit_history(self, data):
        """Grafica el historial de ganancias mensuales."""
        self.axes.clear()
        if not data:
            self.axes.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
            self.draw()
            return
            
        months = [d[0] for d in data]
        profits = [d[1] for d in data]
        
        self.axes.plot(months, profits, color='#8B5CF6', marker='s', linewidth=2)
        self.axes.fill_between(months, profits, color='#8B5CF6', alpha=0.1)
        self.axes.set_title("Ganancias por Mes", color='#F8FAFC', pad=15)
        self.axes.tick_params(axis='x', rotation=30, colors='#94A3B8', labelsize=8)
        self.axes.tick_params(axis='y', colors='#94A3B8')
        
        for spine in self.axes.spines.values():
            spine.set_color('#334155')
            
        self.figure.tight_layout()
        self.draw()
