import sys
import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. load_inventory_data signature
content = content.replace(
    '''            p_id, img_path, sku, name, category, stock, cost, price, min_stock, tax_pct = row_data''',
    '''            p_id, img_path, sku, name, category, stock, cost, price, min_stock, tax_pct, incoming_stock, next_delivery = row_data'''
)

# 2. load_inventory_data stock visual
content = content.replace(
    '''            # 2. Datos de texto con formato
            # SKU, Producto, Categoría, Stock, Costo, Venta
            display_data = [
                (str(sku), Qt.AlignmentFlag.AlignCenter),
                (str(name), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (str(category), Qt.AlignmentFlag.AlignCenter),
                (str(stock), Qt.AlignmentFlag.AlignCenter),''',
    '''            # 2. Datos de texto con formato
            stock_text = str(stock)
            if incoming_stock and incoming_stock > 0:
                short_date = str(next_delivery)[:10] if next_delivery else "Pronto"
                stock_text += f"\\n(+{incoming_stock} para {short_date})"

            # SKU, Producto, Categoría, Stock, Costo, Venta
            display_data = [
                (str(sku), Qt.AlignmentFlag.AlignCenter),
                (str(name), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (str(category), Qt.AlignmentFlag.AlignCenter),
                (stock_text, Qt.AlignmentFlag.AlignCenter),'''
)

# 3. create_inventory button
content = content.replace(
    '''        btn_add = ui.PrimaryButton("+ Nuevo Producto")
        btn_add.clicked.connect(self.open_new_product_dialog)
        
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(search)
        top_layout.addWidget(btn_add)''',
    '''        btn_add = ui.PrimaryButton("+ Nuevo Producto")
        btn_add.clicked.connect(self.open_new_product_dialog)
        
        btn_pending = ui.PrimaryButton("📦 Pedidos Pendientes")
        btn_pending.setObjectName("Secondary")
        btn_pending.clicked.connect(self.open_pending_orders)
        
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(search)
        top_layout.addWidget(btn_pending)
        top_layout.addWidget(btn_add)'''
)

# 4. create_purchases UI fields
content = content.replace(
    '''        self.compra_origin_state = QComboBox()
        self.compra_origin_state.addItems(US_STATES)
        self.compra_origin_state.setCurrentText("TX") # Default
        self.compra_origin_state.setMinimumHeight(40)

        self.compra_selling_price = ui.QLineEdit()''',
    '''        self.compra_origin_state = QComboBox()
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

        self.compra_selling_price = ui.QLineEdit()'''
)

# 5. create_purchases UI layout
content = content.replace(
    '''        prod_form.addRow("Impuesto (%):", self.compra_tax)
        prod_form.addRow("Ganancia (%):", self.compra_profit_pct)
        prod_form.addRow("Estado Origen:", self.compra_origin_state)

        # Precio Sugerido y Botón Aplicar''',
    '''        prod_form.addRow("Impuesto (%):", self.compra_tax)
        prod_form.addRow("Ganancia (%):", self.compra_profit_pct)
        prod_form.addRow("Estado Origen:", self.compra_origin_state)
        prod_form.addRow("Tipo de Compra:", self.compra_type)
        prod_form.addRow("Estimado de Entrega:", self.compra_delivery_date)

        # Precio Sugerido y Botón Aplicar'''
)

# 6. register_purchase logic
content = content.replace(
    '''            origin_state = self.compra_origin_state.currentText()
            tax_pct = float(self.compra_tax.text()) if self.compra_tax.text() else 0.0
            new_price = float(self.compra_selling_price.text()) if self.compra_selling_price.text() else None
            
            if self.db.add_purchase(p_id, qty, cost, supplier_idx, method, responsible, 
                                   is_return=is_ret, card_name=card, is_paid=status, 
                                   due_date=due, origin_state=origin_state, 
                                   tax_percentage=tax_pct, new_selling_price=new_price):''',
    '''            origin_state = self.compra_origin_state.currentText()
            tax_pct = float(self.compra_tax.text()) if self.compra_tax.text() else 0.0
            new_price = float(self.compra_selling_price.text()) if self.compra_selling_price.text() else None
            
            p_type = self.compra_type.currentText()
            d_date = self.compra_delivery_date.date().toString("yyyy-MM-dd") if p_type == "En Línea" else None
            d_status = "Pendiente" if p_type == "En Línea" else "Entregado"
            
            if self.db.add_purchase(p_id, qty, cost, supplier_idx, method, responsible, 
                                   is_return=is_ret, card_name=card, is_paid=status, 
                                   due_date=due, origin_state=origin_state, 
                                   tax_percentage=tax_pct, new_selling_price=new_price,
                                   purchase_type=p_type, delivery_date=d_date, delivery_status=d_status):'''
)

# Add clear fields
content = content.replace(
    '''                self.compra_profit_pct.setText("0")
                self.compra_selling_price.clear()''',
    '''                self.compra_profit_pct.setText("0")
                self.compra_selling_price.clear()
                self.compra_type.setCurrentIndex(0)'''
)

# 7. Add PendingOrdersDialog and open_pending_orders
new_code = '''
    def open_pending_orders(self):
        dialog = PendingOrdersDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_inventory_data()
            self.update_dashboard_data()

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
'''
content = content.replace("if __name__ == \"__main__\":\n", new_code)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("main.py updated")
