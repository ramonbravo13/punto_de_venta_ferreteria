import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add mode selector
header_old = '''        self.quick_mode = QCheckBox("Modo Entrada Rápida (Escáner)")
        self.quick_mode.setStyleSheet("color: #0EA5E9; font-weight: bold; font-size: 11pt;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.quick_mode)'''

header_new = '''        self.compra_mode = QComboBox()
        self.compra_mode.addItems(["Individual", "Combo (Paquete)"])
        self.compra_mode.setMinimumHeight(35)
        
        self.quick_mode = QCheckBox("Modo Entrada Rápida (Escáner)")
        self.quick_mode.setStyleSheet("color: #0EA5E9; font-weight: bold; font-size: 11pt;")
        
        header_layout.addWidget(title)
        header_layout.addSpacing(20)
        header_layout.addWidget(self.compra_mode)
        header_layout.addStretch()
        header_layout.addWidget(self.quick_mode)'''
content = content.replace(header_old, header_new)

# 2. Add Stack Widget
form_old = '''        # --- Formulario en Dos Columnas ---
        columns_layout = QHBoxLayout()'''
form_new = '''        # --- Stack para Modos ---
        self.compra_stack = QStackedWidget()
        layout.addWidget(self.compra_stack)
        
        self.individual_mode_widget = QWidget()
        self.individual_mode_layout = QVBoxLayout(self.individual_mode_widget)
        self.individual_mode_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Formulario INDIVIDUAL en Dos Columnas ---
        columns_layout = QHBoxLayout()'''
content = content.replace(form_old, form_new)

# 3. Fix layouts adding to individual instead of main layout
layout_add_old = '''        columns_layout.addWidget(right_column)
        
        layout.addLayout(columns_layout)
        
        # --- Botón de Acción ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = ui.PrimaryButton("🚀 REGISTRAR COMPRA")
        btn_save.setFixedWidth(300)
        btn_save.setFixedHeight(50)
        btn_save.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #0EA5E9;")
        btn_save.clicked.connect(self.register_purchase)
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addStretch(1)'''

layout_add_new = '''        columns_layout.addWidget(right_column)
        
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
        )'''
content = content.replace(layout_add_old, layout_add_new)

# 4. Define combo methods
new_methods = '''
    def init_combo_ui(self):
        self.combo_mode_widget = QWidget()
        layout = QVBoxLayout(self.combo_mode_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        card = ui.Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        title = ui.QLabel("📋 Detalles del Combo Parcial")
        title.setStyleSheet("font-weight: bold; color: #0EA5E9; font-size: 12pt; margin-bottom: 10px;")
        card_layout.addWidget(title)
        
        form1 = QHBoxLayout()
        form1.addWidget(ui.QLabel("Nombre Combo:"))
        self.combo_name = ui.QLineEdit()
        form1.addWidget(self.combo_name)
        
        form1.addWidget(ui.QLabel("Costo Total Paquete ($):"))
        self.combo_total_cost = ui.QLineEdit()
        self.combo_total_cost.setPlaceholderText("0.00")
        self.combo_total_cost.textChanged.connect(self.update_combo_table_calculations)
        form1.addWidget(self.combo_total_cost)
        
        form1.addWidget(ui.QLabel("Distribución:"))
        self.combo_method = QComboBox()
        self.combo_method.addItems(["Equitativa", "Manual (%)"])
        self.combo_method.currentTextChanged.connect(self.on_combo_method_change)
        form1.addWidget(self.combo_method)
        
        card_layout.addLayout(form1)
        
        # Second row forms (Supplier etc)
        form2 = QHBoxLayout()
        
        form2.addWidget(ui.QLabel("Proveedor:"))
        self.combo_supplier = QComboBox()
        form2.addWidget(self.combo_supplier)
        
        form2.addWidget(ui.QLabel("Resp.:"))
        self.combo_responsible = QComboBox()
        self.combo_responsible.addItems(["David", "Stacey", "Dueño", "Encargado"])
        form2.addWidget(self.combo_responsible)
        
        form2.addWidget(ui.QLabel("Pago:"))
        self.combo_payment_mode = QComboBox()
        self.combo_payment_mode.addItems(["Efectivo", "Tarjeta de Crédito"])
        form2.addWidget(self.combo_payment_mode)
        
        form2.addWidget(ui.QLabel("Tipo:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Física", "En Línea"])
        form2.addWidget(self.combo_type)
        
        card_layout.addLayout(form2)
        layout.addWidget(card)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(ui.QLabel("Agregar Producto:"))
        self.combo_product_search = ui.QLineEdit()
        self.combo_product_search.setPlaceholderText("Escanee el código o nombre y presione Enter...")
        self.combo_product_search.returnPressed.connect(self.add_product_to_combo)
        search_layout.addWidget(self.combo_product_search)
        layout.addLayout(search_layout)
        
        self.combo_table = QTableWidget(0, 6)
        self.combo_table.setHorizontalHeaderLabels(["ID", "SKU", "Producto", "Cantidad", "Peso (%)", "Costo Unidad Calc."])
        self.combo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.combo_table.verticalHeader().setDefaultSectionSize(40)
        self.combo_table.itemChanged.connect(self.on_combo_table_item_changed)
        layout.addWidget(self.combo_table)
        
        self.combo_items = [] # (p_id, sku, name)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = ui.PrimaryButton("🚀 REGISTRAR COMBO")
        btn_save.setFixedWidth(300)
        btn_save.setFixedHeight(50)
        btn_save.clicked.connect(self.register_combo_purchase)
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

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
            QMessageBox.warning(self, "Error", "Producto no encontrado.")
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
        if rows == 0: return
        
        sum_qty = 0
        sum_pct = 0.0
        
        for r in range(rows):
            try: sum_qty += int(self.combo_table.item(r, 3).text())
            except: pass
            if method == "Manual (%)":
                try: sum_pct += float(self.combo_table.item(r, 4).text())
                except: pass
        
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
            else:
                self.combo_table.item(r, 4).setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable) # Unlock %
                try: pct = float(self.combo_table.item(r, 4).text())
                except: pct = 0.0
                
                if qty > 0:
                    cost = (total_cost * (pct / 100.0)) / qty
                
                # Check sum_pct
                if sum_pct != 100.0:
                    self.combo_table.item(r, 4).setBackground(QBrush(QColor("#7f1d1d"))) # red hint
                    
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

'''

content = content.replace("    def update_compra_totals(self):", new_methods + "\n    def update_compra_totals(self):")

# Fill suppliers in both comboboxes within refresh_purchase_selectors
old_refresh = '''        for s in suppliers:
            self.compra_supplier.addItem(s[1], s[0])'''
new_refresh = '''        self.combo_supplier.clear()
        for s in suppliers:
            self.compra_supplier.addItem(s[1], s[0])
            self.combo_supplier.addItem(s[1], s[0])'''
content = content.replace(old_refresh, new_refresh)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("main.py updated for combos")
