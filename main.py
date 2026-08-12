import sys
import os
import shutil
import sqlite3
import json
import random
from datetime import datetime
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem,
                              QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QFormLayout, QMessageBox, QFileDialog, QComboBox, 
                             QCheckBox, QSplitter, QTabWidget, QDateEdit, QGridLayout, QLabel as QtQLabel,
                             QCompleter)
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QPixmap, QIcon, QColor, QBrush, QPainter, QImage
import ui_components as ui
from database import DatabaseManager
from logic import BusinessLogic, MplCanvas

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rios Tools")
        self.setWindowIcon(QIcon("logo.jpg"))
        self.resize(1024, 768)
        self.setStyleSheet(ui.STYLE_SHEET)
        self.setMinimumSize(1024, 768)
        
        self.db = DatabaseManager()
        self.logic = BusinessLogic()
        
        self.init_ui()

    def init_ui(self):
        # Layout Principal
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #0F172A; border-right: 1px solid #1E293B;")
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Logo de Rios Tools en la parte superior izquierda
        logo_label = QtQLabel()
        pixmap = QPixmap("logo.jpg")
        logo_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("padding: 10px; background-color: transparent;")
        sidebar_layout.addWidget(logo_label)
        
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet("""
            QListWidget { background-color: transparent; border: none; padding-top: 20px; }
            QListWidget::item { height: 50px; padding-left: 15px; color: #94A3B8; border: none; }
            QListWidget::item:selected { background-color: #334155; color: #0EA5E9; border-left: 4px solid #0EA5E9; font-weight: bold; }
        """)
        self.menu_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.menu_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.menu_list.setFixedHeight(400) # 7 ítems x 50px + padding
        
        menu_items = ["Reportes", "Inventario", "Punto de Venta", "Compras", "Caja", "Configuración", "Clientes"]
        for item in menu_items:
            self.menu_list.addItem(item)
        self.menu_list.currentRowChanged.connect(self.display_page)
        sidebar_layout.addWidget(self.menu_list)
        
        # Indicador de Caja Global
        self.caja_status_card = ui.Card()
        self.caja_status_card.setStyleSheet("background-color: #1E293B; margin: 5px; border: 1px solid #334155;")
        caja_status_layout = QVBoxLayout(self.caja_status_card)
        self.lbl_caja_indicator = ui.QLabel("🔘 Caja Cerrada")
        self.lbl_caja_indicator.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 10pt;")
        self.lbl_caja_total_day = ui.QLabel("Hoy: $ 0.00")
        self.lbl_caja_total_day.setStyleSheet("color: #0EA5E9; font-size: 9pt;")
        caja_status_layout.addWidget(self.lbl_caja_indicator)
        caja_status_layout.addWidget(self.lbl_caja_total_day)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.caja_status_card)
        
        layout.addWidget(sidebar, 0)
        
        # Area de Contenido (Stacked Widget)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_dashboard())
        self.stack.addWidget(self.create_inventory())
        self.stack.addWidget(self.create_pos())
        self.stack.addWidget(self.create_purchases())
        self.stack.addWidget(self.create_caja())
        self.stack.addWidget(self.create_config())
        self.stack.addWidget(self.create_customers())
        
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(main_widget)
        
        # Carga inicial de datos
        self.update_dashboard_data()
        self.load_inventory_data()
        self.refresh_purchase_selectors()
        self.update_global_caja_status()
        self.load_pos_customers()

    def update_global_caja_status(self):
        open_caja = self.db.get_open_caja()
        if open_caja:
            self.lbl_caja_indicator.setText("🟢 Caja Abierta")
            self.lbl_caja_indicator.setStyleSheet("color: #10B981; font-weight: bold; font-size: 10pt;")
            totals = self.db.get_caja_totals(open_caja[0])
            if totals:
                total_sales = sum(totals['sales'].values())
                self.lbl_caja_total_day.setText(f"Sesión: $ {total_sales:,.2f}")
        else:
            self.lbl_caja_indicator.setText("🔘 Caja Cerrada")
            self.lbl_caja_indicator.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 10pt;")
            self.lbl_caja_total_day.setText("Turno inactivo")

    def display_page(self, index):
        self.stack.setCurrentIndex(index)
        if index == 4: # Página de Caja
            self.update_caja_view()
        elif index == 0: # Dashboard
            self.update_dashboard_data()
        elif index == 1: # Inventario
            self.load_inventory_data()
        elif index == 7: # Clientes
            self.load_customers_table()

    def create_dashboard(self):
        # Usar un contenedor con ScrollArea para que el Sidebar quede fijo
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title_layout = QHBoxLayout()
        title = ui.QLabel("Reportes y Analítica")
        title.setObjectName("Title")
        
        btn_excel = ui.PrimaryButton("Exportar a Excel")
        btn_pdf = ui.PrimaryButton("Generar Reporte PDF")
        btn_pdf.setObjectName("Secondary")
        
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(btn_excel)
        title_layout.addWidget(btn_pdf)
        layout.addLayout(title_layout)
        
        # Grid de Tarjetas de Resumen
        # Row 1
        cards_layout_1 = QHBoxLayout()
        
        # Inversión
        card_inv = ui.Card()
        card_inv_layout = QVBoxLayout(card_inv)
        lbl_inv = ui.QLabel("Inversión / Inventario")
        lbl_inv.setObjectName("Secondary")
        self.val_inv = ui.QLabel("$ 0.00")
        self.val_inv.setStyleSheet("font-size: 20pt; font-weight: bold; color: #0EA5E9;")
        card_inv_layout.addWidget(lbl_inv)
        card_inv_layout.addWidget(self.val_inv)
        
        # Ventas 30d
        card_sales_30d = ui.Card()
        card_sales_30d_layout = QVBoxLayout(card_sales_30d)
        lbl_sales_30d = ui.QLabel("Ventas (30 días)")
        lbl_sales_30d.setObjectName("Secondary")
        self.val_sales_30d = ui.QLabel("$ 0.00")
        self.val_sales_30d.setStyleSheet("font-size: 20pt; font-weight: bold; color: #8B5CF6;")
        card_sales_30d_layout.addWidget(lbl_sales_30d)
        card_sales_30d_layout.addWidget(self.val_sales_30d)

        # Ganancia Neta 30d
        card_gn = ui.Card()
        card_gn_layout = QVBoxLayout(card_gn)
        lbl_gn = ui.QLabel("Ganancia Neta (30 días)")
        lbl_gn.setObjectName("Secondary")
        self.val_gn = ui.QLabel("$ 0.00")
        self.val_gn.setStyleSheet("font-size: 20pt; font-weight: bold; color: #10B981;")
        card_gn_layout.addWidget(lbl_gn)
        card_gn_layout.addWidget(self.val_gn)

        cards_layout_1.addWidget(card_inv)
        cards_layout_1.addWidget(card_sales_30d)
        cards_layout_1.addWidget(card_gn)
        
        # Row 2
        cards_layout_2 = QHBoxLayout()

        # Ventas 7d
        card_sales = ui.Card()
        card_sales_layout = QVBoxLayout(card_sales)
        lbl_sales = ui.QLabel("Ventas (7 días)")
        lbl_sales.setObjectName("Secondary")
        self.val_sales = ui.QLabel("$ 0.00")
        self.val_sales.setStyleSheet("font-size: 20pt; font-weight: bold; color: #10B981;")
        card_sales_layout.addWidget(lbl_sales)
        card_sales_layout.addWidget(self.val_sales)

        # Deuda Total
        card_debt = ui.Card()
        card_debt_layout = QVBoxLayout(card_debt)
        lbl_debt = ui.QLabel("Deuda Total")
        lbl_debt.setObjectName("Secondary")
        self.val_debt = ui.QLabel("$ 0.00")
        self.val_debt.setStyleSheet("font-size: 20pt; font-weight: bold; color: #EF4444;")
        self.lbl_debt_alert = ui.QLabel("")
        self.lbl_debt_alert.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 9pt;")
        self.lbl_debt_alert.setWordWrap(True)
        card_debt_layout.addWidget(lbl_debt)
        card_debt_layout.addWidget(self.val_debt)
        card_debt_layout.addWidget(self.lbl_debt_alert)

        # Alertas de Stock
        card_stock = ui.Card()
        card_stock_layout = QVBoxLayout(card_stock)
        lbl_stock = ui.QLabel("Alertas de Stock")
        lbl_stock.setObjectName("Secondary")
        self.val_stock = ui.QLabel("0 Productos")
        self.val_stock.setStyleSheet("font-size: 20pt; font-weight: bold; color: #F59E0B;")
        card_stock_layout.addWidget(lbl_stock)
        card_stock_layout.addWidget(self.val_stock)
        
        card_inv.clicked.connect(self.show_investment_details)
        card_sales.clicked.connect(self.show_sales_details)
        card_stock.clicked.connect(self.show_stock_alerts)
        card_debt.clicked.connect(self.show_debt_details)
        
        cards_layout_2.addWidget(card_sales)
        cards_layout_2.addWidget(card_debt)
        cards_layout_2.addWidget(card_stock)

        layout.addLayout(cards_layout_1)
        layout.addLayout(cards_layout_2)

        # Gráficas
        charts_grid = QHBoxLayout()
        
        self.inv_profit_chart = MplCanvas(self, width=5, height=4)
        charts_grid.addWidget(self.inv_profit_chart)
        
        self.sales_chart = MplCanvas(self, width=5, height=4)
        charts_grid.addWidget(self.sales_chart)
        
        layout.addLayout(charts_grid)
        
        layout.addStretch()
        
        scroll.setWidget(page)
        return scroll

    def update_dashboard_data(self):
        """Actualiza las métricas y las gráficas del dashboard."""
        # 1. Inversión Total
        inv = self.db.get_investment_data()
        self.val_inv.setText(f"$ {inv:,.2f}")
        
        # 2. Ventas (7 días)
        sales_7d = self.db.get_sales_data(7)
        total_sales = sum(d[1] for d in sales_7d)
        self.val_sales.setText(f"$ {total_sales:,.2f}")
        
        # 3. Alertas de Stock
        alerts = self.db.get_stock_alerts()
        self.val_stock.setText(f"{len(alerts)} Productos")
        
        debt = self.db.get_debts_total()
        self.val_debt.setText(f"$ {debt:,.2f}")
        
        if hasattr(self, 'val_sales_30d') and hasattr(self, 'val_gn'):
            sales_30d = self.db.get_sales_data(30)
            total_sales_30d = sum(d[1] for d in sales_30d)
            ganancia_neta = self.db.get_profit_data(30)
            self.val_sales_30d.setText(f"$ {total_sales_30d:,.2f}")
            self.val_gn.setText(f"$ {ganancia_neta:,.2f}")
            
        upcoming = self.db.get_upcoming_debts()
        if upcoming:
            self.lbl_debt_alert.setText(f"⚠️ {len(upcoming)} deuda(s) vencen pronto")
            self.lbl_debt_alert.show()
        else:
            self.lbl_debt_alert.hide()

        # 8. Actualizar Gráficas
        # 8.1 Ventas Diarias (7 días)
        self.sales_chart.plot_sales(sales_7d)
        
        # 8.2 Inversión vs Ganancia Neta
        # Asegurarnos de que las variables existan para la gráfica
        gn_val = 0.0
        if hasattr(self, 'val_gn'):
            gn_val = self.db.get_profit_data(30) # o del tiempo que desees
            
        self.inv_profit_chart.plot_investment_vs_profit(inv, gn_val)

    def show_investment_details(self):
        dialog = InvestmentDetailDialog(self)
        dialog.exec()

    def show_sales_details(self):
        dialog = SalesDetailDialog(self)
        dialog.exec()

    def show_stock_alerts(self):
        self.display_page(1) # Ir a Inventario
        self.menu_list.setCurrentRow(1)

    def show_debt_details(self):
        dialog = DebtDetailDialog(self)
        dialog.exec()

    def show_profit_details(self):
        dialog = ProfitDetailDialog(self)
        dialog.exec()

    def load_inventory_data(self):
        """Carga los productos desde la DB a la tabla con estilo moderno."""
        products = self.db.get_all_products()
        self.inventory_table.setRowCount(0)
        self.inventory_table.verticalHeader().setDefaultSectionSize(60)
        
        for row_data in products:
            row_idx = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row_idx)
            
            p_id, img_path, sku, name, purchase_type, stock, cost, price, min_stock, tax_pct, incoming_stock, next_delivery = row_data
            
            # Cálculo de nuevos valores
            cost_with_tax = cost * (1 + tax_pct / 100.0)
            profit_per_unit = price - cost_with_tax

            # 1. Imagen (Thumbnail más grande)
            if img_path and os.path.exists(img_path):
                img_label = ui.QLabel()
                pixmap = QPixmap(img_path)
                img_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.inventory_table.setCellWidget(row_idx, 0, img_label)
            
            # 2. Datos de texto con formato
            stock_text = str(stock)
            if incoming_stock and incoming_stock > 0:
                short_date = str(next_delivery)[:10] if next_delivery else "Pronto"
                stock_text += f"\n(+{incoming_stock} para {short_date})"

            # SKU, Producto, Categoría, Stock, Costo, Venta
            display_data = [
                (str(sku), Qt.AlignmentFlag.AlignCenter),
                (str(name), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (str(purchase_type), Qt.AlignmentFlag.AlignCenter),
                (stock_text, Qt.AlignmentFlag.AlignCenter),
                (f"$ {cost:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (f"$ {cost_with_tax:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (f"$ {price:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (f"$ {profit_per_unit:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ]
            
            # Lógica de colores para el stock
            stock_color = QColor("#10B981") # Verde (Normal)
            if stock <= 0:
                stock_color = QColor("#EF4444") # Rojo (Agotado)
            elif stock <= min_stock:
                stock_color = QColor("#F59E0B") # Ámbar (Bajo)
            
            for col, (text, align) in enumerate(display_data, start=1):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                
                # Resaltar la celda de stock
                if col == 4:
                    item.setForeground(QBrush(stock_color))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                self.inventory_table.setItem(row_idx, col, item)
            
            # 3. Columna de Acciones
            btn_edit = ui.TableActionButton("Editar")
            btn_edit.clicked.connect(lambda checked, pid=p_id: self.open_edit_product_dialog(pid))
            self.inventory_table.setCellWidget(row_idx, 9, btn_edit)
        
        # Altura ya manejada por verticalHeader().setDefaultSectionSize(40)
    def create_inventory(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        top_layout = QHBoxLayout()
        title = ui.QLabel("Inventario de Productos")
        title.setObjectName("Title")
        
        search = ui.SearchField("Buscar por SKU o Nombre...")
        search.setFixedWidth(300)
        
        btn_add = ui.PrimaryButton("+ Nuevo Producto")
        btn_add.clicked.connect(self.open_new_product_dialog)
        
        btn_pending = ui.PrimaryButton("📦 Pedidos Pendientes")
        btn_pending.setObjectName("Secondary")
        btn_pending.clicked.connect(self.open_pending_orders)
        
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(search)
        top_layout.addWidget(btn_pending)
        top_layout.addWidget(btn_add)
        layout.addLayout(top_layout)
        
        # Tabla Modernizada
        self.inventory_table = QTableWidget(0, 10)
        self.inventory_table.setHorizontalHeaderLabels([
            "Imagen", "SKU", "Producto", "Tipo Compra", "Stock", "Costo", "Costo c/Imp.", "Venta", "Ganancia", "Acciones"
        ])
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.inventory_table.setColumnWidth(0, 70)
        
        self.inventory_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.inventory_table.itemDoubleClicked.connect(self.on_inventory_double_click)
        layout.addWidget(self.inventory_table)
        
        return page

    def create_pos(self):
        page = QWidget()
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Lado Izquierdo: Lista de Venta
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        title = ui.QLabel("Nueva Venta")
        title.setObjectName("Title")
        left_layout.addWidget(title)
        
        self.barcode_input = ui.QLineEdit()
        self.barcode_input.setPlaceholderText("Escanee Código o ingrese nombre/SKU...")
        self.barcode_input.setStyleSheet("font-size: 14pt; padding: 15px; border: 2px solid #0EA5E9;")
        self.barcode_input.returnPressed.connect(self.add_to_cart)
        
        # --- Autocomplete for POS ---
        self.pos_product_completer_model = QStringListModel()
        self.pos_product_completer = QCompleter(self.pos_product_completer_model, self)
        self.pos_product_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.pos_product_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.pos_product_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.barcode_input.setCompleter(self.pos_product_completer)
        
        self.barcode_input.textEdited.connect(self.on_pos_product_text_edited)
        self.pos_product_completer.activated.connect(self.on_pos_product_selected)
        
        left_layout.addWidget(self.barcode_input)
        
        self.sale_table = QTableWidget(0, 4)
        self.sale_table.setHorizontalHeaderLabels(["SKU", "Artículo", "Cant.", "Subtotal"])
        self.sale_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sale_table.verticalHeader().setDefaultSectionSize(35)
        left_layout.addWidget(self.sale_table)
        
        # Lado Derecho: Checkout
        right_widget = ui.Card()
        right_widget.setFixedWidth(350)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        total_lbl = ui.QLabel("TOTAL")
        total_lbl.setObjectName("Secondary")
        self.total_val = ui.QLabel("$ 0.00")
        self.total_val.setStyleSheet("font-size: 32pt; font-weight: bold; color: #0EA5E9;")
        
        right_layout.addWidget(total_lbl)
        right_layout.addWidget(self.total_val)
        right_layout.addSpacing(20)
        
        right_layout.addWidget(ui.QLabel("Cliente Asignado:"))
        customer_layout = QHBoxLayout()
        self.pos_customer = QComboBox()
        self.pos_customer.setMinimumHeight(35)
        self.pos_customer.addItem("Consumidor Final", None)
        
        btn_new_customer = ui.PrimaryButton("+")
        btn_new_customer.setFixedWidth(40)
        btn_new_customer.clicked.connect(self.pos_add_customer)
        
        customer_layout.addWidget(self.pos_customer)
        customer_layout.addWidget(btn_new_customer)
        right_layout.addLayout(customer_layout)
        
        right_layout.addWidget(ui.QLabel("Descuento Aplicado ($):"))
        self.pos_discount = ui.QLineEdit()
        self.pos_discount.setPlaceholderText("Ej: 5.00")
        self.pos_discount.setMinimumHeight(35)
        self.pos_discount.textChanged.connect(self.update_cart_table)
        right_layout.addWidget(self.pos_discount)
        
        right_layout.addSpacing(20)
        
        btn_pay = ui.PrimaryButton("COBRAR (F5)")
        btn_pay.setFixedHeight(60)
        btn_pay.setStyleSheet("font-size: 16pt;")
        btn_pay.clicked.connect(self.process_sale)
        
        btn_clear = ui.AlertButton("Cancelar Venta")
        btn_clear.clicked.connect(self.clear_sale)
        
        right_layout.addWidget(btn_pay)
        right_layout.addWidget(btn_clear)
        right_layout.addStretch()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        main_layout.addWidget(splitter)
        
        self.cart_items = [] # Almacena (id, sku, name, qty, price)
        
        return page

    def on_pos_product_text_edited(self, text):
        if not text or len(text) < 2:
            self.pos_product_completer_model.setStringList([])
            return
            
        results = self.db.search_products(text, limit=15)
        suggestions = []
        for sku, name, _, _, _ in results:
            suggestions.append(f"{sku} | {name}")
            
        self.pos_product_completer_model.setStringList(suggestions)
        self.pos_product_completer.complete()

    def on_pos_product_selected(self, text):
        if " | " not in text:
            return
        sku = text.split(" | ")[0]
        self.barcode_input.setText(sku)
        self.add_to_cart()

    def add_to_cart(self):
        query = self.barcode_input.text().strip()
        if not query: return
        
        product = self.db.get_product_by_sku_or_name(query)
        if product:
            p_id, p_name, _, price, real_sku = product
            # Buscar si ya está en el carrito
            found = False
            for i, item in enumerate(self.cart_items):
                # item: (id, sku, name, qty, price)
                if item[0] == p_id:
                    self.cart_items[i] = (p_id, item[1], p_name, item[3] + 1, price)
                    found = True
                    break
            
            if not found:
                self.cart_items.append((p_id, real_sku, p_name, 1, price))
            
            self.update_cart_table()
            self.barcode_input.clear()
            self.barcode_input.setFocus()
        else:
            QMessageBox.warning(self, "No Encontrado", f"No se encontró ningún producto con: '{query}'")
            self.barcode_input.selectAll()
            self.barcode_input.setFocus()

    def update_cart_table(self):
        self.sale_table.setRowCount(0)
        total = 0
        for p_id, sku, name, qty, price in self.cart_items:
            row = self.sale_table.rowCount()
            self.sale_table.insertRow(row)
            subtotal = qty * price
            total += subtotal
            
            # Alineación: SKU centro, Articulo izquierda, Cant. centro, Subtotal derecha
            items = [
                (sku, Qt.AlignmentFlag.AlignCenter),
                (name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (str(qty), Qt.AlignmentFlag.AlignCenter),
                (f"$ {subtotal:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ]
            
            for col, (text, align) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                self.sale_table.setItem(row, col, item)
            
        discount = 0.0
        try:
            if self.pos_discount.text().strip():
                discount = float(self.pos_discount.text())
        except ValueError:
            pass
        final_total = max(0, total - discount)
        self.total_val.setText(f"$ {final_total:,.2f}")

    def clear_sale(self):
        self.cart_items = []
        self.update_cart_table()
        self.barcode_input.clear()
        self.pos_discount.clear()
        self.pos_customer.setCurrentIndex(0)

    def process_sale(self):
        if not self.cart_items: return
        
        # 1. Verificar si hay caja abierta
        open_caja = self.db.get_open_caja()
        if not open_caja:
            QMessageBox.warning(self, "Caja Cerrada", "Debe abrir caja antes de realizar ventas.")
            self.menu_list.setCurrentRow(4) # Cambiar a la pestaña de Caja
            return
            
        caja_id = open_caja[0]
        subtotal = sum(item[3] * item[4] for item in self.cart_items)
        discount = 0.0
        try:
            if self.pos_discount.text().strip():
                discount = float(self.pos_discount.text())
        except ValueError: pass
        
        total = max(0, subtotal - discount)
        
        # 2. Diálogo de Pago
        payment_dialog = PaymentDialog(total, self)
        if payment_dialog.exec():
            payment_method = payment_dialog.get_data()
            
            # items para la BD: (id, qty, price)
            db_items = [(item[0], item[3], item[4]) for item in self.cart_items]
            
            customer_id = self.pos_customer.currentData()
            ticket = self.db.add_sale(total, payment_method, db_items, caja_id=caja_id, customer_id=customer_id, discount=discount)
            if ticket:
                QMessageBox.information(self, "Venta Exitosa", f"Ticket generado: {ticket}")
                self.clear_sale()
                self.load_inventory_data()
                self.update_dashboard_data()
                self.update_global_caja_status()
                self.load_pos_customers()
            else:
                QMessageBox.critical(self, "Error", "Error al procesar la venta.")
            
    def keyPressEvent(self, event):
        # Atajo F5 para pagar - solo si estamos en la pestaña de Ventas (index 2)
        if event.key() == Qt.Key.Key_F5 and self.stack.currentIndex() == 2:
            self.process_sale()
        super().keyPressEvent(event)

    def create_purchases(self):
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # --- Cabecera ---
        header_layout = QHBoxLayout()
        title = ui.QLabel("Gestión de Entradas")
        title.setObjectName("Title")
        
        self.compra_mode = QComboBox()
        self.compra_mode.addItems(["Individual", "Combo (Paquete)"])
        self.compra_mode.setMinimumHeight(35)
        
        self.quick_mode = QCheckBox("Modo Entrada Rápida (Escáner)")
        self.quick_mode.setStyleSheet("color: #0EA5E9; font-weight: bold; font-size: 11pt;")
        
        header_layout.addWidget(title)
        header_layout.addSpacing(20)
        header_layout.addWidget(self.compra_mode)
        header_layout.addStretch()
        header_layout.addWidget(self.quick_mode)
        layout.addLayout(header_layout)
        
        # --- Stack para Modos ---
        self.compra_stack = QStackedWidget()
        layout.addWidget(self.compra_stack)
        
        self.individual_mode_widget = QWidget()
        self.individual_mode_layout = QVBoxLayout(self.individual_mode_widget)
        self.individual_mode_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Formulario INDIVIDUAL en Dos Columnas ---
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        
        # Columna 1: Datos del Producto
        left_column = ui.Card()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        left_title = ui.QLabel("📦 Información del Producto")
        left_title.setStyleSheet("font-weight: bold; color: #0EA5E9; font-size: 12pt; margin-bottom: 10px;")
        left_layout.addWidget(left_title)
        
        prod_form = QFormLayout()
        prod_form.setSpacing(15)
        
        self.compra_product = ui.QLineEdit()
        self.compra_product.setPlaceholderText("Escanee el código o escriba el nombre/SKU...")
        self.compra_product.setMinimumHeight(40)
        self.compra_product.returnPressed.connect(self.handle_compra_scan)

        self.compra_product_completer_model = QStringListModel()
        self.compra_product_completer = QCompleter(self.compra_product_completer_model, self)
        self.compra_product_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.compra_product_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.compra_product_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.compra_product.setCompleter(self.compra_product_completer)

        self.compra_product.textEdited.connect(self.on_compra_product_text_edited)
        self.compra_product_completer.activated.connect(self.on_compra_product_selected)
        
        self.compra_qty = ui.QLineEdit()
        self.compra_qty.setPlaceholderText("Ej: 10")
        self.compra_qty.setMinimumHeight(40)
        
        self.compra_cost = ui.QLineEdit()
        self.compra_cost.setPlaceholderText("0.00")
        self.compra_cost.setMinimumHeight(40)
        
        self.compra_tax = ui.QLineEdit()
        self.compra_tax.setPlaceholderText("Ej: 8.25")
        self.compra_tax.setText("0")
        self.compra_tax.setMinimumHeight(40)

        self.compra_profit_pct = ui.QLineEdit()
        self.compra_profit_pct.setPlaceholderText("Ej: 20")
        self.compra_profit_pct.setText("0")
        self.compra_profit_pct.setMinimumHeight(40)

        self.lbl_suggested_price = ui.QLabel("Sug: $ 0.00")
        self.lbl_suggested_price.setStyleSheet("color: #0EA5E9; font-weight: bold;")
        self.btn_apply_suggested = ui.TableActionButton("Aplicar")
        self.btn_apply_suggested.clicked.connect(self.apply_suggested_price)

        # Conectar señales después de inicializar todos los campos dependientes
        self.compra_cost.textChanged.connect(self.update_compra_totals)
        self.compra_tax.textChanged.connect(self.update_compra_totals)
        self.compra_profit_pct.textChanged.connect(self.update_compra_totals)

        self.compra_origin_state = QComboBox()
        self.compra_origin_state.addItems(US_STATES)
        self.compra_origin_state.setCurrentText("TX") # Default
        self.compra_origin_state.setMinimumHeight(40)

        self.compra_type = QComboBox()
        self.compra_type.addItems(["Física", "En Línea"])
        self.compra_type.setMinimumHeight(40)
        
        from PyQt6.QtWidgets import QDateEdit
        from datetime import datetime
        self.compra_delivery_date = QDateEdit()
        self.compra_delivery_date.setCalendarPopup(True)
        self.compra_delivery_date.setDate(datetime.now().date())
        self.compra_delivery_date.setEnabled(False)
        self.compra_delivery_date.setMinimumHeight(40)
        self.compra_type.currentTextChanged.connect(lambda text: self.compra_delivery_date.setEnabled(text == "En Línea"))

        self.compra_selling_price = ui.QLineEdit()
        self.compra_selling_price.setPlaceholderText("Nuevo precio de venta...")
        self.compra_selling_price.setMinimumHeight(40)
        
        prod_form.addRow("Producto/SKU:", self.compra_product)
        prod_form.addRow("Cantidad:", self.compra_qty)
        self.compra_qty.textChanged.connect(self.update_compra_totals)
        prod_form.addRow("Costo Unitario ($):", self.compra_cost)
        prod_form.addRow("Impuesto (%):", self.compra_tax)
        prod_form.addRow("Ganancia (%):", self.compra_profit_pct)
        prod_form.addRow("Estado Origen:", self.compra_origin_state)
        prod_form.addRow("Tipo de Compra:", self.compra_type)
        prod_form.addRow("Estimado de Entrega:", self.compra_delivery_date)

        # Precio Sugerido y Botón Aplicar
        suggested_layout = QHBoxLayout()
        suggested_layout.addWidget(self.lbl_suggested_price)
        suggested_layout.addWidget(self.btn_apply_suggested)
        suggested_layout.addStretch()

        prod_form.addRow("Precio Sugerido:", suggested_layout)
        prod_form.addRow("Precio Venta ($):", self.compra_selling_price)

        # Resumen de Costos dinámico
        self.lbl_compra_total = ui.QLabel("Costo Total: $ 0.00")
        self.lbl_compra_total.setStyleSheet("font-weight: bold; color: #F59E0B; font-size: 11pt; margin-top: 10px;")
        left_layout.addWidget(self.lbl_compra_total)
        
        left_layout.addLayout(prod_form)
        left_layout.addStretch()
        
        # Columna 2: Detalles de Pago y Proveedor
        right_column = ui.Card()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        right_title = ui.QLabel("💳 Detalles de Transacción")
        right_title.setStyleSheet("font-weight: bold; color: #10B981; font-size: 12pt; margin-bottom: 10px;")
        right_layout.addWidget(right_title)
        
        pay_form = QFormLayout()
        pay_form.setSpacing(15)
        
        self.compra_supplier = QComboBox()
        self.compra_supplier.setMinimumHeight(35)
        
        self.compra_responsible = QComboBox()
        self.compra_responsible.setEditable(True)
        self.compra_responsible.setMinimumHeight(35)
        
        self.payment_mode = QComboBox()
        self.payment_mode.addItems(["Efectivo", "Tarjeta de Crédito"])
        self.payment_mode.setMinimumHeight(35)
        
        self.card_selector = QComboBox()
        self.card_selector.setEnabled(False)
        self.card_selector.setMinimumHeight(35)
        
        self.is_paid = QCheckBox("Marcar como pagado inmediatamente")
        self.is_paid.setChecked(True)
        self.is_paid.setStyleSheet("margin-top: 5px;")
        
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(datetime.now().date())
        self.due_date_edit.setEnabled(False)
        self.due_date_edit.setMinimumHeight(35)
        
        self.is_return = QCheckBox("Esta entrada es una devolución")
        
        pay_form.addRow("Proveedor:", self.compra_supplier)
        pay_form.addRow("Responsable:", self.compra_responsible)
        pay_form.addRow("Método de Pago:", self.payment_mode)
        pay_form.addRow("Tarjeta:", self.card_selector)
        pay_form.addRow(self.is_paid)
        pay_form.addRow("Fecha Límite Pago:", self.due_date_edit)
        pay_form.addRow(self.is_return)
        
        right_layout.addLayout(pay_form)
        right_layout.addStretch()
        
        columns_layout.addWidget(left_column)
        columns_layout.addWidget(right_column)
        
        self.individual_mode_layout.addLayout(columns_layout)
        
        # --- Botón de Acción ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = ui.PrimaryButton("🚀 REGISTRAR COMPRA INDIVIDUAL")
        btn_save.setFixedWidth(300)
        btn_save.setFixedHeight(50)
        btn_save.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #0EA5E9;")
        btn_save.clicked.connect(self.register_purchase)
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()
        
        self.individual_mode_layout.addLayout(btn_layout)
        self.individual_mode_layout.addStretch(1)
        
        self.init_combo_ui()
        self.compra_stack.addWidget(self.individual_mode_widget)
        self.compra_stack.addWidget(self.combo_mode_widget)
        
        self.compra_mode.currentTextChanged.connect(
            lambda t: self.compra_stack.setCurrentIndex(0 if t == "Individual" else 1)
        )
        
        # Conexiones Lógicas para una experiencia más fluida
        def on_payment_mode_change():
            is_card = self.payment_mode.currentText() == "Tarjeta de Crédito"
            self.card_selector.setEnabled(is_card)
            self.is_paid.setEnabled(is_card)
            self.is_return.setEnabled(is_card)
            
            if not is_card:
                # Para Efectivo, forzar valores por defecto y deshabilitar controles de crédito
                self.is_paid.setChecked(True)
                self.due_date_edit.setEnabled(False)
                self.is_return.setChecked(False)
                self.card_selector.setCurrentIndex(-1)
            else:
                # Para Tarjeta, la fecha límite depende de si está pagado o no
                self.due_date_edit.setEnabled(not self.is_paid.isChecked())

        self.payment_mode.currentTextChanged.connect(on_payment_mode_change)
        
        def on_paid_change():
            # La fecha límite solo tiene sentido si NO se ha pagado aún (compras a crédito)
            if self.payment_mode.currentText() == "Tarjeta de Crédito":
                self.due_date_edit.setEnabled(not self.is_paid.isChecked())
            else:
                self.due_date_edit.setEnabled(False)

        self.is_paid.stateChanged.connect(on_paid_change)

        # Inicializar estado
        on_payment_mode_change()

        scroll.setWidget(page)
        return scroll


    def init_combo_ui(self):
        self.combo_mode_widget = QWidget()
        layout = QVBoxLayout(self.combo_mode_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # --- FILA 1: Configuración General y Transacción ---
        header_columns = QHBoxLayout()
        header_columns.setSpacing(20)

        # Columna 1: Opciones del Combo
        card_options = ui.Card()
        options_layout = QVBoxLayout(card_options)
        options_layout.setContentsMargins(20, 20, 20, 20)
        
        options_title = ui.QLabel("📦 Configuración del Paquete")
        options_title.setStyleSheet("font-weight: bold; color: #0EA5E9; font-size: 11pt; margin-bottom: 5px;")
        options_layout.addWidget(options_title)

        form_opt = QFormLayout()
        form_opt.setSpacing(12)

        self.combo_name = ui.QLineEdit()
        self.combo_name.setPlaceholderText("Nombre identificador (ej: Lote Herramientas Mayo)")
        self.combo_name.setMinimumHeight(40)
        
        self.combo_total_cost = ui.QLineEdit()
        self.combo_total_cost.setPlaceholderText("0.00")
        self.combo_total_cost.setMinimumHeight(40)
        self.combo_total_cost.textChanged.connect(self.update_combo_table_calculations)
        
        self.combo_method = QComboBox()
        self.combo_method.addItems(["Equitativa", "Manual (%)"])
        self.combo_method.setMinimumHeight(40)
        self.combo_method.currentTextChanged.connect(self.on_combo_method_change)
        
        form_opt.addRow("Nombre Combo:", self.combo_name)
        form_opt.addRow("Inversión Total ($):", self.combo_total_cost)
        form_opt.addRow("Criterio Costo:", self.combo_method)
        options_layout.addLayout(form_opt)
        options_layout.addStretch()

        # Columna 2: Detalles de Transacción
        card_trans = ui.Card()
        trans_layout = QVBoxLayout(card_trans)
        trans_layout.setContentsMargins(20, 20, 20, 20)
        
        trans_title = ui.QLabel("💳 Datos de la Operación")
        trans_title.setStyleSheet("font-weight: bold; color: #10B981; font-size: 11pt; margin-bottom: 5px;")
        trans_layout.addWidget(trans_title)

        form_trans = QFormLayout()
        form_trans.setSpacing(12)

        self.combo_supplier = QComboBox()
        self.combo_supplier.setMinimumHeight(40)
        
        self.combo_responsible = QComboBox()
        self.combo_responsible.setEditable(True)
        self.combo_responsible.setMinimumHeight(40)
        
        self.combo_payment_mode = QComboBox()
        self.combo_payment_mode.addItems(["Efectivo", "Tarjeta de Crédito"])
        self.combo_payment_mode.setMinimumHeight(40)
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Física", "En Línea"])
        self.combo_type.setMinimumHeight(40)

        form_trans.addRow("Proveedor:", self.combo_supplier)
        form_trans.addRow("Responsable:", self.combo_responsible)
        form_trans.addRow("Método Pago:", self.combo_payment_mode)
        form_trans.addRow("Tipo Compra:", self.combo_type)

        trans_layout.addLayout(form_trans)
        trans_layout.addStretch()

        header_columns.addWidget(card_options)
        header_columns.addWidget(card_trans)
        layout.addLayout(header_columns)

        # --- FILA 2: Detalle de Productos ---
        card_items = ui.Card()
        items_layout = QVBoxLayout(card_items)
        items_layout.setContentsMargins(20, 20, 20, 20)
        
        items_title = ui.QLabel("🛒 Productos en el Paquete")
        items_title.setStyleSheet("font-weight: bold; color: #F59E0B; font-size: 11pt; margin-bottom: 15px;")
        items_layout.addWidget(items_title)

        # Búsqueda integrada arriba de la tabla
        search_box = QHBoxLayout()
        search_label = ui.QLabel("🔍 Buscar:")
        search_label.setStyleSheet("color: #94A3B8; font-weight: bold;")
        self.combo_product_search = ui.QLineEdit()
        self.combo_product_search.setMinimumHeight(45)
        self.combo_product_search.setPlaceholderText("Escanee código de barras o escriba nombre del producto...")
        self.combo_product_search.setStyleSheet("font-size: 11pt; background-color: #0F172A; border: 2px solid #334155;")
        self.combo_product_search.returnPressed.connect(self.add_product_to_combo)
        
        self.combo_product_completer_model = QStringListModel()
        self.combo_product_completer = QCompleter(self.combo_product_completer_model, self)
        self.combo_product_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.combo_product_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.combo_product_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.combo_product_search.setCompleter(self.combo_product_completer)
        
        self.combo_product_search.textEdited.connect(self.on_combo_product_text_edited)
        self.combo_product_completer.activated.connect(self.on_combo_product_selected)
        
        self.btn_combo_new_product = ui.PrimaryButton("+ Nuevo")
        self.btn_combo_new_product.setFixedWidth(100)
        self.btn_combo_new_product.setMinimumHeight(45)
        self.btn_combo_new_product.clicked.connect(self.combo_create_new_product)
        
        search_box.addWidget(search_label)
        search_box.addWidget(self.combo_product_search)
        search_box.addWidget(self.btn_combo_new_product)
        items_layout.addLayout(search_box)
        items_layout.addSpacing(10)
        
        self.combo_table = QTableWidget(0, 6)
        self.combo_table.setHorizontalHeaderLabels(["ID", "SKU", "Descripción", "Cant.", "Peso (%)", "Costo/Unid. Calc."])
        self.combo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.combo_table.verticalHeader().setDefaultSectionSize(45)
        self.combo_table.setMinimumHeight(300)
        self.combo_table.itemChanged.connect(self.on_combo_table_item_changed)
        items_layout.addWidget(self.combo_table)

        # Resumen de totales de la tabla
        self.lbl_combo_summary = ui.QLabel("Suma Peso: 0% | Items Totales: 0")
        self.lbl_combo_summary.setStyleSheet("color: #94A3B8; font-weight: bold; margin-top: 5px;")
        items_layout.addWidget(self.lbl_combo_summary)
        
        layout.addWidget(card_items)
        
        self.combo_items = [] # (p_id, sku, name)
        
        # --- Botón de Acción Final ---
        btn_action_layout = QHBoxLayout()
        btn_action_layout.addStretch()
        btn_save = ui.PrimaryButton("🚀 REGISTRAR COMPRA POR COMBO")
        btn_save.setFixedWidth(400)
        btn_save.setFixedHeight(55)
        btn_save.setStyleSheet("font-size: 13pt; letter-spacing: 1px;")
        btn_save.clicked.connect(self.register_combo_purchase)
        btn_action_layout.addWidget(btn_save)
        btn_action_layout.addStretch()
        
        layout.addLayout(btn_action_layout)
        layout.addStretch()

    def combo_create_new_product(self):
        dialog = NewProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_inventory_data()
            new_sku = dialog.sku.text().strip()
            new_p = self.db.get_product_by_sku_or_name(new_sku)
            if new_p:
                self.combo_items.append((new_p[0], new_p[4], new_p[1]))
                row = self.combo_table.rowCount()
                self.combo_table.blockSignals(True)
                self.combo_table.insertRow(row)
                
                # ID
                self.combo_table.setItem(row, 0, QTableWidgetItem(str(new_p[0])))
                # SKU
                self.combo_table.setItem(row, 1, QTableWidgetItem(new_p[4]))
                # Producto
                self.combo_table.setItem(row, 2, QTableWidgetItem(new_p[1]))
                # Cantidad (Default 1) - Editable
                it_qty = QTableWidgetItem("1")
                self.combo_table.setItem(row, 3, it_qty)
                # Peso % (Default 0) - Editable solo si es Manual
                it_peso = QTableWidgetItem("0")
                self.combo_table.setItem(row, 4, it_peso)
                # Costo Calc (Read-only)
                it_cost = QTableWidgetItem("0.00")
                it_cost.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.combo_table.setItem(row, 5, it_cost)
                
                self.combo_table.blockSignals(False)
                self.update_combo_table_calculations()

    def on_combo_method_change(self):
        method = self.combo_method.currentText()
        # Hab/Deshab la col 4 (Peso %)
        self.update_combo_table_calculations()

    def add_product_to_combo(self):
        query = self.combo_product_search.text().strip()
        if not query: return
        p = self.db.get_product_by_sku_or_name(query)
        if p:
            self.combo_items.append((p[0], p[4], p[1]))
            row = self.combo_table.rowCount()
            self.combo_table.blockSignals(True)
            self.combo_table.insertRow(row)
            
            # ID
            self.combo_table.setItem(row, 0, QTableWidgetItem(str(p[0])))
            # SKU
            self.combo_table.setItem(row, 1, QTableWidgetItem(p[4]))
            # Producto
            self.combo_table.setItem(row, 2, QTableWidgetItem(p[1]))
            # Cantidad (Default 1) - Editable
            it_qty = QTableWidgetItem("1")
            self.combo_table.setItem(row, 3, it_qty)
            # Peso % (Default 0) - Editable solo si es Manual
            it_peso = QTableWidgetItem("0")
            self.combo_table.setItem(row, 4, it_peso)
            # Costo Calc (Read-only)
            it_cost = QTableWidgetItem("0.00")
            it_cost.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.combo_table.setItem(row, 5, it_cost)
            
            self.combo_table.blockSignals(False)
            self.update_combo_table_calculations()
            self.combo_product_search.clear()
        else:
            reply = QMessageBox.question(
                self, 
                "Producto No Encontrado", 
                f"El producto con SKU o nombre '{query}' no existe.\n\n¿Desea crearlo ahora para agregarlo al combo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Determinar si query parece un SKU o nombre
                is_numeric_sku = query.isalnum() and len(query) >= 3 and any(char.isdigit() for char in query)
                pre_sku = query if is_numeric_sku else ""
                
                dialog = NewProductDialog(self, pre_sku=pre_sku)
                if not is_numeric_sku:
                    dialog.name.setText(query)
                    
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.load_inventory_data()
                    new_sku = dialog.sku.text().strip()
                    new_p = self.db.get_product_by_sku_or_name(new_sku)
                    if new_p:
                        self.combo_items.append((new_p[0], new_p[4], new_p[1]))
                        row = self.combo_table.rowCount()
                        self.combo_table.blockSignals(True)
                        self.combo_table.insertRow(row)
                        
                        # ID
                        self.combo_table.setItem(row, 0, QTableWidgetItem(str(new_p[0])))
                        # SKU
                        self.combo_table.setItem(row, 1, QTableWidgetItem(new_p[4]))
                        # Producto
                        self.combo_table.setItem(row, 2, QTableWidgetItem(new_p[1]))
                        # Cantidad (Default 1) - Editable
                        it_qty = QTableWidgetItem("1")
                        self.combo_table.setItem(row, 3, it_qty)
                        # Peso % (Default 0) - Editable solo si es Manual
                        it_peso = QTableWidgetItem("0")
                        self.combo_table.setItem(row, 4, it_peso)
                        # Costo Calc (Read-only)
                        it_cost = QTableWidgetItem("0.00")
                        it_cost.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                        self.combo_table.setItem(row, 5, it_cost)
                        
                        self.combo_table.blockSignals(False)
                        self.update_combo_table_calculations()
                        self.combo_product_search.clear()
            else:
                self.combo_product_search.selectAll()

    def on_combo_table_item_changed(self, item):
        if item.column() in (3, 4):
            self.update_combo_table_calculations()

    def update_combo_table_calculations(self):
        # Calculate
        try: total_cost = float(self.combo_total_cost.text())
        except ValueError: total_cost = 0.0
        
        method = self.combo_method.currentText()
        rows = self.combo_table.rowCount()
        
        if rows == 0:
            self.lbl_combo_summary.setText("Suma Peso: 0% | Items Totales: 0")
            return
        
        sum_qty = 0
        sum_pct = 0.0
        
        for r in range(rows):
            try: 
                qty_val = int(self.combo_table.item(r, 3).text())
                sum_qty += qty_val
            except: pass
            
            if method == "Manual (%)":
                try: 
                    pct_val = float(self.combo_table.item(r, 4).text())
                    sum_pct += pct_val
                except: pass
        
        # Actualizar etiqueta de resumen
        summary_text = f"Suma Peso: {sum_pct}% | Items Totales: {sum_qty}"
        if method == "Manual (%)" and abs(sum_pct - 100.0) > 0.01:
            self.lbl_combo_summary.setStyleSheet("color: #EF4444; font-weight: bold; margin-top: 5px;")
            self.lbl_combo_summary.setText(f"⚠️ {summary_text} (Debe ser 100%)")
        else:
            self.lbl_combo_summary.setStyleSheet("color: #94A3B8; font-weight: bold; margin-top: 5px;")
            self.lbl_combo_summary.setText(summary_text)

        self.combo_table.blockSignals(True)
        for r in range(rows):
            try: qty = int(self.combo_table.item(r, 3).text())
            except: qty = 1
            
            # Reset background colors
            self.combo_table.item(r, 4).setBackground(QBrush(QColor("transparent")))
            
            cost = 0.0
            if method == "Equitativa":
                if sum_qty > 0:
                    cost_per_piece = total_cost / sum_qty
                    cost = cost_per_piece
                self.combo_table.item(r, 4).setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled) # Lock %
                self.combo_table.item(r, 4).setText("0")
            else:
                self.combo_table.item(r, 4).setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable) # Unlock %
                try: pct = float(self.combo_table.item(r, 4).text())
                except: pct = 0.0
                
                if qty > 0:
                    cost = (total_cost * (pct / 100.0)) / qty
                
                # Highlight if manual sum is wrong
                if abs(sum_pct - 100.0) > 0.01:
                    self.combo_table.item(r, 4).setBackground(QBrush(QColor("#450a0a"))) # Dark red background
                    
            self.combo_table.item(r, 5).setText(f"{cost:.2f}")
        self.combo_table.blockSignals(False)

    def register_combo_purchase(self):
        name = self.combo_name.text().strip()
        try: total_cost = float(self.combo_total_cost.text())
        except: total_cost = 0.0
        method = self.combo_method.currentText()
        
        if not name or total_cost <= 0:
            QMessageBox.warning(self, "Error", "Nombre e importe total son requeridos.")
            return
            
        rows = self.combo_table.rowCount()
        if rows == 0:
            QMessageBox.warning(self, "Error", "Agregue al menos un producto al combo.")
            return
            
        items_db = []
        sum_pct = 0.0
        
        for r in range(rows):
            p_id = int(self.combo_table.item(r, 0).text())
            try: qty = int(self.combo_table.item(r, 3).text())
            except: qty = 0
            if qty <= 0:
                QMessageBox.warning(self, "Error", "Todas las cantidades deben ser > 0.")
                return
                
            try: u_cost = float(self.combo_table.item(r, 5).text())
            except: u_cost = 0.0
            
            if method == "Manual (%)":
                try: pct = float(self.combo_table.item(r, 4).text())
                except: pct = 0.0
                sum_pct += pct
                
            items_db.append({
                'product_id': p_id,
                'quantity': qty,
                'unit_cost': u_cost,
                'new_selling_price': None # Could be expanded
            })
            
        if method == "Manual (%)" and abs(sum_pct - 100.0) > 0.01:
            QMessageBox.warning(self, "Error", f"La suma de porcentajes manuales no es 100% (Actual: {sum_pct}%)")
            return
            
        supplier_id = self.combo_supplier.currentData()
        pay_mode = self.combo_payment_mode.currentText()
        buyer = self.combo_responsible.currentText()
        state = "TX" 
        p_type = self.combo_type.currentText()
        d_status = "Entregado" if p_type == "Física" else "Pendiente"
        
        ref = self.db.add_combo_purchase(name, total_cost, method, items_db, supplier_id, pay_mode, buyer, state, p_type, None, d_status)
        if ref:
            QMessageBox.information(self, "Éxito", f"Combo '{name}' registrado con éxito.")
            self.combo_name.clear()
            self.combo_total_cost.clear()
            self.combo_table.setRowCount(0)
            self.combo_items = []
            self.load_inventory_data()
            self.update_dashboard_data()
        else:
            QMessageBox.critical(self, "Error", "Fallo al registrar combo.")


    def update_compra_totals(self):
        """Calcula el costo total incluyendo impuestos y el precio sugerido en tiempo real."""
        try:
            qty = int(self.compra_qty.text()) if self.compra_qty.text() else 0
            cost = float(self.compra_cost.text()) if self.compra_cost.text() else 0.0
            tax_pct = float(self.compra_tax.text()) if self.compra_tax.text() else 0.0
            profit_pct = float(self.compra_profit_pct.text()) if self.compra_profit_pct.text() else 0.0
            
            # 1. Costo Total (Inversión)
            base = qty * cost
            total = base * (1 + tax_pct / 100.0)
            self.lbl_compra_total.setText(f"Costo Total: $ {total:,.2f}")

            # 2. Precio Sugerido (Venta)
            # Sugerido = Costo + (Costo * Impuesto%) + (Costo * Ganancia%)
            suggested = cost * (1 + (tax_pct + profit_pct) / 100.0)
            self.lbl_suggested_price.setText(f"Sug: $ {suggested:,.2f}")
            
        except ValueError:
            self.lbl_compra_total.setText("Costo Total: Error")
            self.lbl_suggested_price.setText("Sug: Error")

    def apply_suggested_price(self):
        """Aplica el precio sugerido al campo de precio de venta."""
        try:
            cost = float(self.compra_cost.text()) if self.compra_cost.text() else 0.0
            tax_pct = float(self.compra_tax.text()) if self.compra_tax.text() else 0.0
            profit_pct = float(self.compra_profit_pct.text()) if self.compra_profit_pct.text() else 0.0
            
            suggested = cost * (1 + (tax_pct + profit_pct) / 100.0)
            self.compra_selling_price.setText(f"{suggested:.2f}")
        except ValueError:
            pass

    def register_purchase(self):
        query = self.compra_product.text()
        qty_text = self.compra_qty.text()
        cost_text = self.compra_cost.text()
        
        if not query or not qty_text or not cost_text:
            QMessageBox.warning(self, "Error", "Por favor llene todos los campos.")
            return
            
        try:
            qty = int(qty_text)
            cost = float(cost_text)
            
            # Buscar producto
            product = self.db.get_product_by_sku_or_name(query)
            if not product:
                reply = QMessageBox.question(self, "Producto No Encontrado", 
                                           f"El producto '{query}' no existe en el inventario.\n\n"
                                           "¿Desea registrarlo como nuevo producto ahora?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    # Abrir diálogo de nuevo producto con datos pre-llenados
                    # Usamos los textos actuales de los campos de costo y venta
                    dialog = NewProductDialog(self, pre_sku=query, 
                                            pre_cost=self.compra_cost.text(), 
                                            pre_price=self.compra_selling_price.text())
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # Re-buscar el producto recién creado para obtener su ID
                        product = self.db.get_product_by_sku_or_name(query)
                        if not product: return
                    else:
                        return # Usuario canceló el registro del producto
                else:
                    return # Usuario no quiso registrar el producto
                
            p_id, p_name, _, _, _ = product
            
            # Obtener datos adicionales
            supplier_idx = self.compra_supplier.currentData()
            if supplier_idx is None:
                QMessageBox.warning(self, "Error", "Por favor seleccione un proveedor o añada uno en Configuración.")
                return
                
            responsible = self.compra_responsible.currentText()
            method = "Credit" if self.payment_mode.currentText() == "Tarjeta de Crédito" else "Cash"
            card = self.card_selector.currentText() if method == "Credit" else None
            status = 1 if self.is_paid.isChecked() else 0
            is_ret = 1 if self.is_return.isChecked() else 0
            due = self.due_date_edit.date().toString("yyyy-MM-dd") if not self.is_paid.isChecked() else None
            
            # Nuevos campos
            origin_state = self.compra_origin_state.currentText()
            tax_pct = float(self.compra_tax.text()) if self.compra_tax.text() else 0.0
            new_price = float(self.compra_selling_price.text()) if self.compra_selling_price.text() else None
            
            p_type = self.compra_type.currentText()
            d_date = self.compra_delivery_date.date().toString("yyyy-MM-dd") if p_type == "En Línea" else None
            d_status = "Pendiente" if p_type == "En Línea" else "Entregado"
            
            if self.db.add_purchase(p_id, qty, cost, supplier_idx, method, responsible, 
                                   is_return=is_ret, card_name=card, is_paid=status, 
                                   due_date=due, origin_state=origin_state, 
                                   tax_percentage=tax_pct, new_selling_price=new_price,
                                   purchase_type=p_type, delivery_date=d_date, delivery_status=d_status):
                QMessageBox.information(self, "Éxito", f"Compra registrada para {p_name}.")
                self.update_dashboard_data()
                self.load_inventory_data()
                # Limpiar campos
                self.compra_product.clear()
                self.compra_qty.clear()
                self.compra_cost.clear()
                self.compra_tax.setText("0")
                self.compra_profit_pct.setText("0")
                self.compra_selling_price.clear()
                self.compra_type.setCurrentIndex(0)
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar la compra en la base de datos.")
                
        except ValueError:
            QMessageBox.critical(self, "Error", "Cantidad y Costo deben ser valores numéricos.")

    def on_compra_product_text_edited(self, text):
        if not text or len(text) < 2:
            self.compra_product_completer_model.setStringList([])
            return
            
        results = self.db.search_products(text, limit=15)
        suggestions = []
        for sku, name, _, _, _ in results:
            suggestions.append(f"{sku} | {name}")
            
        self.compra_product_completer_model.setStringList(suggestions)
        self.compra_product_completer.complete()

    def on_compra_product_selected(self, text):
        if " | " not in text:
            return
            
        sku = text.split(" | ")[0]
        product = self.db.get_product_by_sku_or_name(sku)
        
        if product:
            p_id, p_name, cost, selling_price, actual_sku = product
            
            # Obtener el impuesto (no retornado por get_product_by_sku_or_name)
            tax_pct = 0.0
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT tax_percentage FROM products WHERE id=?", (p_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        tax_pct = row[0]
            except:
                pass

            self.compra_product.blockSignals(True)
            self.compra_product.setText(actual_sku)
            self.compra_product.blockSignals(False)
            
            self.compra_qty.setText("1")
            self.compra_cost.setText(f"{cost:.2f}")
            self.compra_tax.setText(f"{tax_pct:.2f}")
            self.compra_selling_price.setText(f"{selling_price:.2f}")
            self.compra_profit_pct.setText("0")
            
            self.update_compra_totals()

    def on_combo_product_text_edited(self, text):
        if not text or len(text) < 2:
            self.combo_product_completer_model.setStringList([])
            return
            
        results = self.db.search_products(text, limit=15)
        suggestions = []
        for sku, name, _, _, _ in results:
            suggestions.append(f"{sku} | {name}")
            
        self.combo_product_completer_model.setStringList(suggestions)
        self.combo_product_completer.complete()

    def on_combo_product_selected(self, text):
        if " | " not in text:
            return
        sku = text.split(" | ")[0]
        self.combo_product_search.setText(sku)
        self.add_product_to_combo()

    def handle_compra_scan(self):
        """Maneja el evento de escaneo en la sección de compras."""
        if self.quick_mode.isChecked():
            query = self.compra_product.text()
            if not query: return
            
            product = self.db.get_product_by_sku_or_name(query)
            if product:
                p_id, p_name, cost, _, _ = product
                # Valores por defecto para entrada rápida
                qty = 1 
                # Si el campo de cantidad tiene algo, usarlo
                if self.compra_qty.text():
                    try: qty = int(self.compra_qty.text())
                    except: pass
                
                # Usar el costo que ya tiene el producto en la BD
                supplier_idx = self.compra_supplier.currentData()
                responsible = self.compra_responsible.currentText()
                
                if self.db.add_purchase(p_id, qty, cost, supplier_idx, "Cash", responsible):
                    self.load_inventory_data()
                    self.update_dashboard_data()
                    self.compra_product.clear()
                    # Feedback visual breve en la barra de estado si existiera, o simple limpieza
                else:
                    QMessageBox.warning(self, "Error", "Error al registrar la entrada rápida.")
            else:
                QMessageBox.warning(self, "Error", "Producto no encontrado.")



    def open_new_product_dialog(self):
        dialog = NewProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_inventory_data()
            self.update_dashboard_data()

    def on_inventory_double_click(self, item):
        product_id = item.data(Qt.ItemDataRole.UserRole)
        if product_id:
            self.open_edit_product_dialog(product_id)

    def open_edit_product_dialog(self, product_id):
        dialog = EditProductDialog(product_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_inventory_data()
            self.update_dashboard_data()

    def create_caja(self):
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        self.caja_page = QWidget()
        self.caja_layout = QVBoxLayout(self.caja_page)
        self.caja_layout.setContentsMargins(30, 30, 30, 30)
        self.caja_layout.setSpacing(20)
        
        scroll.setWidget(self.caja_page)
        return scroll

    def update_caja_view(self):
        # Limpiar layout
        while self.caja_layout.count():
            item = self.caja_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        open_caja = self.db.get_open_caja()
        
        if not open_caja:
            # --- VISTA: APERTURA DE CAJA ---
            title = ui.QLabel("Apertura de Caja")
            title.setObjectName("Title")
            self.caja_layout.addWidget(title)
            
            card = ui.Card()
            card.setFixedWidth(400)
            card_layout = QVBoxLayout(card)
            
            lbl = ui.QLabel("Ingrese el monto inicial de efectivo en caja:")
            lbl.setWordWrap(True)
            self.monto_apertura = ui.QLineEdit()
            self.monto_apertura.setPlaceholderText("Ej: 1000.00")
            self.monto_apertura.setMinimumHeight(45)
            
            btn_open = ui.PrimaryButton("Abrir Caja ahora")
            btn_open.clicked.connect(self.open_caja_action)
            
            card_layout.addWidget(lbl)
            card_layout.addWidget(self.monto_apertura)
            card_layout.addWidget(btn_open)
            
            self.caja_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
            self.caja_layout.addStretch()
        else:
            # --- VISTA: CAJA ACTIVA ---
            c_id, m_inicial, f_apertura, _, _, _, _ = open_caja
            
            header = QHBoxLayout()
            title = ui.QLabel(f"Caja Activa (Abierta: {f_apertura})")
            title.setObjectName("Title")
            header.addWidget(title)
            header.addStretch()
            
            self.caja_layout.addLayout(header)
            
            # Formatear Resumen Actual
            totals = self.db.get_caja_totals(c_id)
            sales = totals['sales']
            movs = totals['movements']
            
            total_efectivo = sales.get('Cash', 0)
            total_tarjeta = sales.get('Card', 0)
            ingresos = movs.get('ingreso', 0)
            retiros = movs.get('retiro', 0)
            
            esperado = m_inicial + total_efectivo + ingresos - retiros
            
            cards_layout = QHBoxLayout()
            
            def create_metric_card(title, value, color):
                c = ui.Card()
                l = QVBoxLayout(c)
                t = ui.QLabel(title)
                t.setObjectName("Secondary")
                v = ui.QLabel(f"$ {value:,.2f}")
                v.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {color};")
                l.addWidget(t)
                l.addWidget(v)
                return c

            cards_layout.addWidget(create_metric_card("Efectivo Ventas", total_efectivo, "#10B981"))
            cards_layout.addWidget(create_metric_card("Tarjeta / Otros", total_tarjeta, "#0EA5E9"))
            cards_layout.addWidget(create_metric_card("Ingresos / Retiros", ingresos - retiros, "#F59E0B"))
            cards_layout.addWidget(create_metric_card("Efectivo Esperado", esperado, "#8B5CF6"))
            
            self.caja_layout.addLayout(cards_layout)
            
            # Botones de Acción
            btns_layout = QHBoxLayout()
            btn_in = ui.PrimaryButton("+ Ingreso")
            btn_in.clicked.connect(lambda: self.add_movement_action('ingreso'))
            
            btn_out = ui.AlertButton("- Retiro")
            btn_out.clicked.connect(lambda: self.add_movement_action('retiro'))
            
            btn_corte = ui.PrimaryButton("Realizar Corte (Cerrar Caja)")
            btn_corte.setStyleSheet("background-color: #F97316; height: 50px; font-weight: bold;")
            btn_corte.clicked.connect(self.close_caja_action)
            
            btns_layout.addWidget(btn_in)
            btns_layout.addWidget(btn_out)
            btns_layout.addStretch()
            btns_layout.addWidget(btn_corte)
            
            self.caja_layout.addLayout(btns_layout)
            
            # Tabla de Movimientos del Día (Ventas)
            lbl_movs = ui.QLabel("Descripción Detallada de las Ventas del Día")
            lbl_movs.setObjectName("Secondary")
            self.caja_layout.addWidget(lbl_movs)
            
            sales_table = QTableWidget(0, 4)
            sales_table.setHorizontalHeaderLabels(["Hora/Fecha", "Ticket", "Método", "Total"])
            sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            sales_table.verticalHeader().setVisible(False)
            sales_table.setMinimumHeight(200)
            
            caja_sales = self.db.get_caja_sales(c_id)
            sales_table.setRowCount(len(caja_sales))
            for i, sale in enumerate(caja_sales):
                s_date, s_ticket, s_total, s_method = sale
                sales_table.setItem(i, 0, QTableWidgetItem(s_date))
                sales_table.setItem(i, 1, QTableWidgetItem(s_ticket))
                sales_table.setItem(i, 2, QTableWidgetItem(s_method))
                
                total_item = QTableWidgetItem(f"${s_total:,.2f}")
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                sales_table.setItem(i, 3, total_item)
                
            self.caja_layout.addWidget(sales_table)
            self.caja_layout.addStretch()
            
            # --- SECCIÓN: HISTORIAL DE CORTES ---
            hist_title = ui.QLabel("Historial de Cortes Recientes")
            hist_title.setStyleSheet("font-weight: bold; margin-top: 20px; color: #94A3B8;")
            self.caja_layout.addWidget(hist_title)
            
            self.hist_table = QTableWidget(0, 5)
            self.hist_table.setHorizontalHeaderLabels(["Apertura", "Cierre", "Ventas", "Diferencia", "Estado"])
            self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.hist_table.setStyleSheet("background-color: #1E293B; color: white;")
            self.caja_layout.addWidget(self.hist_table)
            self.load_caja_history()

    def load_caja_history(self):
        history = self.db.get_caja_history()
        self.hist_table.setRowCount(0)
        for h in history[:10]: # Últimos 10
            # id, m_inicial, f_apertura, f_cierre, estado, dif, resumen_json
            row = self.hist_table.rowCount()
            self.hist_table.insertRow(row)
            
            # Formatear c_resumen para sacar ventas totales si existe
            ventas_total = 0
            if h[6]:
                try:
                    res = json.loads(h[6])
                    ventas_total = res.get('ventas_efectivo', 0) + res.get('ventas_tarjeta', 0)
                except: pass

            data = [
                (str(h[2]), Qt.AlignmentFlag.AlignLeft),
                (str(h[3]) if h[3] else "-", Qt.AlignmentFlag.AlignLeft),
                (f"$ {ventas_total:,.2f}", Qt.AlignmentFlag.AlignRight),
                (f"$ {h[5]:,.2f}", Qt.AlignmentFlag.AlignRight),
                (h[4].upper(), Qt.AlignmentFlag.AlignCenter)
            ]
            
            for col, (text, align) in enumerate(data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                if col == 4: # Estado
                    if h[4] == 'abierta': item.setForeground(QBrush(QColor("#10B981")))
                    else: item.setForeground(QBrush(QColor("#94A3B8")))
                self.hist_table.setItem(row, col, item)

    def open_caja_action(self):
        try:
            monto = float(self.monto_apertura.text())
            if self.db.open_caja(monto):
                QMessageBox.information(self, "Éxito", "Caja abierta correctamente.")
                self.update_caja_view()
                self.update_global_caja_status()
            else:
                QMessageBox.critical(self, "Error", "No se pudo abrir la caja.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un monto inicial válido.")

    def add_movement_action(self, tipo):
        caja = self.db.get_open_caja()
        if not caja: return
        
        dialog = CajaMovementDialog(tipo, self)
        if dialog.exec():
            monto, motivo = dialog.get_data()
            if self.db.add_caja_movement(caja[0], tipo, monto, motivo):
                self.update_caja_view()
                self.update_global_caja_status()

    def close_caja_action(self):
        caja = self.db.get_open_caja()
        if not caja: return
        
        totals = self.db.get_caja_totals(caja[0])
        dialog = CorteCajaDialog(caja, totals, self)
        if dialog.exec():
            # El diálogo ya maneja el guardado si se acepta
            self.update_caja_view()
            self.update_global_caja_status()

    def create_config(self):
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        title = ui.QLabel("Configuración del Sistema")
        title.setObjectName("Title")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self.create_supplier_config(), "Proveedores")
        tabs.addTab(self.create_card_config(), "Tarjetas de Crédito")
        tabs.addTab(self.create_category_config(), "Categorías")
        tabs.addTab(self.create_personnel_config(), "Personal")
        tabs.addTab(self.create_printer_config(), "Impresora de Etiquetas")
        tabs.addTab(self.create_database_config(), "Base de Datos")
        layout.addWidget(tabs)

        scroll.setWidget(page)
        return scroll

    def create_printer_config(self):
        from printing.printer_config import PrinterConfig
        self.printer_config = PrinterConfig()
        
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.combo_printers = QComboBox()
        try:
            from PyQt6.QtPrintSupport import QPrinterInfo
            for printer_info in QPrinterInfo.availablePrinters():
                self.combo_printers.addItem(printer_info.printerName())
        except Exception:
            pass
            
        index = self.combo_printers.findText(self.printer_config.printer_name)
        if index >= 0:
            self.combo_printers.setCurrentIndex(index)
            
        self.combo_connection = QComboBox()
        self.combo_connection.addItems(["windows", "serial", "bluetooth"])
        index = self.combo_connection.findText(self.printer_config.connection_type)
        if index >= 0:
            self.combo_connection.setCurrentIndex(index)
            
        self.input_com_port = ui.SearchField("COM1")
        self.input_com_port.setText(str(self.printer_config.com_port))
        
        self.input_baud_rate = ui.SearchField("9600")
        self.input_baud_rate.setText(str(self.printer_config.baud_rate))
            
        self.input_width = ui.SearchField("58")
        self.input_width.setText(str(self.printer_config.label_width_mm))
        
        self.input_height = ui.SearchField("30")
        self.input_height.setText(str(self.printer_config.label_height_mm))
        
        self.input_dpi = ui.SearchField("203")
        self.input_dpi.setText(str(self.printer_config.dpi))
        
        self.input_ml = ui.SearchField("2")
        self.input_ml.setText(str(self.printer_config.margin_left_mm))
        self.input_mr = ui.SearchField("2")
        self.input_mr.setText(str(self.printer_config.margin_right_mm))
        self.input_mt = ui.SearchField("2")
        self.input_mt.setText(str(self.printer_config.margin_top_mm))
        self.input_mb = ui.SearchField("2")
        self.input_mb.setText(str(self.printer_config.margin_bottom_mm))
        
        btn_save = ui.PrimaryButton("Guardar Configuración")
        btn_save.clicked.connect(self.save_printer_config)
        
        btn_test = ui.PrimaryButton("Imprimir etiqueta de prueba")
        btn_test.setObjectName("Secondary")
        btn_test.clicked.connect(self.print_test_label)
        
        layout.addRow("Impresora:", self.combo_printers)
        layout.addRow("Tipo de Conexión:", self.combo_connection)
        layout.addRow("Puerto COM (Serial/BT):", self.input_com_port)
        layout.addRow("Baud Rate:", self.input_baud_rate)
        layout.addRow("Ancho (mm):", self.input_width)
        layout.addRow("Alto (mm):", self.input_height)
        layout.addRow("DPI:", self.input_dpi)
        layout.addRow("Margen Izq (mm):", self.input_ml)
        layout.addRow("Margen Der (mm):", self.input_mr)
        layout.addRow("Margen Sup (mm):", self.input_mt)
        layout.addRow("Margen Inf (mm):", self.input_mb)
        layout.addRow("", btn_save)
        layout.addRow("", btn_test)
        
        return widget
        
    def save_printer_config(self):
        try:
            self.printer_config.printer_name = self.combo_printers.currentText()
            self.printer_config.connection_type = self.combo_connection.currentText()
            self.printer_config.label_width_mm = float(self.input_width.text())
            self.printer_config.label_height_mm = float(self.input_height.text())
            self.printer_config.dpi = int(self.input_dpi.text())
            self.printer_config.margin_left_mm = float(self.input_ml.text())
            self.printer_config.margin_right_mm = float(self.input_mr.text())
            self.printer_config.margin_top_mm = float(self.input_mt.text())
            self.printer_config.margin_bottom_mm = float(self.input_mb.text())
            self.printer_config.com_port = self.input_com_port.text().strip()
            self.printer_config.baud_rate = int(self.input_baud_rate.text())
            self.printer_config.save()
            QMessageBox.information(self, "Éxito", "Configuración de impresora guardada correctamente.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Valores numéricos inválidos.")

    def print_test_label(self):
        try:
            from printing.thermal_printer import ThermalLabelPrinter
            printer = ThermalLabelPrinter()
            printer.print_test_label()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al imprimir: {e}")

    def create_database_config(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl_info = ui.QLabel("Usa estas herramientas para respaldar tu información o para mover tu base de datos a otra computadora.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #94A3B8; font-size: 11pt;")
        layout.addWidget(lbl_info)

        btn_export = ui.PrimaryButton("⬇️ Exportar Base de Datos (Descargar)")
        btn_export.setFixedHeight(45)
        btn_export.clicked.connect(self.export_database_action)
        
        btn_import = ui.AlertButton("⬆️ Importar Base de Datos (Subir)")
        btn_import.setFixedHeight(45)
        btn_import.clicked.connect(self.import_database_action)

        layout.addWidget(btn_export)
        layout.addWidget(btn_import)
        layout.addStretch()

        return widget

    def export_database_action(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Base de Datos", "Respaldo_ProVision.db", "Database Files (*.db);;All Files (*)"
        )
        if file_path:
            try:
                shutil.copy(self.db.db_path, file_path)
                QMessageBox.information(self, "Éxito", f"Base de datos exportada correctamente a:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error al exportar:\n{e}")

    def import_database_action(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Base de Datos", "", "Database Files (*.db);;All Files (*)"
        )
        if file_path:
            reply = QMessageBox.warning(
                self, "Advertencia Crítica", 
                "⚠️ Al importar una base de datos, TODOS tus datos actuales serán sobreescritos.\n\n"
                "Para que los cambios se apliquen correctamente de forma segura, la aplicación se cerrará después de importar.\n\n"
                "¿Estás completamente seguro de que deseas continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    shutil.copy(file_path, self.db.db_path)
                    QMessageBox.information(self, "Importación Exitosa", "Base de datos importada correctamente.\nLa aplicación se cerrará ahora. Por favor, ábrela de nuevo para ver los cambios.")
                    sys.exit(0)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Ocurrió un error al importar:\n{e}")

    def create_supplier_config(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top = QHBoxLayout()
        self.supplier_input = ui.QLineEdit()
        self.supplier_input.setPlaceholderText("Nombre del nuevo proveedor...")
        btn_add = ui.PrimaryButton("Añadir")
        btn_add.clicked.connect(self.add_supplier)
        top.addWidget(self.supplier_input)
        top.addWidget(btn_add)
        layout.addLayout(top)

        self.supplier_table = QTableWidget(0, 2)
        self.supplier_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.supplier_table.verticalHeader().setDefaultSectionSize(35)
        self.supplier_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.supplier_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.supplier_table)

        btn_del = ui.AlertButton("Eliminar Seleccionado")
        btn_del.clicked.connect(self.delete_supplier)
        layout.addWidget(btn_del)

        self.load_suppliers_table()
        return widget

    def create_card_config(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top = QHBoxLayout()
        self.card_input = ui.QLineEdit()
        self.card_input.setPlaceholderText("Nombre de la tarjeta (ej. Visa - 1234)...")
        btn_add = ui.PrimaryButton("Añadir")
        btn_add.clicked.connect(self.add_card)
        top.addWidget(self.card_input)
        top.addWidget(btn_add)
        layout.addLayout(top)

        self.card_table = QTableWidget(0, 2)
        self.card_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.card_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.card_table.verticalHeader().setDefaultSectionSize(35)
        self.card_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.card_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.card_table)

        btn_del = ui.AlertButton("Eliminar Seleccionada")
        btn_del.clicked.connect(self.delete_card)
        layout.addWidget(btn_del)

        self.load_cards_table()
        return widget

    def load_suppliers_table(self):
        suppliers = self.db.get_all_suppliers()
        self.supplier_table.setRowCount(0)
        for s_id, name in suppliers:
            row = self.supplier_table.rowCount()
            self.supplier_table.insertRow(row)
            
            item_id = QTableWidgetItem(str(s_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.supplier_table.setItem(row, 0, item_id)
            
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.supplier_table.setItem(row, 1, item_name)

    def load_cards_table(self):
        cards = self.db.get_all_credit_cards()
        self.card_table.setRowCount(0)
        for c_id, name in cards:
            row = self.card_table.rowCount()
            self.card_table.insertRow(row)
            
            item_id = QTableWidgetItem(str(c_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.card_table.setItem(row, 0, item_id)
            
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.card_table.setItem(row, 1, item_name)

    def add_supplier(self):
        name = self.supplier_input.text()
        if name and self.db.add_supplier(name):
            self.supplier_input.clear()
            self.load_suppliers_table()
            self.refresh_purchase_selectors()
        else:
            QMessageBox.warning(self, "Error", "No se pudo añadir el proveedor.")

    def delete_supplier(self):
        row = self.supplier_table.currentRow()
        if row >= 0:
            s_id = int(self.supplier_table.item(row, 0).text())
            if self.db.delete_supplier(s_id):
                self.load_suppliers_table()
                self.refresh_purchase_selectors()

    def add_card(self):
        name = self.card_input.text()
        if name and self.db.add_credit_card(name):
            self.card_input.clear()
            self.load_cards_table()
            self.refresh_purchase_selectors()
        else:
            QMessageBox.warning(self, "Error", "No se pudo añadir la tarjeta.")

    def delete_card(self):
        row = self.card_table.currentRow()
        if row >= 0:
            c_id = int(self.card_table.item(row, 0).text())
            if self.db.delete_credit_card(c_id):
                self.load_cards_table()
                self.refresh_purchase_selectors()

    def refresh_purchase_selectors(self):
        """Actualiza los combo boxes en la sección de compras y configuración."""
        self.compra_supplier.clear()
        self.combo_supplier.clear()
        suppliers = self.db.get_all_suppliers()
        for s_id, name in suppliers:
            self.compra_supplier.addItem(name, s_id)
            self.combo_supplier.addItem(name, s_id)

        self.card_selector.clear()
        cards = self.db.get_all_credit_cards()
        for c_id, name in cards:
            self.card_selector.addItem(name, c_id)

        self.compra_responsible.clear()
        self.combo_responsible.clear()
        personnel = self.db.get_all_personnel()
        for p_id, name in personnel:
            self.compra_responsible.addItem(name, p_id)
            self.combo_responsible.addItem(name, p_id)

    def create_category_config(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top = QHBoxLayout()
        self.category_input = ui.QLineEdit()
        self.category_input.setPlaceholderText("Nombre de la nueva categoría...")
        btn_add = ui.PrimaryButton("Añadir")
        btn_add.clicked.connect(self.add_category)
        top.addWidget(self.category_input)
        top.addWidget(btn_add)
        layout.addLayout(top)

        self.category_table = QTableWidget(0, 2)
        self.category_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.category_table.verticalHeader().setDefaultSectionSize(35)
        self.category_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.category_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.category_table)

        btn_del = ui.AlertButton("Eliminar Seleccionada")
        btn_del.clicked.connect(self.delete_category)
        layout.addWidget(btn_del)

        self.load_categories_table()
        return widget

    def load_categories_table(self):
        categories = self.db.get_all_categories()
        self.category_table.setRowCount(0)
        for c_id, name in categories:
            row = self.category_table.rowCount()
            self.category_table.insertRow(row)
            
            item_id = QTableWidgetItem(str(c_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.category_table.setItem(row, 0, item_id)
            
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.category_table.setItem(row, 1, item_name)

    def add_category(self):
        name = self.category_input.text()
        if name and self.db.add_category(name):
            self.category_input.clear()
            self.load_categories_table()
        else:
            QMessageBox.warning(self, "Error", "No se pudo añadir la categoría.")

    def delete_category(self):
        row = self.category_table.currentRow()
        if row >= 0:
            c_id = int(self.category_table.item(row, 0).text())
            if self.db.delete_category(c_id):
                self.load_categories_table()

    def create_personnel_config(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top = QHBoxLayout()
        self.personnel_input = ui.QLineEdit()
        self.personnel_input.setPlaceholderText("Nombre del nuevo personal...")
        btn_add = ui.PrimaryButton("Añadir")
        btn_add.clicked.connect(self.add_personnel)
        top.addWidget(self.personnel_input)
        top.addWidget(btn_add)
        layout.addLayout(top)

        self.personnel_table = QTableWidget(0, 2)
        self.personnel_table.setHorizontalHeaderLabels(["ID", "Nombre"])
        header = self.personnel_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.personnel_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.personnel_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.personnel_table)

        btn_del = ui.AlertButton("Eliminar Seleccionado")
        btn_del.clicked.connect(self.delete_personnel)
        layout.addWidget(btn_del)

        self.load_personnel_table()
        return widget

    def load_personnel_table(self):
        personnel = self.db.get_all_personnel()
        self.personnel_table.setRowCount(0)
        for p_id, name in personnel:
            row = self.personnel_table.rowCount()
            self.personnel_table.insertRow(row)
            
            item_id = QTableWidgetItem(str(p_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.personnel_table.setItem(row, 0, item_id)
            
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.personnel_table.setItem(row, 1, item_name)

    def add_personnel(self):
        name = self.personnel_input.text()
        if name and self.db.add_personnel(name):
            self.personnel_input.clear()
            self.load_personnel_table()
            self.refresh_purchase_selectors()
        else:
            QMessageBox.warning(self, "Error", "No se pudo añadir al personal.")

    def delete_personnel(self):
        row = self.personnel_table.currentRow()
        if row >= 0:
            p_id = int(self.personnel_table.item(row, 0).text())
            if self.db.delete_personnel(p_id):
                self.load_personnel_table()
                self.refresh_purchase_selectors()

    def open_pending_orders(self):
        dialog = PendingOrdersDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_inventory_data()
            self.update_dashboard_data()


    def load_pos_customers(self):
        customers = self.db.get_all_customers()
        self.pos_customer.clear()
        self.pos_customer.addItem("Consumidor Final", None)
        for c in customers:
            self.pos_customer.addItem(c[1], c[0])

    def pos_add_customer(self):
        dialog = NewCustomerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_pos_customers()
            idx = self.pos_customer.count() - 1
            self.pos_customer.setCurrentIndex(idx)
            self.load_customers_table()

    def create_customers(self):
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        title = ui.QLabel("Gestión de Clientes")
        title.setObjectName("Title")

        top_layout = QHBoxLayout()
        top_layout.addWidget(title)
        top_layout.addStretch()

        btn_add = ui.PrimaryButton("+ Nuevo Cliente")
        btn_add.clicked.connect(self.pos_add_customer)
        top_layout.addWidget(btn_add)
        
        layout.addLayout(top_layout)

        # Tablero Dividido
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Izquierda: Tabla
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.customers_table = QTableWidget(0, 6)
        self.customers_table.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Visitas", "$ Gastado", "$ Promociones"])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.customers_table.verticalHeader().setDefaultSectionSize(40)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customers_table.itemDoubleClicked.connect(self.show_customer_profile)
        left_layout.addWidget(self.customers_table)
        
        # Derecha: Analytics
        right_widget = ui.Card()
        right_layout = QVBoxLayout(right_widget)
        
        lbl_top_s = ui.QLabel("🏆 Top Clientes (Ingresos)")
        lbl_top_s.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11pt;")
        self.top_spent_list = QListWidget()
        self.top_spent_list.setStyleSheet("background: transparent; color: #F8FAFC; font-size: 10pt; border: none;")
        
        lbl_top_f = ui.QLabel("🔥 Top Clientes Frecuentes")
        lbl_top_f.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 11pt;")
        self.top_freq_list = QListWidget()
        self.top_freq_list.setStyleSheet("background: transparent; color: #F8FAFC; font-size: 10pt; border: none;")

        lbl_top_p = ui.QLabel("🎁 Top Recompensados")
        lbl_top_p.setStyleSheet("color: #0EA5E9; font-weight: bold; font-size: 11pt;")
        self.top_promo_list = QListWidget()
        self.top_promo_list.setStyleSheet("background: transparent; color: #F8FAFC; font-size: 10pt; border: none;")

        right_layout.addWidget(lbl_top_s)
        right_layout.addWidget(self.top_spent_list)
        right_layout.addWidget(lbl_top_f)
        right_layout.addWidget(self.top_freq_list)
        right_layout.addWidget(lbl_top_p)
        right_layout.addWidget(self.top_promo_list)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 300])

        layout.addWidget(splitter)
        scroll.setWidget(page)
        return scroll

    def load_customers_table(self):
        customers = self.db.get_all_customers()
        self.customers_table.setRowCount(0)
        for c_id, name, phone, email, visits, spent, discounts in customers:
            row = self.customers_table.rowCount()
            self.customers_table.insertRow(row)
            
            items = [
                str(c_id),
                name,
                phone if phone else "N/A",
                str(visits),
                f"$ {spent:,.2f}",
                f"$ {discounts:,.2f}"
            ]
            
            for col, text in enumerate(items):
                it = QTableWidgetItem(text)
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                # Almacenar ID maestro en el Nombre
                if col == 1:
                    it.setData(Qt.ItemDataRole.UserRole, c_id)
                self.customers_table.setItem(row, col, it)
                
        # Load Analytics
        self.top_spent_list.clear()
        for idx, (name, total) in enumerate(self.db.get_top_customers_by_spent(5), 1):
            self.top_spent_list.addItem(f"{idx}. {name} - $ {total:,.2f}")
            
        self.top_freq_list.clear()
        for idx, (name, freq) in enumerate(self.db.get_top_customers_by_frequency(5), 1):
            self.top_freq_list.addItem(f"{idx}. {name} - {freq} visitas")
            
        self.top_promo_list.clear()
        for idx, (name, desc) in enumerate(self.db.get_top_customers_by_promotions(5), 1):
            self.top_promo_list.addItem(f"{idx}. {name} - $ {desc:,.2f}")

    def show_customer_profile(self, item):
        row = item.row()
        name_item = self.customers_table.item(row, 1)
        c_id = name_item.data(Qt.ItemDataRole.UserRole)
        name = name_item.text()
        
        # Simple popup visualizando historial
        history = self.db.get_customer_history(c_id)
        msg_text = f"Historial de: {name}\n\n"
        if not history:
            msg_text += "No hay compras registradas.\n"
        else:
            for d, t_num, t_amount, d_app in history:
                msg_text += f"{d} | {t_num} | Total: ${t_amount:,.2f} | Descuento: ${d_app:,.2f}\n"
                
        from PyQt6.QtWidgets import QMessageBox
        box = QMessageBox(self)
        box.setWindowTitle("Perfil del Cliente")
        box.setText(msg_text)
        box.exec()

class NewCustomerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.db = parent.db
        self.setWindowTitle("Nuevo Cliente")
        self.setFixedWidth(400)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = ui.QLineEdit()
        self.inp_phone = ui.QLineEdit()
        self.inp_email = ui.QLineEdit()
        
        form.addRow("Nombre:", self.inp_name)
        form.addRow("Teléfono:", self.inp_phone)
        form.addRow("Email:", self.inp_email)
        
        layout.addLayout(form)
        
        btn_save = ui.PrimaryButton("Registrar Cliente")
        btn_save.clicked.connect(self.save_customer)
        layout.addWidget(btn_save)
        
    def save_customer(self):
        name = self.inp_name.text().strip()
        if not name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "El nombre es requerido.")
            return
            
        phone = self.inp_phone.text()
        email = self.inp_email.text()
        
        if self.db.add_customer(name, phone, email):
            self.accept()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", "Error al registrar cliente.")

class CajaMovementDialog(QDialog):
    def __init__(self, tipo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Registrar {tipo.capitalize()}")
        self.setFixedWidth(300)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.monto = ui.QLineEdit()
        self.monto.setPlaceholderText("0.00")
        self.motivo = ui.QLineEdit()
        self.motivo.setPlaceholderText("Ej: Pago de flete")
        
        form.addRow("Monto:", self.monto)
        form.addRow("Motivo:", self.motivo)
        
        layout.addLayout(form)
        
        btn_save = ui.PrimaryButton("Guardar")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

    def get_data(self):
        try:
            return float(self.monto.text()), self.motivo.text()
        except ValueError:
            return 0.0, ""

class CorteCajaDialog(QDialog):
    def __init__(self, caja, totals, parent=None):
        super().__init__(parent)
        self.caja = caja
        self.totals = totals
        self.db = parent.db
        self.setWindowTitle("Corte de Caja")
        self.setFixedWidth(400)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        
        # Resumen Automático
        c_id, m_inicial, _, _, _, _, _ = caja
        sales = totals['sales']
        movs = totals['movements']
        
        efectivo = sales.get('Cash', 0)
        tarjeta = sales.get('Card', 0)
        ingresos = movs.get('ingreso', 0)
        retiros = movs.get('retiro', 0)
        self.esperado = m_inicial + efectivo + ingresos - retiros
        
        res_card = ui.Card()
        res_layout = QVBoxLayout(res_card)
        res_layout.addWidget(ui.QLabel(f"Efectivo Inicial: $ {m_inicial:,.2f}"))
        res_layout.addWidget(ui.QLabel(f"Ventas Efectivo: + $ {efectivo:,.2f}"))
        res_layout.addWidget(ui.QLabel(f"Ingresos Extra: + $ {ingresos:,.2f}"))
        res_layout.addWidget(ui.QLabel(f"Retiros: - $ {retiros:,.2f}"))
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        res_layout.addWidget(line)
        
        lbl_esp = ui.QLabel(f"TOTAL ESPERADO: $ {self.esperado:,.2f}")
        lbl_esp.setStyleSheet("font-weight: bold; font-size: 14pt; color: #0EA5E9;")
        res_layout.addWidget(lbl_esp)
        
        layout.addWidget(res_card)
        
        # Conteo Real
        cnt_lbl = ui.QLabel("Efectivo Contado (Real):")
        cnt_lbl.setObjectName("Secondary")
        self.contado = ui.QLineEdit()
        self.contado.setStyleSheet("font-size: 18pt; padding: 10px;")
        self.contado.setPlaceholderText("Ingrese monto...")
        
        self.lbl_dif = ui.QLabel("Diferencia: $ 0.00")
        self.lbl_dif.setStyleSheet("font-size: 12pt; font-weight: bold;")
        
        self.contado.textChanged.connect(self.update_diff)
        
        layout.addWidget(cnt_lbl)
        layout.addWidget(self.contado)
        layout.addWidget(self.lbl_dif)
        
        btn_close = ui.PrimaryButton("CERRAR CAJA Y GUARDAR")
        btn_close.setStyleSheet("background-color: #10B981; min-height: 50px;")
        btn_close.clicked.connect(self.save_close)
        layout.addWidget(btn_close)

    def update_diff(self):
        try:
            real = float(self.contado.text()) if self.contado.text() else 0.0
            dif = real - self.esperado
            self.lbl_dif.setText(f"Diferencia: $ {dif:,.2f}")
            if abs(dif) < 0.01:
                self.lbl_dif.setStyleSheet("font-size: 12pt; color: #10B981; font-weight: bold;")
            elif dif > 0:
                self.lbl_dif.setStyleSheet("font-size: 12pt; color: #F59E0B; font-weight: bold;")
            else:
                self.lbl_dif.setStyleSheet("font-size: 12pt; color: #EF4444; font-weight: bold;")
        except ValueError:
            self.lbl_dif.setText("Diferencia: Error")

    def save_close(self):
        try:
            real = float(self.contado.text())
            dif = real - self.esperado
            
            resumen = {
                'monto_inicial': self.caja[1],
                'ventas_efectivo': self.totals['sales'].get('Cash', 0),
                'ventas_tarjeta': self.totals['sales'].get('Card', 0),
                'ingresos': self.totals['movements'].get('ingreso', 0),
                'retiros': self.totals['movements'].get('retiro', 0),
                'total_esperado': self.esperado,
                'total_real': real
            }
            
            if self.db.close_caja(self.caja[0], dif, json.dumps(resumen)):
                QMessageBox.information(self, "Cierre Exitoso", f"Caja cerrada. Diferencia: $ {dif:,.2f}")
                self.accept()
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un monto contado válido.")

class PaymentDialog(QDialog):
    def __init__(self, total, parent=None):
        super().__init__(parent)
        self.total = total
        self.setWindowTitle("Procesar Pago")
        self.setFixedWidth(400)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        
        lbl_total = ui.QLabel(f"TOTAL A COBRAR: $ {total:,.2f}")
        lbl_total.setStyleSheet("font-size: 20pt; font-weight: bold; color: #0EA5E9; margin-bottom: 20px;")
        lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_total)
        
        self.method = QComboBox()
        self.method.addItems(["Efectivo", "Tarjeta", "Transferencia"])
        self.method.setMinimumHeight(45)
        layout.addWidget(ui.QLabel("Método de Pago:"))
        layout.addWidget(self.method)
        
        self.received = ui.QLineEdit()
        self.received.setPlaceholderText("Monto recibido (en efectivo)...")
        self.received.setMinimumHeight(45)
        self.received.setStyleSheet("font-size: 14pt;")
        layout.addWidget(ui.QLabel("Recibido:"))
        layout.addWidget(self.received)
        
        self.lbl_change = ui.QLabel("Cambio: $ 0.00")
        self.lbl_change.setStyleSheet("font-size: 16pt; font-weight: bold; color: #10B981;")
        layout.addWidget(self.lbl_change)
        
        self.received.textChanged.connect(self.update_change)
        
        btn_confirm = ui.PrimaryButton("CONFIRMAR VENTA")
        btn_confirm.setMinimumHeight(60)
        btn_confirm.clicked.connect(self.accept)
        layout.addWidget(btn_confirm)

    def update_change(self):
        try:
            rec = float(self.received.text()) if self.received.text() else 0.0
            change = rec - self.total
            self.lbl_change.setText(f"Cambio: $ {max(0, change):,.2f}")
        except ValueError:
            self.lbl_change.setText("Cambio: Error")

    def get_data(self):
        method = self.method.currentText()
        if method == "Efectivo": return "Cash"
        if method == "Tarjeta": return "Card"
        return "Transfer"

class CustomPrintPreviewDialog(QDialog):
    def __init__(self, name, sku, price, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vista Previa de Impresión")
        self.setFixedSize(450, 500)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        self.name = name
        self.sku = sku
        self.price = price
        
        layout = QVBoxLayout(self)
        
        lbl_title = ui.QLabel("Vista Previa de Etiqueta")
        lbl_title.setObjectName("Title")
        layout.addWidget(lbl_title)
        
        from printing.thermal_printer import ThermalLabelPrinter
        try:
            self.printer = ThermalLabelPrinter()
            img = self.printer.renderer.render_product_label(self.name, self.sku, self.price)
            
            import io
            from PyQt6.QtGui import QPixmap, QImage
            from PyQt6.QtCore import Qt
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            qimg = QImage.fromData(buf.getvalue())
            pixmap = QPixmap.fromImage(qimg)
            
            lbl_preview = ui.QLabel()
            lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_preview.setPixmap(pixmap)
            # Fondo blanco para simular la etiqueta
            lbl_preview.setStyleSheet("background-color: white; border: 1px solid #334155; padding: 20px;")
            
            layout.addWidget(lbl_preview)
            
        except Exception as e:
            layout.addWidget(ui.QLabel(f"Error al generar vista previa: {e}"))
            
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_print = ui.PrimaryButton("Imprimir")
        btn_print.clicked.connect(self.do_print)
        btn_cancel = ui.AlertButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_print)
        
        layout.addLayout(btn_layout)
        
    def do_print(self):
        try:
            self.printer.print_product_label(self.name, self.sku, self.price)
            QMessageBox.information(self, "Éxito", "Etiqueta enviada a impresión.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al imprimir: {e}")


class NewProductDialog(QDialog):
    def __init__(self, parent=None, pre_sku="", pre_cost="", pre_price=""):
        super().__init__(parent)
        self.setWindowTitle("Añadir Nuevo Producto")
        self.setFixedWidth(400)
        self.setStyleSheet(ui.STYLE_SHEET)
        self.db = parent.db
        self.pre_sku = pre_sku
        self.pre_cost = str(pre_cost) if pre_cost else ""
        self.pre_price = str(pre_price) if pre_price else ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # 1. Creación de Widgets
        self.sku = ui.QLineEdit()
        self.name = ui.QLineEdit()
        self.category = QComboBox()
        self.cost = ui.QLineEdit()
        self.tax_pct = ui.QLineEdit()
        self.profit_pct = ui.QLineEdit()
        self.price = ui.QLineEdit()
        self.min_stock = ui.QLineEdit()
        self.current_stock = ui.QLineEdit()
        self.img_path_label = ui.QLabel("Sin imagen")
        self.lbl_suggested_price = ui.QLabel("Sug: $ 0.00")
        self.btn_apply_suggested = ui.TableActionButton("Aplicar")
        self.btn_img = ui.PrimaryButton("Subir Imagen")

        # 2. Configuración y Conexiones
        self.load_categories()
        self.sku.returnPressed.connect(lambda: self.name.setFocus())
        self.btn_img.clicked.connect(self.select_image)
        self.btn_apply_suggested.clicked.connect(self.apply_suggested_price)
        
        # Conectar señales de cálculo
        self.cost.textChanged.connect(self.update_suggested_price)
        self.tax_pct.textChanged.connect(self.update_suggested_price)
        self.profit_pct.textChanged.connect(self.update_suggested_price)

        # 3. Valores Iniciales (pueden disparar señales)
        self.tax_pct.setPlaceholderText("0")
        self.profit_pct.setPlaceholderText("0")
        self.tax_pct.setText("0")
        self.profit_pct.setText("0")
        self.min_stock.setText("5")
        self.current_stock.setText("0")
        
        if self.pre_sku: self.sku.setText(self.pre_sku)
        if self.pre_cost: self.cost.setText(self.pre_cost)
        if self.pre_price: self.price.setText(self.pre_price)
        
        self.selected_image_path = None
        self.img_path_label.setObjectName("Secondary")
        
        # Foco inteligente
        if self.pre_sku:
            self.name.setFocus()
        else:
            self.sku.setFocus()
        
        self.img_path_label = ui.QLabel("Sin imagen")
        self.img_path_label.setObjectName("Secondary")
        self.btn_img = ui.PrimaryButton("Subir Imagen")
        self.btn_img.clicked.connect(self.select_image)
        self.selected_image_path = None
        
        self.btn_gen_sku = ui.TableActionButton("Generar")
        self.btn_gen_sku.clicked.connect(self.generate_sku)
        self.btn_print_sku = ui.TableActionButton("Imprimir")
        self.btn_print_sku.clicked.connect(self.print_barcode)
        
        sku_layout = QHBoxLayout()
        sku_layout.addWidget(self.sku)
        sku_layout.addWidget(self.btn_gen_sku)
        sku_layout.addWidget(self.btn_print_sku)
        
        form.addRow("SKU:", sku_layout)
        form.addRow("Nombre:", self.name)
        form.addRow("Categoría:", self.category)
        form.addRow("Precio Costo ($):", self.cost)
        form.addRow("Impuesto (%):", self.tax_pct)
        form.addRow("Ganancia (%):", self.profit_pct)

        # Precio Sugerido y Botón Aplicar
        suggested_layout = QHBoxLayout()
        suggested_layout.addWidget(self.lbl_suggested_price)
        suggested_layout.addWidget(self.btn_apply_suggested)
        suggested_layout.addStretch()

        form.addRow("Precio Sugerido:", suggested_layout)
        form.addRow("Precio Venta ($):", self.price)
        form.addRow("Stock Mínimo:", self.min_stock)
        form.addRow("Stock Inicial:", self.current_stock)
        form.addRow("Imagen:", self.btn_img)
        form.addRow("", self.img_path_label)
        
        layout.addLayout(form)        
        btn_save = ui.PrimaryButton("Guardar Producto")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def generate_sku(self):
        new_sku = str(random.randint(100000000000, 999999999999))
        self.sku.setText(new_sku)

    def print_barcode(self):
        sku_text = self.sku.text().strip()
        name_text = self.name.text().strip()
        if not name_text:
            name_text = "Producto Nuevo"
            
        if not sku_text:
            QMessageBox.warning(self, "Error", "Debe ingresar o generar un SKU primero.")
            return
            
        price_val = 0.0
        try:
            price_val = float(self.price.text())
        except ValueError:
            pass
            
        dialog = CustomPrintPreviewDialog(name_text, sku_text, price_val, self)
        dialog.exec()

    def update_suggested_price(self):
        try:
            cost = float(self.cost.text()) if self.cost.text() else 0.0
            tax = float(self.tax_pct.text()) if self.tax_pct.text() else 0.0
            profit = float(self.profit_pct.text()) if self.profit_pct.text() else 0.0
            suggested = cost * (1 + (tax + profit) / 100.0)
            self.lbl_suggested_price.setText(f"Sug: $ {suggested:,.2f}")
        except ValueError:
            self.lbl_suggested_price.setText("Sug: Error")

    def apply_suggested_price(self):
        try:
            cost = float(self.cost.text()) if self.cost.text() else 0.0
            tax = float(self.tax_pct.text()) if self.tax_pct.text() else 0.0
            profit = float(self.profit_pct.text()) if self.profit_pct.text() else 0.0
            suggested = cost * (1 + (tax + profit) / 100.0)
            self.price.setText(f"{suggested:.2f}")
        except ValueError:
            pass

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.selected_image_path = file_path
            self.img_path_label.setText(os.path.basename(file_path))

    def save(self):
        try:
            sku = self.sku.text()
            name = self.name.text()
            category = self.category.currentText()
            cost = float(self.cost.text())
            price = float(self.price.text())
            tax_pct = float(self.tax_pct.text()) if self.tax_pct.text() else 0.0
            min_st = int(self.min_stock.text())
            stock = int(self.current_stock.text())
            
            # Procesar imagen si existe
            final_img_path = None
            if self.selected_image_path:
                try:
                    logic = BusinessLogic()
                    final_img_path = logic.resize_product_image(self.selected_image_path)
                except Exception as img_err:
                    QMessageBox.warning(self, "Error de Imagen", f"No se pudo procesar la imagen: {img_err}")

            if self.db.add_product(sku, name, category, cost, price, min_st, stock, 
                                 image_path=final_img_path, tax_percentage=tax_pct):
                QMessageBox.information(self, "Éxito", "Producto guardado correctamente.")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "No se pudo guardar el producto (SKU duplicado?).")
        except ValueError:
            QMessageBox.critical(self, "Error", "Por favor ingrese valores numéricos válidos en costo y stock.")

    def load_categories(self):
        categories = self.db.get_all_categories()
        self.category.clear()
        for _, name in categories:
            self.category.addItem(name)

class EditProductDialog(QDialog):
    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.parent = parent
        self.db = parent.db
        self.image_path = None
        self.setWindowTitle("Editar Producto")
        self.setFixedWidth(400)
        self.setStyleSheet(ui.STYLE_SHEET)
        self.init_ui()
        self.load_product_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.sku = ui.QLineEdit()
        self.name = ui.QLineEdit()
        self.category = QComboBox()
        self.cost = ui.QLineEdit()
        self.tax_pct = ui.QLineEdit()
        self.tax_pct.setPlaceholderText("0")
        self.profit_pct = ui.QLineEdit()
        self.profit_pct.setPlaceholderText("0")
        self.price = ui.QLineEdit()
        self.min_stock = ui.QLineEdit()
        self.stock = ui.QLineEdit()
        self.lbl_suggested_price = ui.QLabel("Sug: $ 0.00")
        self.lbl_suggested_price.setStyleSheet("color: #0EA5E9; font-weight: bold;")
        self.btn_apply_suggested = ui.TableActionButton("Aplicar")
        self.btn_img = ui.PrimaryButton("Cambiar Imagen")

        # 2. Configuración y Conexiones
        self.load_categories()
        self.sku.returnPressed.connect(lambda: self.name.setFocus())
        self.btn_img.clicked.connect(self.select_image)
        self.btn_img.setObjectName("Secondary")
        self.btn_apply_suggested.clicked.connect(self.apply_suggested_price)
        
        # Conectar señales
        self.cost.textChanged.connect(self.update_suggested_price)
        self.tax_pct.textChanged.connect(self.update_suggested_price)
        self.profit_pct.textChanged.connect(self.update_suggested_price)

        # 3. Valores iniciales
        self.tax_pct.setText("0")
        self.profit_pct.setText("0")
        
        self.btn_gen_sku = ui.TableActionButton("Generar")
        self.btn_gen_sku.clicked.connect(self.generate_sku)
        self.btn_print_sku = ui.TableActionButton("Imprimir")
        self.btn_print_sku.clicked.connect(self.print_barcode)
        
        sku_layout = QHBoxLayout()
        sku_layout.addWidget(self.sku)
        sku_layout.addWidget(self.btn_gen_sku)
        sku_layout.addWidget(self.btn_print_sku)
        
        form.addRow("Imagen:", self.btn_img)
        form.addRow("SKU:", sku_layout)
        form.addRow("Nombre:", self.name)
        form.addRow("Categoría:", self.category)
        form.addRow("Costo ($):", self.cost)
        form.addRow("Impuesto (%):", self.tax_pct)
        form.addRow("Ganancia (%):", self.profit_pct)

        # Precio Sugerido y Botón Aplicar
        suggested_layout = QHBoxLayout()
        suggested_layout.addWidget(self.lbl_suggested_price)
        suggested_layout.addWidget(self.btn_apply_suggested)
        suggested_layout.addStretch()

        form.addRow("Precio Sugerido:", suggested_layout)
        form.addRow("Venta ($):", self.price)
        form.addRow("Stock Mín.:", self.min_stock)
        form.addRow("Stock Act.:", self.stock)

        layout.addLayout(form)

        btn_save = ui.PrimaryButton("Guardar Cambios")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def generate_sku(self):
        new_sku = str(random.randint(100000000000, 999999999999))
        self.sku.setText(new_sku)

    def print_barcode(self):
        sku_text = self.sku.text().strip()
        name_text = self.name.text().strip()
        if not name_text:
            name_text = "Producto Editado"
            
        if not sku_text:
            QMessageBox.warning(self, "Error", "Debe ingresar o generar un SKU primero.")
            return
            
        price_val = 0.0
        try:
            price_val = float(self.price.text())
        except ValueError:
            pass
            
        dialog = CustomPrintPreviewDialog(name_text, sku_text, price_val, self)
        dialog.exec()

    def update_suggested_price(self):
        try:
            cost = float(self.cost.text()) if self.cost.text() else 0.0
            tax = float(self.tax_pct.text()) if self.tax_pct.text() else 0.0
            profit = float(self.profit_pct.text()) if self.profit_pct.text() else 0.0
            suggested = cost * (1 + (tax + profit) / 100.0)
            self.lbl_suggested_price.setText(f"Sug: $ {suggested:,.2f}")
        except ValueError:
            self.lbl_suggested_price.setText("Sug: Error")

    def apply_suggested_price(self):
        try:
            cost = float(self.cost.text()) if self.cost.text() else 0.0
            tax = float(self.tax_pct.text()) if self.tax_pct.text() else 0.0
            profit = float(self.profit_pct.text()) if self.profit_pct.text() else 0.0
            suggested = cost * (1 + (tax + profit) / 100.0)
            self.price.setText(f"{suggested:.2f}")
        except ValueError:
            pass

    def load_categories(self):
        categories = self.db.get_all_categories()
        self.category.clear()
        for _, name in categories:
            self.category.addItem(name)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            self.image_path = file_path

    def load_product_data(self):
        # Necesitamos un método para obtener todos los campos de un producto por ID
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sku, name, category, cost_price, selling_price, min_stock, current_stock, image_path, tax_percentage FROM products WHERE id = ?", (self.product_id,))
                data = cursor.fetchone()
                if data:
                    self.sku.setText(data[0])
                    self.name.setText(data[1])
                    self.category.setCurrentText(data[2])
                    self.cost.setText(str(data[3]))
                    self.price.setText(str(data[4]))
                    self.min_stock.setText(str(data[5]))
                    self.stock.setText(str(data[6]))
                    self.image_path = data[7]
                    self.tax_pct.setText(str(data[8]))
        except sqlite3.Error as e:
            print(f"Error al cargar producto: {e}")

    def save(self):
        try:
            sku = self.sku.text()
            name = self.name.text()
            category = self.category.currentText()
            cost = float(self.cost.text())
            price = float(self.price.text())
            tax_pct = float(self.tax_pct.text()) if self.tax_pct.text() else 0.0
            min_st = int(self.min_stock.text())
            stock = int(self.stock.text())

            if self.db.update_product(self.product_id, sku, name, category, cost, price, min_st, stock, self.image_path, tax_percentage=tax_pct):
                QMessageBox.information(self, "Éxito", "Producto actualizado correctamente.")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el producto.")
        except ValueError:
            QMessageBox.critical(self, "Error", "Por favor ingrese valores numéricos válidos.")





class InvestmentDetailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = parent.db
        self.setWindowTitle("Desglose de Inversión")
        self.resize(600, 400)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        title = ui.QLabel("Inversión Detallada por Producto")
        title.setObjectName("Secondary")
        layout.addWidget(title)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["SKU", "Producto", "Stock", "Costo", "Total Inv."])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(35)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        products = self.db.get_all_products()
        self.table.setRowCount(0)
        total_inv = 0
        for p in products:
            # p = (id, image, sku, name, category, stock, cost, price, min)
            sku, name, stock, cost = p[2], p[3], p[5], p[6]
            row_total = stock * cost
            total_inv += row_total
            
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            # SKU y Stock centrados, Nombre izquierda, Precios derecha
            items = [
                (sku, Qt.AlignmentFlag.AlignCenter),
                (name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (str(stock), Qt.AlignmentFlag.AlignCenter),
                (f"$ {cost:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (f"$ {row_total:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            ]
            
            for i, (text, align) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                self.table.setItem(row_idx, i, item)
            
        lbl_sum = ui.QLabel(f"Inversión Total en Inventario: $ {total_inv:,.2f}")
        lbl_sum.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 10px;")
        layout = self.layout()
        layout.addWidget(lbl_sum)

class SalesDetailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = parent.db
        self.setWindowTitle("Detalle de Ventas")
        self.resize(800, 500)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        title = ui.QLabel("Historial de Ventas")
        title.setObjectName("Secondary")
        layout.addWidget(title)
        
        filters = QHBoxLayout()
        self.period = QComboBox()
        self.period.addItems(["Últimos 7 días", "Últimos 30 días", "Este Año", "Todo el tiempo"])
        self.period.currentIndexChanged.connect(self.load_data)
        filters.addWidget(ui.QLabel("Período:"))
        filters.addWidget(self.period)
        filters.addStretch()
        layout.addLayout(filters)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Ticket", "Fecha", "Monto", "Método"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(35)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        days = 30
        idx = self.period.currentIndex()
        if idx == 0: days = 7
        elif idx == 1: days = 30
        elif idx == 2: days = 365
        else: days = 9999
        
        # Necesitamos un método en DB para obtener ventas por período
        # Por ahora usaremos get_sales_data(days) pero ese devuelve (dia, monto)
        # Necesitamos uno que devuelva los detalles de los tickets.
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # Reparado: Usamos columna 'date' en lugar de 'created_at' y ordenamos correctamente
                cursor.execute("""
                    SELECT ticket_number, date, total_amount, payment_method 
                    FROM sales 
                    WHERE date >= date('now', ?)
                    ORDER BY date DESC
                """, (f'-{days} days',))
                sales = cursor.fetchall()
                
                self.table.setRowCount(0)
                for s in sales:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    for i, val in enumerate(s):
                        if i == 2: val = f"$ {val:,.2f}"
                        item = QTableWidgetItem(str(val))
                        
                        # Alineación Homogénea: Monto derecha, resto centro
                        if i == 2:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        else:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            
                        self.table.setItem(row, i, item)
        except Exception as e:
            print(f"Error al cargar detalle de ventas: {e}")



class DebtDetailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = parent.db
        self.setWindowTitle("Desglose de Deudas")
        self.resize(800, 500)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        title = ui.QLabel("Historial y Detalle de Compras a Crédito")
        title.setObjectName("Secondary")
        layout.addWidget(title)
        
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Fecha Compra", "Producto", "Monto", "Tarjeta", "Límite Pago", "Estado", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(35)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        debts = self.db.get_detailed_debts()
        self.table.setRowCount(0)
        from PyQt6.QtWidgets import QPushButton
        for p_id, date, prod_name, amount, card_name, is_paid, due_date in debts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            clean_date = str(date).split(" ")[0] if date else ""
            clean_due = str(due_date).split(" ")[0] if due_date else "N/A"
            
            # Alineación y formato
            col_data = [
                (clean_date, Qt.AlignmentFlag.AlignCenter),
                (prod_name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (f"$ {amount:,.2f}", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (str(card_name), Qt.AlignmentFlag.AlignCenter),
                (clean_due, Qt.AlignmentFlag.AlignCenter)
            ]
            
            for i, (text, align) in enumerate(col_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                self.table.setItem(row, i, item)
            
            status_text = "Pagado" if is_paid else "Pendiente"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if not is_paid:
                status_item.setForeground(QBrush(QColor("#EF4444"))) 
                btn_action = ui.TableActionButton("Pagar")
                btn_action.clicked.connect(lambda checked, pid=p_id: self.pay_debt(pid))
            else:
                status_item.setForeground(QBrush(QColor("#10B981"))) 
                btn_action = ui.TableActionButton("Revertir")
                btn_action.clicked.connect(lambda checked, pid=p_id: self.revert_debt(pid))
                
            self.table.setCellWidget(row, 6, btn_action)
            self.table.setItem(row, 5, status_item)

    def pay_debt(self, purchase_id):
        reply = QMessageBox.question(self, "Confirmar Pago", 
                                   "¿Está seguro de marcar esta deuda como PAGADA?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.set_purchase_paid_status(purchase_id, 1):
                self.load_data()
                if self.parent():
                    self.parent().update_dashboard_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar la deuda.")

    def revert_debt(self, purchase_id):
        reply = QMessageBox.question(self, "Confirmar Reversión", 
                                   "¿Desea marcar esta deuda como PENDIENTE nuevamente?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.set_purchase_paid_status(purchase_id, 0):
                self.load_data()
                if self.parent():
                    self.parent().update_dashboard_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo revertir el estado de la deuda.")


class ProfitDetailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = parent.db
        self.setWindowTitle("Detalle de Rentabilidad")
        self.resize(800, 600)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        title = ui.QLabel("Análisis de Ganancias")
        title.setObjectName("Secondary")
        layout.addWidget(title)
        
        # Gráfica Histórica
        self.chart = MplCanvas(self, width=8, height=4)
        layout.addWidget(self.chart)
        
        # Tabla de Detalles
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Periodo (Mes)", "Ganancia Estimada"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(35)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        monthly_data = self.db.get_monthly_profits(6)
        self.chart.plot_profit_history(monthly_data)
        
        self.table.setRowCount(0)
        for month, profit in reversed(monthly_data):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Periodo centro, Ganancia derecha
            item_month = QTableWidgetItem(str(month))
            item_month.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_month)
            
            item_profit = QTableWidgetItem(f"$ {profit:,.2f}")
            item_profit.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_profit.setForeground(QBrush(QColor("#10B981")))
            self.table.setItem(row, 1, item_profit)

class PendingOrdersDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Pedidos en Línea Pendientes")
        self.resize(800, 400)
        self.setStyleSheet(ui.STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        
        lbl = ui.QLabel("Pedidos Pendientes de Entrega")
        lbl.setObjectName("Title")
        layout.addWidget(lbl)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Producto", "Cant.", "Fecha Estimada", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        layout.addWidget(self.table)
        
        btn_close = ui.PrimaryButton("Cerrar")
        btn_close.clicked.connect(self.reject)
        layout.addWidget(btn_close)
        
        self.load_data()
        
    def load_data(self):
        orders = self.db.get_pending_orders()
        self.table.setRowCount(0)
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        for p_id, p_name, qty, d_date, total, sup_id in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            items = [
                (str(p_id), Qt.AlignmentFlag.AlignCenter),
                (p_name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (str(qty), Qt.AlignmentFlag.AlignCenter),
                (d_date[:10] if d_date else "N/A", Qt.AlignmentFlag.AlignCenter)
            ]
            
            for col, (text, align) in enumerate(items):
                it = QTableWidgetItem(text)
                it.setTextAlignment(align)
                self.table.setItem(row, col, it)
                
            btn_receive = ui.TableActionButton("✅ Recibir Pedido")
            btn_receive.setStyleSheet("background-color: #10B981; color: white;")
            btn_receive.clicked.connect(lambda checked, pid=p_id: self.receive_order(pid))
            self.table.setCellWidget(row, 4, btn_receive)
            
    def receive_order(self, purchase_id):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirmar Entrada", 
                                   "¿Confirmas que el pedido ha llegado y se agregará al inventario?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.receive_purchase(purchase_id):
                QMessageBox.information(self, "Éxito", "El stock físico ha sido actualizado.")
                self.load_data()
                # Informar éxito al parent para que recargue cuando cierre
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar el inventario.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
