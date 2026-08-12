import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update menu list
content = content.replace(
    '''        menu_items = ["Dashboard", "Inventario", "POS", "Compras", "Caja", "Reportes", "Configuración"]''',
    '''        menu_items = ["Dashboard", "Inventario", "POS", "Compras", "Caja", "Reportes", "Configuración", "Clientes"]'''
)

# 2. Add stack widget
content = content.replace(
    '''        self.stack.addWidget(self.create_config())''',
    '''        self.stack.addWidget(self.create_config())\n        self.stack.addWidget(self.create_customers())'''
)

# 3. Handle index routing in display_page
content = content.replace(
    '''        elif index == 1: # Inventario
            self.load_inventory_data()''',
    '''        elif index == 1: # Inventario
            self.load_inventory_data()
        elif index == 7: # Clientes
            self.load_customers_table()'''
)

# 4. Modify create_pos to include customer & discount
old_pos = '''        right_layout.addSpacing(40)
        
        btn_pay = ui.PrimaryButton("COBRAR (F5)")'''
new_pos = '''        right_layout.addSpacing(20)
        
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
        
        btn_pay = ui.PrimaryButton("COBRAR (F5)")'''
content = content.replace(old_pos, new_pos)

# 5. Populate customers when POS is opened or initially
content = content.replace(
    '''        self.update_global_caja_status()''',
    '''        self.update_global_caja_status()\n        self.load_pos_customers()'''
)

# 6. cart total logic to include discount (in update_cart_table)
old_cart_total = '''        self.total_val.setText(f"$ {total:,.2f}")'''
new_cart_total = '''        discount = 0.0
        try:
            if self.pos_discount.text().strip():
                discount = float(self.pos_discount.text())
        except ValueError:
            pass
        final_total = max(0, total - discount)
        self.total_val.setText(f"$ {final_total:,.2f}")'''
content = content.replace(old_cart_total, new_cart_total)

# 7. Modify process_sale logic
old_process_sale = '''        caja_id = open_caja[0]
        total = sum(item[3] * item[4] for item in self.cart_items)
        
        # 2. Diálogo de Pago
        payment_dialog = PaymentDialog(total, self)
        if payment_dialog.exec():
            payment_method = payment_dialog.get_data()
            
            # items para la BD: (id, qty, price)
            db_items = [(item[0], item[3], item[4]) for item in self.cart_items]
            
            ticket = self.db.add_sale(total, payment_method, db_items, caja_id=caja_id)'''

new_process_sale = '''        caja_id = open_caja[0]
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
            ticket = self.db.add_sale(total, payment_method, db_items, caja_id=caja_id, customer_id=customer_id, discount=discount)'''
content = content.replace(old_process_sale, new_process_sale)

# And clear the pos discount when sale clears
old_clear = '''        self.barcode_input.clear()'''
new_clear = '''        self.barcode_input.clear()
        self.pos_discount.clear()
        self.pos_customer.setCurrentIndex(0)'''
content = content.replace(old_clear, new_clear)


# 8. Add all new Customer Methods in MainWindow and the NewCustomerDialog
new_classes = '''
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
        msg_text = f"Historial de: {name}\\n\\n"
        if not history:
            msg_text += "No hay compras registradas.\\n"
        else:
            for d, t_num, t_amount, d_app in history:
                msg_text += f"{d} | {t_num} | Total: ${t_amount:,.2f} | Descuento: ${d_app:,.2f}\\n"
                
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
'''

content = content.replace("class CajaMovementDialog(QDialog):\n", new_classes)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("main.py UI updated for customers")
