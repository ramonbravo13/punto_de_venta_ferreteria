from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox, 
                             QCheckBox, QMessageBox, QTabWidget, QDateEdit, QScrollArea, QRadioButton,
                             QGridLayout, QCompleter)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtCore import QStringListModel
import ui_components as ui
from datetime import datetime
import uuid

class PurchasesTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.main_window = parent
        self.current_order_items = []
        self._syncing_price = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = ui.QLabel("Módulo de Compras")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; background: #0F172A; }
            QTabBar::tab { background: #1E293B; color: #94A3B8; padding: 10px 20px; font-weight: bold; border: 1px solid #334155; }
            QTabBar::tab:selected { background: #0EA5E9; color: white; }
        """)

        # Tab 1: Registro de Compra Rápida
        self.tab_new_order = QWidget()
        self.setup_new_order_tab()
        self.tabs.addTab(self.tab_new_order, "⚡ Compra Rápida")

        # Tab 2: Órdenes (Historial)
        self.tab_history = QWidget()
        self.setup_history_tab()
        self.tabs.addTab(self.tab_history, "📋 Órdenes")

        # Tab 3: Recibir Orden
        self.tab_receive = QWidget()
        self.setup_receive_tab()
        self.tabs.addTab(self.tab_receive, "📦 Recibir Orden")

        layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_payment_method_changed(self, text):
        visible = text in ["A crédito", "Tarjeta"]
        self.in_card.setVisible(visible)
        if hasattr(self, 'lbl_card'):
            self.lbl_card.setVisible(visible)

    def load_cards(self):
        self.in_card.clear()
        cards = self.db.get_all_credit_cards()
        for card in cards:
            c_id, name, cut_day, payment_day, bank, last_digits, limit, is_active = card
            if is_active:
                self.in_card.addItem(f"{name} ({bank} - {last_digits})", userData=c_id)

    def load_suppliers(self):
        self.in_supplier.clear()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM suppliers")
                for sid, name in cursor.fetchall():
                    self.in_supplier.addItem(name, sid)
        except Exception as e:
            pass

    def setup_new_order_tab(self):
        main_layout = QVBoxLayout(self.tab_new_order)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(20)

        # Formulario Cabecera
        header_card = ui.Card()
        header_layout = QGridLayout(header_card)
        header_layout.setSpacing(15)
        
        self.in_supplier = QComboBox()
        self.load_suppliers()
        
        self.in_type = QComboBox()
        self.in_type.addItems(["Física", "En Línea"])
        self.in_type.currentTextChanged.connect(self.on_purchase_type_changed)
        
        self.in_mode = QComboBox()
        self.in_mode.addItems(["Individual", "Combo (Paquete)"])
        self.in_mode.currentTextChanged.connect(self.on_purchase_mode_changed)
        
        self.in_state = QComboBox()
        self.in_state.addItems([
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ])
        self.in_state.setCurrentText("TX") # Default optional
        self.in_tracking = QLineEdit()
        self.in_tracking.setPlaceholderText("Tracking Number (Solo En Línea)")
        self.in_tracking.setEnabled(False)
        
        self.in_delivery_date = QDateEdit()
        self.in_delivery_date.setCalendarPopup(True)
        self.in_delivery_date.setDate(QDate.currentDate().addDays(3))
        self.in_delivery_date.setEnabled(False)
        
        self.in_payment_method = QComboBox()
        self.in_payment_method.addItems(["Efectivo", "Tarjeta", "A crédito"])
        self.in_payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        
        self.lbl_card = QLabel("Tarjeta:")
        self.lbl_card.setVisible(False)
        self.in_card = QComboBox()
        self.in_card.setVisible(False)
        self.load_cards()
        
        # Fila 0
        header_layout.addWidget(QLabel("Proveedor:"), 0, 0)
        header_layout.addWidget(self.in_supplier, 0, 1)
        
        header_layout.addWidget(QLabel("Modalidad:"), 0, 2)
        header_layout.addWidget(self.in_mode, 0, 3)
        
        header_layout.addWidget(QLabel("Tipo de Compra:"), 0, 4)
        header_layout.addWidget(self.in_type, 0, 5)
        
        header_layout.addWidget(QLabel("Estado de origen:"), 0, 6)
        header_layout.addWidget(self.in_state, 0, 7)
        
        # Fila 1
        header_layout.addWidget(QLabel("Tracking / Guía:"), 1, 0)
        header_layout.addWidget(self.in_tracking, 1, 1)
        
        header_layout.addWidget(QLabel("Fecha estimada entrega:"), 1, 2)
        header_layout.addWidget(self.in_delivery_date, 1, 3)
        
        header_layout.addWidget(QLabel("Método de Pago:"), 1, 4)
        header_layout.addWidget(self.in_payment_method, 1, 5)
        
        header_layout.addWidget(self.lbl_card, 1, 6)
        header_layout.addWidget(self.in_card, 1, 7)
        
        layout.addWidget(header_card)
        
        # Panel de Combo
        self.combo_card = ui.Card()
        combo_layout = QHBoxLayout(self.combo_card)
        self.in_combo_name = QLineEdit()
        self.in_combo_name.setPlaceholderText("Ej: Lote de Laptops HP")
        self.in_combo_total = QDoubleSpinBox()
        self.in_combo_total.setRange(0, 999999)
        self.in_combo_total.setPrefix("$ ")
        self.in_combo_total.setDecimals(2)
        self.in_combo_total.valueChanged.connect(self.on_combo_total_changed)
        self.in_combo_method = QComboBox()
        self.in_combo_method.addItems(["Equitativa", "Manual ($)"])
        self.in_combo_method.currentTextChanged.connect(self.on_combo_method_changed)
        
        combo_layout.addWidget(QLabel("Nombre del Combo:"))
        combo_layout.addWidget(self.in_combo_name)
        combo_layout.addWidget(QLabel("Inversión Total ($):"))
        combo_layout.addWidget(self.in_combo_total)
        combo_layout.addWidget(QLabel("Distribución Costo:"))
        combo_layout.addWidget(self.in_combo_method)
        self.combo_card.hide() # Oculto por defecto
        
        layout.addWidget(self.combo_card)

        # Productos a agregar
        # Productos a agregar (Grid Layout para que quepan todos los campos bien)
        products_grid = QGridLayout()
        products_grid.setSpacing(10)
        
        self.in_product = QLineEdit()
        self.in_product.setPlaceholderText("ID o SKU del producto...")
        
        self.product_completer_model = QStringListModel()
        self.product_completer = QCompleter(self.product_completer_model, self)
        self.product_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.product_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.product_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.in_product.setCompleter(self.product_completer)
        
        self.in_product.textEdited.connect(self.on_product_text_edited)
        self.product_completer.activated.connect(self.on_product_selected)
        
        self.in_qty = QDoubleSpinBox()
        self.in_qty.setDecimals(0)
        self.in_qty.setRange(1, 9999)
        
        self.in_cost = QDoubleSpinBox()
        self.in_cost.setDecimals(2)
        self.in_cost.setRange(0, 999999)
        self.in_cost.setPrefix("$ ")
        self.in_cost.valueChanged.connect(self.calculate_suggested_price)
        
        self.in_combo_pct = QDoubleSpinBox()
        self.in_combo_pct.setDecimals(2)
        self.in_combo_pct.setRange(0, 999999)
        self.in_combo_pct.setPrefix("$ ")
        self.in_combo_pct.hide() # Oculto por defecto
        self.lbl_combo_pct = QLabel("Costo Asignado:")
        self.lbl_combo_pct.hide()
        
        self.in_item_tax = QDoubleSpinBox()
        self.in_item_tax.setDecimals(2)
        self.in_item_tax.setRange(0, 100)
        self.in_item_tax.setSuffix(" %")
        self.in_item_tax.valueChanged.connect(self.calculate_suggested_price)
        
        self.in_item_margin = QDoubleSpinBox()
        self.in_item_margin.setDecimals(2)
        self.in_item_margin.setRange(0, 1000)
        self.in_item_margin.setSuffix(" %")
        self.in_item_margin.setValue(30.0) # Default margin
        self.in_item_margin.valueChanged.connect(self.calculate_suggested_price)
        
        self.lbl_sug_price = QLabel("$ 0.00")
        self.lbl_sug_price.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11pt;")
        
        self.btn_apply_sug = QPushButton("Aplicar")
        self.btn_apply_sug.setToolTip("Aplicar precio sugerido a precio de venta")
        self.btn_apply_sug.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply_sug.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #38BDF8;
                border: 1px solid #0EA5E9;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0EA5E9;
                color: white;
            }
        """)
        self.btn_apply_sug.clicked.connect(self.apply_suggested_price)
        
        sug_box = QHBoxLayout()
        sug_box.setContentsMargins(0, 0, 0, 0)
        sug_box.setSpacing(6)
        sug_box.addWidget(self.lbl_sug_price)
        sug_box.addWidget(self.btn_apply_sug)
        
        self.in_selling_price = QDoubleSpinBox()
        self.in_selling_price.setDecimals(2)
        self.in_selling_price.setRange(0, 999999)
        self.in_selling_price.setPrefix("$ ")
        
        btn_add_item = ui.PrimaryButton("Añadir a la Orden")
        btn_add_item.clicked.connect(self.add_item_to_order)
        
        btn_new_product = ui.PrimaryButton("+ Nuevo")
        btn_new_product.clicked.connect(self.open_new_product)
        
        # Fila 0
        products_grid.addWidget(QLabel("Producto:"), 0, 0)
        products_grid.addWidget(self.in_product, 0, 1, 1, 2) # Ocupa 2 columnas
        products_grid.addWidget(btn_new_product, 0, 3)
        products_grid.addWidget(QLabel("Cant:"), 0, 4)
        products_grid.addWidget(self.in_qty, 0, 5)
        products_grid.addWidget(QLabel("Costo Unit:"), 0, 6)
        products_grid.addWidget(self.in_cost, 0, 7)
        products_grid.addWidget(self.lbl_combo_pct, 0, 8)
        products_grid.addWidget(self.in_combo_pct, 0, 9)
        
        # Fila 1
        products_grid.addWidget(QLabel("Impuesto:"), 1, 0)
        products_grid.addWidget(self.in_item_tax, 1, 1)
        products_grid.addWidget(QLabel("Ganancia:"), 1, 2)
        products_grid.addWidget(self.in_item_margin, 1, 3)
        products_grid.addWidget(QLabel("Sugerido:"), 1, 4)
        products_grid.addLayout(sug_box, 1, 5)
        products_grid.addWidget(QLabel("Precio Venta:"), 1, 6)
        products_grid.addWidget(self.in_selling_price, 1, 7)
        
        # Fila 2
        products_grid.addWidget(btn_add_item, 2, 0, 1, 10)
        
        layout.addLayout(products_grid)

        # Tabla de items de la orden
        self.order_table = QTableWidget(0, 8)
        self.order_table.setHorizontalHeaderLabels(["ID", "Nombre", "Cant", "Costo U.", "Impuesto %", "P. Venta", "Subtotal", "Acción"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.order_table.setColumnWidth(7, 95)
        self.order_table.cellDoubleClicked.connect(self.on_order_table_double_clicked)
        layout.addWidget(self.order_table)
        
        # Totales y Costos Adicionales
        totals_card = ui.Card()
        totals_layout = QHBoxLayout(totals_card)
        self.in_tax = QDoubleSpinBox()
        self.in_tax.setRange(0, 999999)
        self.in_tax.setPrefix("$ ")
        self.in_tax.valueChanged.connect(self.update_order_totals)
        
        self.in_shipping = QDoubleSpinBox()
        self.in_shipping.setRange(0, 999999)
        self.in_shipping.setPrefix("$ ")
        self.in_shipping.valueChanged.connect(self.update_order_totals)
        
        self.lbl_subtotal = QLabel("$ 0.00")
        self.lbl_subtotal.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.lbl_total = QLabel("$ 0.00")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 14pt; color: #0EA5E9;")
        
        totals_layout.addWidget(QLabel("Subtotal:"))
        totals_layout.addWidget(self.lbl_subtotal)
        totals_layout.addStretch()
        totals_layout.addWidget(QLabel("Impuestos / Tax:"))
        totals_layout.addWidget(self.in_tax)
        totals_layout.addWidget(QLabel("Costo Envío:"))
        totals_layout.addWidget(self.in_shipping)
        totals_layout.addStretch()
        
        lbl_tot_title = QLabel("TOTAL:")
        lbl_tot_title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        totals_layout.addWidget(lbl_tot_title)
        totals_layout.addWidget(self.lbl_total)
        
        layout.addWidget(totals_card)

        # Acciones
        actions_layout = QHBoxLayout()
        btn_confirm = ui.PrimaryButton("Registrar Compra")
        btn_confirm.setMinimumHeight(40)
        btn_confirm.clicked.connect(self.save_order)
        
        actions_layout.addWidget(btn_confirm)
        layout.addLayout(actions_layout)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def open_new_product(self):
        if hasattr(self.main_window, 'open_new_product_dialog'):
            self.main_window.open_new_product_dialog()

    def on_purchase_mode_changed(self, mode):
        if mode == "Combo (Paquete)":
            self.combo_card.show()
            self.on_combo_method_changed(self.in_combo_method.currentText())
        else:
            self.combo_card.hide()
            self.in_cost.setEnabled(True)
            self.lbl_combo_pct.hide()
            self.in_combo_pct.hide()
            
    def on_combo_method_changed(self, method):
        if self.in_mode.currentText() != "Combo (Paquete)": return
        
        if method == "Equitativa":
            self.in_cost.setEnabled(False)
            self.in_cost.setValue(0) # Será calculado después
            self.lbl_combo_pct.hide()
            self.in_combo_pct.hide()
        elif method == "Manual ($)":
            self.in_cost.setEnabled(False)
            self.in_cost.setValue(0)
            self.lbl_combo_pct.show()
            self.in_combo_pct.show()
            
        self.recalculate_combo_costs()
        self.refresh_order_table()
        
    def on_combo_total_changed(self):
        if self.in_mode.currentText() == "Combo (Paquete)":
            self.recalculate_combo_costs()
            self.refresh_order_table()

    def on_purchase_type_changed(self, text):
        is_online = (text == "En Línea")
        self.in_tracking.setEnabled(is_online)
        self.in_delivery_date.setEnabled(is_online)

    def calculate_suggested_price(self):
        cost = self.in_cost.value()
        tax = self.in_item_tax.value() / 100.0
        margin = self.in_item_margin.value() / 100.0
        
        cost_with_tax = cost * (1.0 + tax)
        suggested = round(cost_with_tax * (1.0 + margin), 2)
        self.lbl_sug_price.setText(f"$ {suggested:,.2f}")
        self.in_selling_price.setValue(suggested)

    def apply_suggested_price(self):
        cost = self.in_cost.value()
        tax = self.in_item_tax.value() / 100.0
        margin = self.in_item_margin.value() / 100.0
        cost_with_tax = cost * (1.0 + tax)
        suggested = round(cost_with_tax * (1.0 + margin), 2)
        self.in_selling_price.setValue(suggested)
        self.lbl_sug_price.setText(f"$ {suggested:,.2f}")

    def on_product_text_edited(self, text):
        if not text or len(text) < 2:
            self.product_completer_model.setStringList([])
            return
            
        results = self.db.search_products(text, limit=15)
        suggestions = []
        for sku, name, _, _, _, marca, modelo in results:
            clean_sku = sku if sku else ""
            extra = []
            if marca: extra.append(marca)
            if modelo: extra.append(modelo)
            extra_str = f" | {' '.join(extra)}" if extra else ""
            suggestions.append(f"{clean_sku} | {name}{extra_str}")
            
        self.product_completer_model.setStringList(suggestions)
        self.product_completer.complete()

    def on_product_selected(self, text):
        if " | " not in text: return
        parts = text.split(" | ")
        sku = parts[0].strip()
        name = parts[1].strip() if len(parts) > 1 else ""
        query = sku if sku else name
        self.in_product.setText(query)
        
        product = self.db.get_product_by_sku_or_name(query)
        if product:
            p_id = product[0]
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT p.cost_price, p.tax_percentage, p.selling_price,
                               IFNULL((
                                   SELECT MAX(c) FROM (
                                       SELECT (total_cost * 1.0 / quantity) as c FROM purchases WHERE product_id = p.id AND quantity > 0
                                       UNION 
                                       SELECT actual_unit_cost as c FROM purchase_order_details WHERE product_id = p.id
                                   )
                               ), p.cost_price) as last_cost
                        FROM products p WHERE p.id = ?
                    """, (p_id,))
                    row = cursor.fetchone()
                    if row:
                        cost, tax, price, last_cost = row
                        if (cost == 0 or cost is None) and last_cost and last_cost > 0:
                            cost = last_cost
                            
                        self._syncing_price = True
                        try:
                            self.in_cost.setValue(float(cost) if cost else 0.0)
                            self.in_item_tax.setValue(float(tax) if tax else 0.0)
                            self.in_selling_price.setValue(float(price) if price else 0.0)
                            
                            cost_with_tax = (float(cost) if cost else 0.0) * (1.0 + ((float(tax) if tax else 0.0) / 100.0))
                            if cost_with_tax > 0 and price and price > 0:
                                current_margin = ((float(price) / cost_with_tax) - 1.0) * 100.0
                                self.in_item_margin.setValue(max(0.0, round(current_margin, 2)))
                            else:
                                self.in_item_margin.setValue(30.0)
                                
                            margin_val = self.in_item_margin.value() / 100.0
                            suggested = round(cost_with_tax * (1.0 + margin_val), 2)
                            self.lbl_sug_price.setText(f"$ {suggested:,.2f}")
                        finally:
                            self._syncing_price = False
                            
                        self.in_qty.setValue(1)
            except Exception as e:
                print(f"Error al seleccionar producto: {e}")

    def add_item_to_order(self):
        raw_query = self.in_product.text().strip()
        if not raw_query: return
        
        query = raw_query.split(" | ")[0].strip() if " | " in raw_query else raw_query
        if not query and " | " in raw_query:
            parts = raw_query.split(" | ")
            query = parts[1].strip() if len(parts) > 1 else raw_query
            
        product = self.db.get_product_by_sku_or_name(query)
        if not product:
            QMessageBox.warning(self, "Error", "Producto no encontrado.")
            return
            
        p_id, p_name, _, _, _ = product
        qty = int(self.in_qty.value())
        cost = self.in_cost.value()
        tax = self.in_item_tax.value()
        selling_price = self.in_selling_price.value()
        combo_pct = self.in_combo_pct.value()
        
        item = {
            'product_id': p_id,
            'name': p_name,
            'quantity': qty,
            'unit_cost': cost,
            'tax_percentage': tax,
            'selling_price': selling_price,
            'combo_pct': combo_pct
        }
        self.current_order_items.append(item)
        self.recalculate_combo_costs()
        self.refresh_order_table()
        
        # Limpiar variables temporales utilizadas durante la captura del producto
        self._syncing_price = True
        try:
            self.in_product.clear()
            self.in_qty.setValue(1)
            self.in_cost.setValue(0)
            self.in_item_tax.setValue(0)
            self.in_item_margin.setValue(30.0)
            self.in_selling_price.setValue(0)
            self.in_combo_pct.setValue(0)
            self.lbl_sug_price.setText("$ 0.00")
        finally:
            self._syncing_price = False
        
    def recalculate_combo_costs(self):
        if self.in_mode.currentText() != "Combo (Paquete)": return
        total_investment = self.in_combo_total.value()
        method = self.in_combo_method.currentText()
        
        total_items_qty = sum(item['quantity'] for item in self.current_order_items)
        
        for item in self.current_order_items:
            if method == "Equitativa":
                if total_items_qty > 0:
                    item['unit_cost'] = total_investment / total_items_qty
                else:
                    item['unit_cost'] = 0
            elif method == "Manual ($)":
                manual_cost = item.get('combo_pct', 0)
                item['unit_cost'] = manual_cost / item['quantity'] if item['quantity'] > 0 else 0

    def on_order_table_double_clicked(self, row, column):
        if column != 7:
            self.edit_order_item(row)

    def edit_order_item(self, index):
        if not (0 <= index < len(self.current_order_items)):
            return
        item = self.current_order_items[index]
        is_combo = self.in_mode.currentText() == "Combo (Paquete)"
        combo_method = self.in_combo_method.currentText() if is_combo else None
        
        dialog = EditOrderItemDialog(item, is_combo=is_combo, combo_method=combo_method, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_data()
            item['quantity'] = updated['quantity']
            if not (is_combo and combo_method == "Equitativa"):
                item['unit_cost'] = updated['unit_cost']
            item['tax_percentage'] = updated['tax_percentage']
            item['selling_price'] = updated['selling_price']
            if is_combo and combo_method == "Manual ($)":
                item['combo_pct'] = updated['combo_pct']
                
            self.recalculate_combo_costs()
            self.refresh_order_table()

    def remove_order_item(self, index):
        if 0 <= index < len(self.current_order_items):
            del self.current_order_items[index]
            self.refresh_order_table()

    def refresh_order_table(self):
        self.order_table.setRowCount(0)
        subtotal = 0
        for idx, item in enumerate(self.current_order_items):
            row = self.order_table.rowCount()
            self.order_table.insertRow(row)
            
            st = item['quantity'] * item['unit_cost']
            subtotal += st
            
            col_data = [
                str(item['product_id']),
                item['name'],
                str(item['quantity']),
                f"$ {item['unit_cost']:.2f}",
                f"{item['tax_percentage']:.2f} %",
                f"$ {item['selling_price']:.2f}",
                f"$ {st:.2f}"
            ]
            for col_idx, text_val in enumerate(col_data):
                t_item = QTableWidgetItem(text_val)
                t_item.setFlags(t_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.order_table.setItem(row, col_idx, t_item)
            
            btn_edit = QPushButton("✏️")
            btn_edit.setToolTip("Editar artículo (Cantidad, Costo, Impuesto, Precio)")
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #0EA5E9;
                    color: white;
                    border-radius: 4px;
                    padding: 4px;
                    font-weight: bold;
                    min-width: 28px;
                    max-width: 32px;
                    min-height: 24px;
                    max-height: 28px;
                }
                QPushButton:hover {
                    background-color: #0284C7;
                }
            """)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda checked, i=idx: self.edit_order_item(i))

            btn_delete = QPushButton("❌")
            btn_delete.setToolTip("Eliminar producto de la orden")
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444;
                    color: white;
                    border-radius: 4px;
                    padding: 4px;
                    font-weight: bold;
                    min-width: 28px;
                    max-width: 32px;
                    min-height: 24px;
                    max-height: 28px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
            """)
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.clicked.connect(lambda checked, i=idx: self.remove_order_item(i))
            
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(btn_edit)
            layout.addWidget(btn_delete)
            self.order_table.setCellWidget(row, 7, widget)
            
        self.lbl_subtotal.setText(f"$ {subtotal:.2f}")
        self.update_order_totals()

    def update_order_totals(self):
        subtotal = sum(i['quantity'] * i['unit_cost'] for i in self.current_order_items)
        tax = self.in_tax.value()
        shipping = self.in_shipping.value()
        total = subtotal + tax + shipping
        self.lbl_total.setText(f"$ {total:.2f}")
        return subtotal, tax, shipping, total

    def save_order(self):
        if not self.current_order_items:
            QMessageBox.warning(self, "Error", "Agregue productos a la compra.")
            return
            
        is_combo = self.in_mode.currentText() == "Combo (Paquete)"
        if is_combo and self.in_combo_method.currentText() == "Manual ($)":
            total_manual = sum(item.get('combo_pct', 0) for item in self.current_order_items)
            total_investment = self.in_combo_total.value()
            if abs(total_manual - total_investment) > 0.01:
                QMessageBox.warning(self, "Error de Validación", f"La suma del costo asignado manualmente (${total_manual:.2f}) no coincide con la inversión total del combo (${total_investment:.2f}).")
                return
                
        supp_id = self.in_supplier.currentData()
        p_type = self.in_type.currentText()
        track = self.in_tracking.text() if p_type == "En Línea" else ""
        del_date = self.in_delivery_date.date().toString("yyyy-MM-dd") if p_type == "En Línea" else None
        pay_method = self.in_payment_method.currentText()
        
        subtotal, tax, shipping, total = self.update_order_totals()
        
        order_num = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Estado inicial SIEMPRE como "Pendiente de recibir" para que el trigger de inventario actúe si es Física
        initial_status = "Pendiente de recibir"
        
        is_combo = self.in_mode.currentText() == "Combo (Paquete)"
        combo_name = self.in_combo_name.text() if is_combo else None
        combo_ref = str(uuid.uuid4()) if is_combo else None
        
        # Preparar los items con combo_ref y combo_name si aplica
        items_to_save = []
        for it in self.current_order_items:
            # Creamos un dict nuevo para pasarlo a add_purchase_order_details
            it_copy = dict(it)
            if is_combo:
                it_copy['combo_ref'] = combo_ref
                it_copy['combo_name'] = combo_name
            items_to_save.append(it_copy)
        
        # 1. Crear Orden
        payment_method = self.in_payment_method.currentText()
        card_id = None
        if payment_method in ["A crédito", "Tarjeta"]:
            card_id = self.in_card.currentData()
            
        order_id = self.db.create_purchase_order(
            order_number=order_num, supplier_id=supp_id, purchase_type=p_type,
            tracking_number=track, status=initial_status,
            subtotal=subtotal, tax=tax, shipping=shipping, total=total,
            estimated_delivery_date=del_date, payment_method=payment_method, card_id=card_id,
            origin_state=self.in_state.currentText()
        )
        
        if not order_id:
            QMessageBox.critical(self, "Error", "No se pudo crear la compra.")
            return
            
        try:
            # 2. Agregar Detalles
            self.db.add_purchase_order_details(order_id, items_to_save, tax, shipping)
            
            # 2.5. Actualizar Precios de Venta en el Catálogo (inmediato para ambos tipos)
            for item in self.current_order_items:
                try:
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE products SET selling_price = ?, tax_percentage = ? WHERE id = ?", 
                                       (item['selling_price'], item['tax_percentage'], item['product_id']))
                        conn.commit()
                except Exception as e:
                    print(f"Error silencioso al actualizar precio de {item['product_id']}: {e}")
            
            # 3. Si es Física, afectar inventario y finanzas inmediatamente
            if p_type == "Física":
                received_items = []
                details = self.db.get_purchase_order_details(order_id)
                for d in details:
                    received_items.append({
                        'detail_id': d[0],
                        'received_qty': d[4], 
                        'product_id': d[1],
                        'actual_unit_cost': d[7],
                        'condition': 'Buenas Condiciones'
                    })
                # El método update_purchase_order_status ya tiene lógica para 'Recibida'
                success = self.db.update_purchase_order_status(order_id, "Recibida", received_items, payment_method=pay_method, is_paid=(pay_method=="Efectivo"))
                if not success:
                    raise Exception("Fallo interno al actualizar estado físico de la orden (inventario/finanzas).")
                    
                QMessageBox.information(self, "Éxito", f"Compra Física Registrada. Inventario y finanzas actualizados.")
            else:
                QMessageBox.information(self, "Éxito", f"Compra En Línea Registrada como Pendiente. Número de Orden: {order_num}")
                
            self.current_order_items.clear()
            self.refresh_order_table()
            self.load_history()
            self.load_receive_orders()
            self.clear_form()
            
        except Exception as e:
            # Rollback manual de la orden creada
            print(f"Error general en save_order. Haciendo rollback de orden {order_id}: {e}")
            self.db.delete_purchase_order(order_id)
            QMessageBox.critical(self, "Error Crítico", f"Ha ocurrido un error al procesar la compra. La operación ha sido cancelada y los cambios revertidos.\nDetalle: {e}")

    def clear_form(self):
        if self.in_supplier.count() > 0:
            self.in_supplier.setCurrentIndex(0)
        self.in_type.setCurrentIndex(0)
        self.in_mode.setCurrentIndex(0)
        self.in_state.setCurrentText("TX")
        self.in_tracking.clear()
        self.in_delivery_date.setDate(QDate.currentDate().addDays(3))
        self.in_payment_method.setCurrentIndex(0)
        if hasattr(self, 'in_card') and self.in_card.count() > 0:
            self.in_card.setCurrentIndex(0)
        
        self.in_combo_name.clear()
        self.in_combo_total.setValue(0)
        self.in_combo_method.setCurrentIndex(0)
        
        self.in_product.clear()
        self.in_qty.setValue(1)
        self.in_cost.setValue(0)
        self.in_combo_pct.setValue(0)
        self.in_item_tax.setValue(0)
        self.in_item_margin.setValue(30.0)
        self.in_selling_price.setValue(0)
        self.in_selling_price.setProperty("auto_update", False)
        self.lbl_sug_price.setText("$ 0.00")
        
        self.in_tax.setValue(0)
        self.in_shipping.setValue(0)
        
        # Limpiar tabla forzadamente por si acaso
        self.current_order_items = []
        self.order_table.setRowCount(0)
        self.lbl_subtotal.setText("$ 0.00")
        self.lbl_total.setText("$ 0.00")

    # --- TAB 2: ÓRDENES (HISTORIAL) ---
    def setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        
        self.hist_table = QTableWidget(0, 9)
        self.hist_table.setHorizontalHeaderLabels(["ID Orden", "Fecha", "Tipo", "Proveedor", "Total", "Tracking", "Estado", "Origen", "Acciones"])
        self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.hist_table)

    def load_history(self):
        self.hist_table.setRowCount(0)
        orders = self.db.get_purchase_orders(limit=100)
        
        for po_id, num, date, sup, ptype, status, total, track, origin in orders:
            row = self.hist_table.rowCount()
            self.hist_table.insertRow(row)
            
            self.hist_table.setItem(row, 0, QTableWidgetItem(num))
            self.hist_table.setItem(row, 1, QTableWidgetItem(date[:10]))
            self.hist_table.setItem(row, 2, QTableWidgetItem(ptype))
            self.hist_table.setItem(row, 3, QTableWidgetItem(sup))
            self.hist_table.setItem(row, 4, QTableWidgetItem(f"$ {total:.2f}"))
            self.hist_table.setItem(row, 5, QTableWidgetItem(track if track else "N/A"))
            
            item_status = QTableWidgetItem(status)
            if status == "Recibida":
                item_status.setForeground(Qt.GlobalColor.green)
            elif status == "Pendiente / Por llegar":
                item_status.setForeground(Qt.GlobalColor.yellow)
            elif status == "Rechazada / Devuelta":
                item_status.setForeground(Qt.GlobalColor.red)
                
            self.hist_table.setItem(row, 6, item_status)
            self.hist_table.setItem(row, 7, QTableWidgetItem(origin if origin else "N/A"))
            
            btn_details = ui.TableActionButton("Detalles")
            btn_details.clicked.connect(lambda checked, pid=po_id, pnum=num: self.view_order_details(pid, pnum))
            self.hist_table.setCellWidget(row, 8, btn_details)

    def view_order_details(self, order_id, order_num):
        dialog = PurchaseOrderDetailDialog(self.db, order_id, order_num, self)
        dialog.exec()

    # --- TAB 3: RECIBIR ORDEN ---
    def setup_receive_tab(self):
        layout = QVBoxLayout(self.tab_receive)
        
        lbl = ui.QLabel("Seleccione una orden pendiente para validar su recepción:")
        layout.addWidget(lbl)
        
        self.receive_table = QTableWidget(0, 6)
        self.receive_table.setHorizontalHeaderLabels(["ID Orden", "Fecha", "Proveedor", "Tracking", "Total", "Acciones"])
        self.receive_table.setAlternatingRowColors(True)
        self.receive_table.verticalHeader().setDefaultSectionSize(40)
        self.receive_table.verticalHeader().setVisible(False)
        self.receive_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.receive_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.receive_table.setColumnWidth(0, 110)
        self.receive_table.setColumnWidth(1, 100)
        self.receive_table.setColumnWidth(3, 120)
        self.receive_table.setColumnWidth(4, 100)
        self.receive_table.setColumnWidth(5, 270)
        
        layout.addWidget(self.receive_table)

    def load_receive_orders(self):
        self.receive_table.setRowCount(0)
        orders = self.db.get_purchase_orders(status="Pendiente de recibir", limit=100)
        
        for po_id, num, date, sup, ptype, status, total, track, origin in orders:
            row = self.receive_table.rowCount()
            self.receive_table.insertRow(row)
            
            item_num = QTableWidgetItem(num)
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.receive_table.setItem(row, 0, item_num)
            
            item_date = QTableWidgetItem(date[:10])
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.receive_table.setItem(row, 1, item_date)
            
            item_sup = QTableWidgetItem(sup)
            item_sup.setToolTip(sup)
            self.receive_table.setItem(row, 2, item_sup)
            
            item_track = QTableWidgetItem(track if track else "N/A")
            item_track.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.receive_table.setItem(row, 3, item_track)
            
            item_total = QTableWidgetItem(f"$ {total:.2f}")
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.receive_table.setItem(row, 4, item_total)
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)
            
            btn_details = ui.TableActionButton("👁️ Detalles")
            btn_details.setStyleSheet("background-color: #0284C7; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            btn_details.setToolTip("Ver detalles y productos de la orden")
            btn_details.clicked.connect(lambda checked, pid=po_id, pnum=num: self.view_order_details(pid, pnum))
            
            btn_receive = ui.PrimaryButton("📦 Validar Recepción")
            btn_receive.setStyleSheet("background-color: #F59E0B; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            btn_receive.setToolTip("Validar recepción de mercancía e ingresar a inventario")
            btn_receive.clicked.connect(lambda checked, oid=po_id: self.open_receive_dialog(oid))
            
            actions_layout.addWidget(btn_details)
            actions_layout.addWidget(btn_receive)
            
            self.receive_table.setCellWidget(row, 5, actions_widget)

    def on_tab_changed(self, index):
        if index == 1:
            self.load_history()
        elif index == 2:
            self.load_receive_orders()

    def open_receive_dialog(self, order_id):
        dialog = ReceiveOrderDialog(self.db, order_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_history()
            self.load_receive_orders()

class EditOrderItemDialog(QDialog):
    def __init__(self, item, is_combo=False, combo_method="Equitativa", parent=None):
        super().__init__(parent)
        self.item = item
        self.is_combo = is_combo
        self.combo_method = combo_method
        self._syncing = False
        self.setWindowTitle("Editar Artículo de la Orden")
        self.setStyleSheet(ui.STYLE_SHEET)
        self.setMinimumWidth(480)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header Info Card
        header_card = ui.Card()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        title_lbl = QLabel(f"✏️ Editar: {self.item.get('name', 'Producto')}")
        title_lbl.setStyleSheet("font-size: 13pt; font-weight: bold; color: #0EA5E9;")
        title_lbl.setWordWrap(True)
        header_layout.addWidget(title_lbl)
        
        id_lbl = QLabel(f"ID Producto: {self.item.get('product_id', 'N/A')}")
        id_lbl.setStyleSheet("color: #94A3B8; font-size: 9pt;")
        header_layout.addWidget(id_lbl)
        
        layout.addWidget(header_card)
        
        # Form Card
        form_card = ui.Card()
        form_layout = QGridLayout(form_card)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 15, 15, 15)
        
        # 1. Cantidad
        lbl_qty = QLabel("Cantidad:")
        lbl_qty.setStyleSheet("font-weight: bold;")
        self.in_qty = QDoubleSpinBox()
        self.in_qty.setDecimals(0)
        self.in_qty.setRange(1, 99999)
        self.in_qty.valueChanged.connect(self.on_qty_changed)
        
        form_layout.addWidget(lbl_qty, 0, 0)
        form_layout.addWidget(self.in_qty, 0, 1)
        
        # 2. Costo Unitario
        lbl_cost = QLabel("Costo Unitario ($):")
        lbl_cost.setStyleSheet("font-weight: bold;")
        self.in_cost = QDoubleSpinBox()
        self.in_cost.setDecimals(2)
        self.in_cost.setRange(0, 999999)
        self.in_cost.setPrefix("$ ")
        if self.is_combo and self.combo_method == "Equitativa":
            self.in_cost.setEnabled(False)
            self.in_cost.setToolTip("El costo unitario se distribuye automáticamente en la modalidad Combo Equitativa.")
        self.in_cost.valueChanged.connect(self.on_margin_or_cost_changed)
        
        form_layout.addWidget(lbl_cost, 1, 0)
        form_layout.addWidget(self.in_cost, 1, 1)
        
        # 3. Impuesto %
        lbl_tax = QLabel("Impuesto (%):")
        lbl_tax.setStyleSheet("font-weight: bold;")
        self.in_tax = QDoubleSpinBox()
        self.in_tax.setDecimals(2)
        self.in_tax.setRange(0, 100)
        self.in_tax.setSuffix(" %")
        self.in_tax.valueChanged.connect(self.on_margin_or_cost_changed)
        
        form_layout.addWidget(lbl_tax, 2, 0)
        form_layout.addWidget(self.in_tax, 2, 1)
        
        # 4. Margen / Ganancia deseada
        lbl_margin = QLabel("Ganancia / Margen:")
        lbl_margin.setStyleSheet("font-weight: bold;")
        self.in_margin = QDoubleSpinBox()
        self.in_margin.setDecimals(2)
        self.in_margin.setRange(0, 1000)
        self.in_margin.setSuffix(" %")
        self.in_margin.valueChanged.connect(self.on_margin_or_cost_changed)
        
        form_layout.addWidget(lbl_margin, 3, 0)
        form_layout.addWidget(self.in_margin, 3, 1)
        
        # 5. Precio Sugerido con botón Aplicar
        lbl_sug_title = QLabel("Precio Sugerido:")
        lbl_sug_title.setStyleSheet("color: #94A3B8;")
        sug_box = QHBoxLayout()
        self.lbl_sug_price = QLabel("$ 0.00")
        self.lbl_sug_price.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11pt;")
        btn_apply_sug = QPushButton("Aplicar")
        btn_apply_sug.setToolTip("Copiar precio sugerido a precio de venta")
        btn_apply_sug.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_apply_sug.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #38BDF8;
                border: 1px solid #0EA5E9;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0EA5E9;
                color: white;
            }
        """)
        btn_apply_sug.clicked.connect(self.apply_suggested_price)
        sug_box.addWidget(self.lbl_sug_price)
        sug_box.addWidget(btn_apply_sug)
        sug_box.addStretch()
        
        form_layout.addWidget(lbl_sug_title, 4, 0)
        form_layout.addLayout(sug_box, 4, 1)
        
        # 6. Precio de Venta
        lbl_sp = QLabel("Precio de Venta ($):")
        lbl_sp.setStyleSheet("font-weight: bold;")
        self.in_selling_price = QDoubleSpinBox()
        self.in_selling_price.setDecimals(2)
        self.in_selling_price.setRange(0, 999999)
        self.in_selling_price.setPrefix("$ ")
        
        form_layout.addWidget(lbl_sp, 5, 0)
        form_layout.addWidget(self.in_selling_price, 5, 1)
        
        layout.addWidget(form_card)
        
        # Resumen Subtotal Card
        subtotal_card = ui.Card()
        subtotal_layout = QHBoxLayout(subtotal_card)
        subtotal_layout.setContentsMargins(15, 10, 15, 10)
        lbl_st_desc = QLabel("Subtotal Compra (Cant × Costo U.):")
        lbl_st_desc.setStyleSheet("font-weight: bold;")
        self.lbl_subtotal_preview = QLabel("$ 0.00")
        self.lbl_subtotal_preview.setStyleSheet("font-size: 12pt; font-weight: bold; color: #10B981;")
        subtotal_layout.addWidget(lbl_st_desc)
        subtotal_layout.addStretch()
        subtotal_layout.addWidget(self.lbl_subtotal_preview)
        layout.addWidget(subtotal_card)
        
        if self.is_combo and self.combo_method == "Equitativa":
            info_combo = QLabel("ℹ️ Modo Combo Equitativo: El costo unitario se recalcula automáticamente según la inversión total del combo.")
            info_combo.setStyleSheet("color: #F59E0B; font-size: 9pt;")
            info_combo.setWordWrap(True)
            layout.addWidget(info_combo)
            
        # Botones de Acción
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("Secondary")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = ui.PrimaryButton("💾 Guardar Cambios")
        btn_save.setMinimumHeight(38)
        btn_save.clicked.connect(self.validate_and_accept)
        
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)
        
        # Cargar valores iniciales
        self._syncing = True
        try:
            self.in_qty.setValue(float(self.item.get('quantity', 1)))
            init_c = float(self.item.get('unit_cost', 0.0))
            init_t = float(self.item.get('tax_percentage', 0.0))
            init_sp = float(self.item.get('selling_price', 0.0))
            
            self.in_cost.setValue(init_c)
            self.in_tax.setValue(init_t)
            self.in_selling_price.setValue(init_sp)
            
            cost_with_tax = init_c * (1.0 + init_t / 100.0)
            if cost_with_tax > 0 and init_sp > 0:
                init_m = ((init_sp / cost_with_tax) - 1.0) * 100.0
                self.in_margin.setValue(max(0.0, round(init_m, 2)))
            else:
                self.in_margin.setValue(30.0)
                
            sug = round(cost_with_tax * (1.0 + self.in_margin.value() / 100.0), 2)
            self.lbl_sug_price.setText(f"$ {sug:,.2f}")
            self.on_qty_changed()
        finally:
            self._syncing = False
        
    def on_qty_changed(self):
        qty = self.in_qty.value()
        cost = self.in_cost.value()
        st = qty * cost
        self.lbl_subtotal_preview.setText(f"$ {st:,.2f}")

    def on_margin_or_cost_changed(self):
        cost = self.in_cost.value()
        tax = self.in_tax.value() / 100.0
        margin = self.in_margin.value() / 100.0
        cost_with_tax = cost * (1.0 + tax)
        suggested = round(cost_with_tax * (1.0 + margin), 2)
        self.lbl_sug_price.setText(f"$ {suggested:,.2f}")
        self.in_selling_price.setValue(suggested)
        
        qty = self.in_qty.value()
        st = qty * cost
        self.lbl_subtotal_preview.setText(f"$ {st:,.2f}")

    def apply_suggested_price(self):
        cost = self.in_cost.value()
        tax = self.in_tax.value() / 100.0
        margin = self.in_margin.value() / 100.0
        cost_with_tax = cost * (1.0 + tax)
        suggested = round(cost_with_tax * (1.0 + margin), 2)
        self.in_selling_price.setValue(suggested)
        self.lbl_sug_price.setText(f"$ {suggested:,.2f}")
        
    def validate_and_accept(self):
        if self.in_qty.value() <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor a 0.")
            return
        self.accept()
        
    def get_data(self):
        qty = int(self.in_qty.value())
        cost = self.in_cost.value()
        tax = self.in_tax.value()
        selling = self.in_selling_price.value()
        return {
            'quantity': qty,
            'unit_cost': cost,
            'tax_percentage': tax,
            'selling_price': selling,
            'combo_pct': cost * qty
        }

class ReceiveOrderDialog(QDialog):
    def __init__(self, db, order_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self.setWindowTitle(f"Validación de Recepción - Orden #{order_id}")
        self.resize(800, 600)
        self.setStyleSheet(ui.STYLE_SHEET)
        self.received_data = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        title = ui.QLabel("Verificar Mercancía Recibida")
        title.setObjectName("Title")
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        btn_details = ui.TableActionButton("👁️ Ver Detalles de la Orden")
        btn_details.setStyleSheet("background-color: #0284C7; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold;")
        btn_details.clicked.connect(self.show_order_details)
        top_layout.addWidget(btn_details)
        layout.addLayout(top_layout)
        
        # Pregunta de validación
        question_layout = QHBoxLayout()
        question_lbl = QLabel("¿Los productos fueron recibidos en buen estado?")
        question_lbl.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;")
        
        self.radio_yes = QRadioButton("Sí (Validar y Autorizar)")
        self.radio_yes.setStyleSheet("color: #10B981; font-weight: bold; font-size: 12pt;")
        self.radio_no = QRadioButton("No (Rechazar/Devolver)")
        self.radio_no.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 12pt;")
        
        self.radio_yes.setChecked(True)
        self.radio_yes.toggled.connect(self.on_condition_changed)
        
        question_layout.addWidget(question_lbl)
        question_layout.addStretch()
        question_layout.addWidget(self.radio_yes)
        question_layout.addWidget(self.radio_no)
        layout.addLayout(question_layout)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Producto", "Ordenado", "Cant. Recibida", "Costo Real/U (Congelado)", "Acción"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        
        self.table.setColumnWidth(1, 85)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 175)
        self.table.setColumnWidth(4, 95)
        
        layout.addWidget(self.table)
        
        details = self.db.get_purchase_order_details(self.order_id)
        for d in details:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            prod_text = f"{d[2]} ({d[3]})"
            item_prod = QTableWidgetItem(prod_text)
            item_prod.setToolTip(prod_text)
            self.table.setItem(row, 0, item_prod)
            
            item_ord = QTableWidgetItem(str(d[4]))
            item_ord.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_ord)
            
            spin_qty = QDoubleSpinBox()
            spin_qty.setDecimals(0)
            spin_qty.setRange(0, 9999)
            spin_qty.setValue(d[4]) 
            self.table.setCellWidget(row, 2, spin_qty)
            
            self.table.setItem(row, 3, QTableWidgetItem(f"$ {d[7]:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem("Autorizado"))
            
            self.received_data.append({
                'detail_id': d[0],
                'product_id': d[1],
                'actual_unit_cost': d[7],
                'spin_qty': spin_qty
            })
            
        self.btn_confirm = ui.PrimaryButton("Confirmar Recepción e Ingresar a Inventario")
        self.btn_confirm.clicked.connect(self.confirm_receipt)
        layout.addWidget(self.btn_confirm)
        
    def on_condition_changed(self):
        if self.radio_no.isChecked():
            self.table.setEnabled(False)
            self.btn_confirm.setText("Rechazar Orden (No afectar inventario)")
            self.btn_confirm.setStyleSheet("background-color: #EF4444; color: white;")
        else:
            self.table.setEnabled(True)
            self.btn_confirm.setText("Confirmar Recepción e Ingresar a Inventario")
            self.btn_confirm.setStyleSheet("") # Back to primary
            
    def confirm_receipt(self):
        if self.radio_no.isChecked():
            # Rechazar
            if self.db.update_purchase_order_status(self.order_id, "Rechazada / Devuelta"):
                QMessageBox.information(self, "Orden Rechazada", "La orden fue marcada como devuelta. El inventario NO se afectó.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar la orden.")
            return

        # Confirmar Recepción (Sí)
        payload = []
        for item in self.received_data:
            payload.append({
                'detail_id': item['detail_id'],
                'product_id': item['product_id'],
                'actual_unit_cost': item['actual_unit_cost'],
                'received_qty': int(item['spin_qty'].value()),
                'condition': 'Buenas Condiciones'
            })
            
        # Opcionalmente se puede solicitar metodo de pago o asumir Efectivo / mantener Pendiente (CP)
        # Asumimos que como fue en linea y validada, se registra a cuentas por pagar si fue credito
        try:
            if self.db.update_purchase_order_status(self.order_id, "Recibida", payload, payment_method="Efectivo", is_paid=False):
                QMessageBox.information(self, "Éxito", "Mercancía recibida. Inventario actualizado y lote histórico generado.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo procesar la recepción.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar la recepción: {e}")
            
    def show_order_details(self):
        order_num = f"#{self.order_id}"
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT order_number FROM purchase_orders WHERE id = ?", (self.order_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    order_num = row[0]
        except Exception:
            pass
        dialog = PurchaseOrderDetailDialog(self.db, self.order_id, order_num, self)
        dialog.exec()
            
class PurchaseOrderDetailDialog(QDialog):
    def __init__(self, db, order_id, order_num, parent=None):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self.order_num = order_num
        self.setWindowTitle(f"Detalles de Orden {order_num}")
        self.resize(950, 520)
        self.setMinimumWidth(750)
        self.setMinimumHeight(400)
        self.setStyleSheet(ui.STYLE_SHEET)
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.lbl_info = ui.QLabel("")
        self.lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.lbl_info)
        
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Producto", "Cant. Pedida", "Cant. Recibida", "Costo Real Unit.", "Subtotal", "Combo"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 105)
        self.table.setColumnWidth(3, 115)
        self.table.setColumnWidth(4, 95)
        self.table.setColumnWidth(5, 85)
        
        layout.addWidget(self.table)
        
        btn_close = ui.PrimaryButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)
        
    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT subtotal, tax, shipping, total, status, origin_state FROM purchase_orders WHERE id = ?", (self.order_id,))
                row = cursor.fetchone()
                if row:
                    sub, tax, ship, total, status, origin = row
                    info_text = f"Subtotal: ${sub:.2f} | Impuesto: ${tax:.2f} | Envío: ${ship:.2f} | Total: ${total:.2f}\nEstado: {status} | Estado de origen: {origin if origin else 'N/A'}"
                    self.lbl_info.setText(info_text)
                    
            details = self.db.get_purchase_order_details(self.order_id)
            self.table.setRowCount(0)
            for d in details:
                # d format from db.py: id(0), product_id(1), name(2), sku(3), ordered_quantity(4), received_quantity(5), original_cost(6), actual_cost(7), combo_ref(8), combo_name(9)
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                sku_name = f"{d[3]} - {d[2]}"
                ord_qty = d[4]
                rec_qty = d[5]
                actual_cost = d[7]
                combo_name = d[9] if len(d) > 9 and d[9] else "-"
                subtotal = ord_qty * actual_cost
                
                item_prod = QTableWidgetItem(sku_name)
                item_prod.setToolTip(sku_name)
                
                item_ord = QTableWidgetItem(str(ord_qty))
                item_ord.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                item_rec = QTableWidgetItem(str(rec_qty))
                item_rec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                item_cost = QTableWidgetItem(f"${actual_cost:.2f}")
                item_cost.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                item_sub = QTableWidgetItem(f"${subtotal:.2f}")
                item_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                item_combo = QTableWidgetItem(combo_name)
                item_combo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if combo_name != "-":
                    item_combo.setToolTip(combo_name)
                
                self.table.setItem(r, 0, item_prod)
                self.table.setItem(r, 1, item_ord)
                self.table.setItem(r, 2, item_rec)
                self.table.setItem(r, 3, item_cost)
                self.table.setItem(r, 4, item_sub)
                self.table.setItem(r, 5, item_combo)
                
        except Exception as e:
            self.lbl_info.setText("Error al cargar detalles.")
            print(f"Error loading details: {e}")
