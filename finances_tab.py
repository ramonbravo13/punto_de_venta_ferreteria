from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox, 
                             QCheckBox, QMessageBox, QTabWidget, QDateEdit, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
import ui_components as ui
from datetime import datetime

class NewExpenseDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Registrar Nuevo Gasto")
        self.setFixedSize(400, 350)
        self.setStyleSheet("background-color: #1E293B; color: #F8FAFC;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Luz", "Renta", "Nómina", "Insumos", "Mantenimiento", "Otros"])
        self.cat_combo.setEditable(True)
        form_layout.addRow("Categoría:", self.cat_combo)
        
        self.desc_input = QLineEdit()
        form_layout.addRow("Descripción:", self.desc_input)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 9999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("$ ")
        form_layout.addRow("Monto Total:", self.amount_input)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Efectivo", "Tarjeta de Débito/Crédito", "Transferencia"])
        form_layout.addRow("Método de Pago:", self.method_combo)
        
        self.tax_check = QCheckBox("Incluye IVA (Deducible)")
        form_layout.addRow("", self.tax_check)
        
        self.deduct_caja_check = QCheckBox("Descontar de Caja Actual")
        self.deduct_caja_check.setChecked(True)
        form_layout.addRow("", self.deduct_caja_check)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_save = ui.PrimaryButton("Registrar Gasto")
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self.save_expense)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def save_expense(self):
        amount = self.amount_input.value()
        if amount <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a 0")
            return
            
        category = self.cat_combo.currentText()
        desc = self.desc_input.text()
        method = self.method_combo.currentText()
        tax_inc = self.tax_check.isChecked()
        deduct_caja = self.deduct_caja_check.isChecked()
        
        expense_id = self.db.add_expense(category, desc, amount, method, tax_inc, True)
        if expense_id:
            if deduct_caja and method == "Efectivo":
                open_caja = self.db.get_open_caja()
                if open_caja:
                    caja_id = open_caja[0]
                    self.db.add_caja_movement(caja_id, "retiro", amount, f"Gasto: {category} - {desc}")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el gasto en la BD.")

class NewDebtDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Registrar Cuenta por Pagar")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #1E293B; color: #F8FAFC;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.prov_input = QLineEdit()
        form_layout.addRow("Proveedor/Servicio:", self.prov_input)
        
        self.desc_input = QLineEdit()
        form_layout.addRow("Descripción:", self.desc_input)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 9999999)
        self.amount_input.setPrefix("$ ")
        form_layout.addRow("Monto Total:", self.amount_input)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate().addDays(30))
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Fecha Límite:", self.date_input)
        
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Efectivo", "Tarjeta de Débito/Crédito", "Transferencia"])
        form_layout.addRow("Medio de Pago:", self.payment_method)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_save = ui.PrimaryButton("Registrar")
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self.save_debt)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
    def save_debt(self):
        if self.amount_input.value() <= 0 or not self.prov_input.text():
            QMessageBox.warning(self, "Error", "Datos incompletos")
            return
        due_date = self.date_input.date().toString("yyyy-MM-dd")
        pm = self.payment_method.currentText()
        if self.db.add_account_payable(self.prov_input.text(), self.desc_input.text(), self.amount_input.value(), due_date, pm):
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Fallo al guardar.")

class PayDebtDialog(QDialog):
    def __init__(self, db, account_id, remaining, parent=None):
        super().__init__(parent)
        self.db = db
        self.account_id = account_id
        self.remaining = remaining
        self.setWindowTitle("Marcar como Pagado")
        self.setFixedSize(300, 180)
        self.setStyleSheet("background-color: #1E293B; color: #F8FAFC;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.lbl = QLabel(f"¿Confirmas el pago total de ${self.remaining:,.2f}?")
        self.lbl.setWordWrap(True)
        layout.addWidget(self.lbl)
        
        layout.addWidget(QLabel("Medio de Pago utilizado:"))
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Efectivo", "Tarjeta de Débito/Crédito", "Transferencia"])
        layout.addWidget(self.payment_method)
        
        btn_layout = QHBoxLayout()
        btn_save = ui.PrimaryButton("Confirmar Pago")
        btn_save.clicked.connect(self.process_payment)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
    def process_payment(self):
        amount = self.remaining
        pm = self.payment_method.currentText()
        if self.db.add_payment_to_account(self.account_id, amount):
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el abono.")

class PurchaseDetailDialog(QDialog):
    def __init__(self, db, order_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self.setWindowTitle(f"Detalle de Orden #{order_id}")
        self.resize(800, 500)
        self.setStyleSheet("background-color: #1E293B; color: #F8FAFC;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        order = self.db.get_purchase_order_by_id(self.order_id)
        if not order:
            layout.addWidget(QLabel("No se encontró información detallada de esta orden."))
            btn_close = ui.PrimaryButton("Cerrar")
            btn_close.clicked.connect(self.accept)
            layout.addWidget(btn_close)
            return
            
        header_layout = QFormLayout()
        header_layout.addRow("ID Interno:", QLabel(str(order[0])))
        header_layout.addRow("Número de Orden:", QLabel(str(order[1])))
        header_layout.addRow("Fecha:", QLabel(str(order[2])))
        header_layout.addRow("Proveedor:", QLabel(str(order[3])))
        header_layout.addRow("Tipo de Compra:", QLabel(str(order[4])))
        header_layout.addRow("Total Compra:", QLabel(f"${order[6]:,.2f}"))
        
        layout.addLayout(header_layout)
        
        layout.addWidget(QLabel("Productos Incluidos:"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["SKU", "Producto", "Combo/Paquete", "Cantidad", "Costo U.", "Importe", "Costo Real (c/Impuestos)"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("QTableWidget { background-color: #0F172A; color: #F8FAFC; border: none; }")
        
        header_p = self.table.horizontalHeader()
        header_p.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header_p.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(2, 105)
        self.table.setColumnWidth(3, 75)
        self.table.setColumnWidth(4, 85)
        self.table.setColumnWidth(5, 85)
        self.table.setColumnWidth(6, 150)
        
        details = self.db.get_purchase_order_details(self.order_id)
        self.table.setRowCount(0)
        
        for d in details:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            sku = str(d[3]) if d[3] else ""
            name = str(d[2])
            combo_name = str(d[9]) if d[9] else "N/A"
            qty = d[4]
            u_cost = d[6]
            actual_u_cost = d[7]
            importe = qty * u_cost
            
            item_sku = QTableWidgetItem(sku)
            item_sku.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_sku)
            
            item_name = QTableWidgetItem(name)
            item_name.setToolTip(name)
            self.table.setItem(row, 1, item_name)
            
            item_combo = QTableWidgetItem(combo_name)
            item_combo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_combo)
            
            item_qty = QTableWidgetItem(str(qty))
            item_qty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, item_qty)
            
            item_uc = QTableWidgetItem(f"${u_cost:,.2f}")
            item_uc.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, item_uc)
            
            item_imp = QTableWidgetItem(f"${importe:,.2f}")
            item_imp.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, item_imp)
            
            item_act = QTableWidgetItem(f"${actual_u_cost:,.2f}")
            item_act.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 6, item_act)
            
        layout.addWidget(self.table)
        
        btn_close = ui.PrimaryButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class FinancesTab(QWidget):
    def __init__(self, db, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window # Reference to update dashboard if needed
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Finanzas y Gastos Operativos")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #F8FAFC;")
        header_layout.addWidget(title)
        
        btn_new_expense = ui.PrimaryButton("+ Nuevo Gasto")
        btn_new_expense.clicked.connect(self.open_new_expense)
        header_layout.addWidget(btn_new_expense)
        
        main_layout.addLayout(header_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; border-radius: 4px; background: #1E293B; }
            QTabBar::tab { background: #0F172A; color: #94A3B8; padding: 10px 20px; border: 1px solid #334155; }
            QTabBar::tab:selected { background: #334155; color: #0EA5E9; font-weight: bold; }
        """)
        
        # Pestaña 1: Historial de Gastos
        self.tab_expenses = QWidget()
        self.setup_expenses_tab()
        self.tabs.addTab(self.tab_expenses, "Historial de Gastos")
        
        # Pestaña 2: Cuentas por Pagar
        self.tab_debts = QWidget()
        self.setup_debts_tab()
        self.tabs.addTab(self.tab_debts, "Cuentas por Pagar")
        
        # Pestaña 3: Resumen Tarjetas
        self.tab_cards = QWidget()
        self.setup_cards_tab()
        self.tabs.addTab(self.tab_cards, "Resumen Tarjetas")
        
        # Pestaña 4: Valorización de Inventario
        self.tab_inventory_val = QWidget()
        self.setup_inventory_val_tab()
        self.tabs.addTab(self.tab_inventory_val, "Valorización de Inventario")
        
        main_layout.addWidget(self.tabs)

    def setup_expenses_tab(self):
        layout = QVBoxLayout(self.tab_expenses)
        
        # Filtros
        filter_layout = QHBoxLayout()
        self.date_start = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_start.setCalendarPopup(True)
        self.date_end = QDateEdit(QDate.currentDate())
        self.date_end.setCalendarPopup(True)
        btn_filter = QPushButton("Filtrar")
        btn_filter.clicked.connect(self.load_expenses)
        
        filter_layout.addWidget(QLabel("Desde:"))
        filter_layout.addWidget(self.date_start)
        filter_layout.addWidget(QLabel("Hasta:"))
        filter_layout.addWidget(self.date_end)
        filter_layout.addWidget(btn_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tabla
        self.exp_table = QTableWidget()
        self.exp_table.setColumnCount(11)
        self.exp_table.setHorizontalHeaderLabels(["ID / Ref", "Fecha", "Prov. / Cat.", "Concepto", "Importe", "Impuestos", "Tarjeta/Método", "Dígitos", "Estado", "Fecha Pago", "Acciones"])
        self.exp_table.setAlternatingRowColors(True)
        self.exp_table.verticalHeader().setDefaultSectionSize(38)
        self.exp_table.verticalHeader().setVisible(False)
        self.exp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.exp_table.setStyleSheet("QTableWidget { background-color: #0F172A; color: #F8FAFC; border: none; }")
        
        header = self.exp_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.exp_table.setColumnWidth(0, 75)   # ID / Ref
        self.exp_table.setColumnWidth(1, 90)   # Fecha
        self.exp_table.setColumnWidth(2, 130)  # Prov. / Cat.
        # Columna 3 (Concepto) es Stretch -> toma todo el espacio sobrante
        self.exp_table.setColumnWidth(4, 95)   # Importe
        self.exp_table.setColumnWidth(5, 85)   # Impuestos
        self.exp_table.setColumnWidth(6, 115)  # Tarjeta/Método
        self.exp_table.setColumnWidth(7, 65)   # Dígitos
        self.exp_table.setColumnWidth(8, 85)   # Estado
        self.exp_table.setColumnWidth(9, 90)   # Fecha Pago
        self.exp_table.setColumnWidth(10, 85)  # Acciones
        
        layout.addWidget(self.exp_table)
        
        self.lbl_total_exp = QLabel("Total Gastos: $0.00")
        self.lbl_total_exp.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444;")
        layout.addWidget(self.lbl_total_exp)
        
    def setup_debts_tab(self):
        layout = QVBoxLayout(self.tab_debts)
        
        header = QHBoxLayout()
        btn_new_debt = QPushButton("+ Nueva Cuenta por Pagar")
        btn_new_debt.clicked.connect(self.open_new_debt)
        header.addWidget(btn_new_debt)
        header.addStretch()
        layout.addLayout(header)
        
        self.debt_table = QTableWidget()
        self.debt_table.setColumnCount(12)
        self.debt_table.setHorizontalHeaderLabels(["Proveedor", "Concepto", "Medio Pago", "Tarjeta", "Tipo", "Subtotal", "Costo Envío", "Total", "Pagado", "Restante", "Vencimiento", "Acción"])
        self.debt_table.setAlternatingRowColors(True)
        self.debt_table.verticalHeader().setDefaultSectionSize(38)
        self.debt_table.verticalHeader().setVisible(False)
        self.debt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.debt_table.setStyleSheet("QTableWidget { background-color: #0F172A; color: #F8FAFC; border: none; }")
        
        header_d = self.debt_table.horizontalHeader()
        header_d.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header_d.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.debt_table.setColumnWidth(0, 120)  # Proveedor
        # Columna 1 (Concepto) es Stretch
        self.debt_table.setColumnWidth(2, 95)   # Medio Pago
        self.debt_table.setColumnWidth(3, 90)   # Tarjeta
        self.debt_table.setColumnWidth(4, 75)   # Tipo
        self.debt_table.setColumnWidth(5, 85)   # Subtotal
        self.debt_table.setColumnWidth(6, 85)   # Costo Envío
        self.debt_table.setColumnWidth(7, 85)   # Total
        self.debt_table.setColumnWidth(8, 85)   # Pagado
        self.debt_table.setColumnWidth(9, 85)   # Restante
        self.debt_table.setColumnWidth(10, 85)  # Vencimiento
        self.debt_table.setColumnWidth(11, 130) # Acción
        
        layout.addWidget(self.debt_table)

    def load_data(self):
        self.load_expenses()
        self.load_debts()
        self.load_cards_summary()
        self.load_inventory_valuation()

    def load_expenses(self):
        s_date = self.date_start.date().toString("yyyy-MM-dd")
        e_date = self.date_end.date().toString("yyyy-MM-dd")
        expenses = self.db.get_unified_expenses_by_period(s_date, e_date)
        
        self.exp_table.setRowCount(0)
        total = 0.0
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import Qt
        
        for exp in expenses:
            row = self.exp_table.rowCount()
            self.exp_table.insertRow(row)
            
            exp_id, fecha, prov_cat, concepto, importe, impuestos, tarjeta, digitos, estado, fecha_pago = exp
            
            item_id = QTableWidgetItem(str(exp_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row, 0, item_id)
            
            item_fecha = QTableWidgetItem(str(fecha)[:10] if fecha else "")
            item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row, 1, item_fecha)
            
            item_prov = QTableWidgetItem(str(prov_cat))
            item_prov.setToolTip(str(prov_cat))
            self.exp_table.setItem(row, 2, item_prov)
            
            item_concepto = QTableWidgetItem(str(concepto))
            item_concepto.setToolTip(str(concepto))
            self.exp_table.setItem(row, 3, item_concepto)
            
            item_importe = QTableWidgetItem(f"${importe:,.2f}")
            item_importe.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.exp_table.setItem(row, 4, item_importe)
            
            item_impuestos = QTableWidgetItem(f"${impuestos:,.2f}")
            item_impuestos.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.exp_table.setItem(row, 5, item_impuestos)
            
            item_tarjeta = QTableWidgetItem(str(tarjeta))
            item_tarjeta.setToolTip(str(tarjeta))
            item_tarjeta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row, 6, item_tarjeta)
            
            item_digitos = QTableWidgetItem(str(digitos))
            item_digitos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row, 7, item_digitos)
            
            item_estado = QTableWidgetItem(str(estado))
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if estado == 'Pagado':
                item_estado.setForeground(QColor("#10B981"))
            else:
                item_estado.setForeground(QColor("#F59E0B"))
            self.exp_table.setItem(row, 8, item_estado)
            
            fecha_pago_str = str(fecha_pago)[:10] if (estado == 'Pagado' and fecha_pago) else "N/A"
            item_pago = QTableWidgetItem(fecha_pago_str)
            item_pago.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row, 9, item_pago)
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)
            
            if "Orden de Compra " in str(concepto):
                import re
                match = re.search(r'Orden de Compra (\d+)', str(concepto))
                if match:
                    order_id = int(match.group(1))
                    btn_detail = ui.PrimaryButton("Detalle")
                    btn_detail.setStyleSheet("background-color: #0284C7; color: white; padding: 3px 8px; font-size: 8pt;")
                    btn_detail.clicked.connect(lambda checked, oid=order_id: self.show_purchase_detail(oid))
                    action_layout.addWidget(btn_detail)
            
            self.exp_table.setCellWidget(row, 10, action_widget)
            
            total += importe
            
        self.lbl_total_exp.setText(f"Total Gastos Periodo: ${total:,.2f}")

    def load_debts(self):
        debts = self.db.get_accounts_payable("Pendiente")
        self.debt_table.setRowCount(0)
        for debt in debts:
            row = self.debt_table.rowCount()
            self.debt_table.insertRow(row)
            item_prov = QTableWidgetItem(debt[1])
            item_prov.setToolTip(debt[1])
            self.debt_table.setItem(row, 0, item_prov)
            
            item_concepto = QTableWidgetItem(debt[2])
            item_concepto.setToolTip(debt[2])
            self.debt_table.setItem(row, 1, item_concepto)
            
            pm = debt[7] if len(debt) > 7 and debt[7] else "N/A"
            item_pm = QTableWidgetItem(pm)
            item_pm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.debt_table.setItem(row, 2, item_pm)
            
            card = debt[8] if len(debt) > 8 and debt[8] else "N/A"
            item_card = QTableWidgetItem(card)
            item_card.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.debt_table.setItem(row, 3, item_card)
            
            ptype = debt[10] if len(debt) > 10 and debt[10] else "N/A"
            item_ptype = QTableWidgetItem(ptype)
            item_ptype.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.debt_table.setItem(row, 4, item_ptype)
            
            shipping = float(debt[9]) if len(debt) > 9 and debt[9] else 0.0
            subtotal = debt[3] - shipping
            
            item_sub = QTableWidgetItem(f"${subtotal:,.2f}")
            item_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.debt_table.setItem(row, 5, item_sub)
            
            item_ship = QTableWidgetItem(f"${shipping:,.2f}")
            item_ship.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.debt_table.setItem(row, 6, item_ship)
            
            item_tot = QTableWidgetItem(f"${debt[3]:,.2f}")
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.debt_table.setItem(row, 7, item_tot)
            
            item_pag = QTableWidgetItem(f"${debt[4]:,.2f}")
            item_pag.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.debt_table.setItem(row, 8, item_pag)
            
            remaining = debt[3] - debt[4]
            item_rem = QTableWidgetItem(f"${remaining:,.2f}")
            item_rem.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.debt_table.setItem(row, 9, item_rem)
            
            due_date_str = debt[5]
            due_item = QTableWidgetItem(due_date_str if due_date_str else "N/A")
            due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if due_date_str:
                from PyQt6.QtCore import QDate
                from PyQt6.QtGui import QColor
                due_qdate = QDate.fromString(due_date_str, "yyyy-MM-dd")
                if due_qdate.isValid():
                    days_to_due = QDate.currentDate().daysTo(due_qdate)
                    if days_to_due <= 5:
                        due_item.setForeground(QColor("#EF4444")) # Rojo
            self.debt_table.setItem(row, 10, due_item)
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(4)
            
            btn_pay = ui.PrimaryButton("Pagado")
            btn_pay.clicked.connect(lambda checked, d_id=debt[0], rem=remaining: self.pay_debt(d_id, rem))
            action_layout.addWidget(btn_pay)
            
            concepto = str(debt[2])
            if "Orden de Compra " in concepto:
                import re
                match = re.search(r'Orden de Compra (\d+)', concepto)
                if match:
                    order_id = int(match.group(1))
                    btn_detail = ui.PrimaryButton("Detalle")
                    btn_detail.clicked.connect(lambda checked, oid=order_id: self.show_purchase_detail(oid))
                    action_layout.addWidget(btn_detail)
            
            self.debt_table.setCellWidget(row, 11, action_widget)

    def open_new_expense(self):
        dlg = NewExpenseDialog(self.db, self)
        if dlg.exec():
            self.load_expenses()
            self.main_window.update_dashboard_data()

    def open_new_debt(self):
        dlg = NewDebtDialog(self.db, self)
        if dlg.exec():
            self.load_debts()

    def pay_debt(self, account_id, remaining):
        dlg = PayDebtDialog(self.db, account_id, remaining, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_debts()

    def setup_cards_tab(self):
        layout = QVBoxLayout(self.tab_cards)
        
        self.card_table = QTableWidget()
        self.card_table.setColumnCount(11)
        self.card_table.setHorizontalHeaderLabels(["Tarjeta", "Banco", "Term.", "Límite", "Corte", "Día Pago", "Total Gastado", "Deuda Pend.", "Ya Pagado", "Compras", "Acciones"])
        self.card_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.card_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)
        self.card_table.verticalHeader().setDefaultSectionSize(45)
        self.card_table.setStyleSheet("QTableWidget { background-color: #0F172A; color: #F8FAFC; border: none; }")
        layout.addWidget(self.card_table)

    def load_cards_summary(self):
        summaries = self.db.get_credit_card_summaries()
        self.card_table.setRowCount(0)
        from PyQt6.QtCore import QDate
        from PyQt6.QtGui import QColor
        import ui_components as ui
        
        for c_id, name, bank, last_digits, limit, cut_day, pay_day, total_gastado, total_pendiente, total_pagado, num_purchases in summaries:
            row = self.card_table.rowCount()
            self.card_table.insertRow(row)
            
            self.card_table.setItem(row, 0, QTableWidgetItem(name))
            self.card_table.setItem(row, 1, QTableWidgetItem(str(bank) if bank else ""))
            self.card_table.setItem(row, 2, QTableWidgetItem(str(last_digits) if last_digits else ""))
            self.card_table.setItem(row, 3, QTableWidgetItem(f"${limit:,.2f}" if limit else "$0.00"))
            self.card_table.setItem(row, 4, QTableWidgetItem(str(cut_day) if cut_day else "N/A"))
            self.card_table.setItem(row, 5, QTableWidgetItem(str(pay_day) if pay_day else "N/A"))
            
            self.card_table.setItem(row, 6, QTableWidgetItem(f"${total_gastado:,.2f}"))
            
            item_debt = QTableWidgetItem(f"${total_pendiente:,.2f}")
            if total_pendiente > 0:
                item_debt.setForeground(QColor("#EF4444"))
            self.card_table.setItem(row, 7, item_debt)
            
            item_pagado = QTableWidgetItem(f"${total_pagado:,.2f}")
            item_pagado.setForeground(QColor("#10B981"))
            self.card_table.setItem(row, 8, item_pagado)
            
            self.card_table.setItem(row, 9, QTableWidgetItem(str(num_purchases)))
            
            btn_history = ui.PrimaryButton("Ver Compras")
            btn_history.clicked.connect(lambda checked, cid=c_id, cname=name: self.open_card_history(cid, cname))
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(4)
            action_layout.addWidget(btn_history)
            
            self.card_table.setCellWidget(row, 10, action_widget)

    def open_card_history(self, card_id, card_name):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Historial de Compras - {card_name}")
        dlg.resize(1100, 500)
        layout = QVBoxLayout(dlg)
        
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["Fecha", "Proveedor", "Concepto", "Importe", "Estado", "Fecha Pago", "Acciones"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setDefaultSectionSize(45)
        layout.addWidget(table)
        
        purchases = self.db.get_card_purchases(card_id)
        table.setRowCount(0)
        for p in purchases:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(p[0])[:10] if p[0] else ""))
            table.setItem(row, 1, QTableWidgetItem(str(p[1])))
            
            concepto = str(p[2])
            table.setItem(row, 2, QTableWidgetItem(concepto))
            table.setItem(row, 3, QTableWidgetItem(f"${p[3]:,.2f}"))
            table.setItem(row, 4, QTableWidgetItem(str(p[4])))
            table.setItem(row, 5, QTableWidgetItem(str(p[5])[:10] if p[5] else "N/A"))
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(4)
            
            if "Orden de Compra " in concepto:
                import re
                match = re.search(r'Orden de Compra (\d+)', concepto)
                if match:
                    order_id = int(match.group(1))
                    btn_detail = ui.PrimaryButton("Detalle")
                    btn_detail.clicked.connect(lambda checked, oid=order_id: self.show_purchase_detail(oid))
                    action_layout.addWidget(btn_detail)
            
            table.setCellWidget(row, 6, action_widget)
            
        dlg.exec()
        
        # update dashboard debt summary
        self.main_window.update_dashboard_data()

    def show_purchase_detail(self, order_id):
        dlg = PurchaseDetailDialog(self.db, order_id, self)
        dlg.exec()

    def setup_inventory_val_tab(self):
        layout = QVBoxLayout(self.tab_inventory_val)
        
        info_label = ui.QLabel("Esta tabla muestra el valor exacto del inventario disponible, calculado en base al costo real de cada lote registrado al momento de la compra.")
        info_label.setStyleSheet("color: #94A3B8; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        self.val_table = QTableWidget(0, 7)
        self.val_table.setHorizontalHeaderLabels(["SKU", "Producto", "Lote (ID)", "Cant. Disp.", "Costo Real/U", "Valor Total Lote", "Recepción"])
        self.val_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.val_table)
        
        totals_layout = QHBoxLayout()
        self.lbl_total_inv = ui.QLabel("Valor Total de Inventario: $0.00")
        self.lbl_total_inv.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        totals_layout.addStretch()
        totals_layout.addWidget(self.lbl_total_inv)
        
        layout.addLayout(totals_layout)
        
        btn_refresh = ui.PrimaryButton("Actualizar Valores")
        btn_refresh.clicked.connect(self.load_inventory_valuation)
        layout.addWidget(btn_refresh, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Cargar datos iniciales
        self.load_inventory_valuation()

    def load_inventory_valuation(self):
        self.val_table.setRowCount(0)
        batches = self.db.get_inventory_valuation()
        
        total_valuation = 0.0
        
        for sku, name, b_id, qty, cost, val, date, cond in batches:
            row = self.val_table.rowCount()
            self.val_table.insertRow(row)
            
            self.val_table.setItem(row, 0, QTableWidgetItem(sku))
            self.val_table.setItem(row, 1, QTableWidgetItem(name))
            self.val_table.setItem(row, 2, QTableWidgetItem(str(b_id)))
            self.val_table.setItem(row, 3, QTableWidgetItem(str(qty)))
            self.val_table.setItem(row, 4, QTableWidgetItem(f"${cost:,.2f}"))
            
            item_val = QTableWidgetItem(f"${val:,.2f}")
            item_val.setForeground(QColor("#10B981"))
            self.val_table.setItem(row, 5, item_val)
            
            self.val_table.setItem(row, 6, QTableWidgetItem(date[:10] if date else ""))
            
            total_valuation += val
            
        self.lbl_total_inv.setText(f"Valor Total de Inventario: ${total_valuation:,.2f}")
