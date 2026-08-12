from PyQt6.QtWidgets import QPushButton, QFrame, QLabel, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal

# Paleta "Slate & Steel"
STYLE_SHEET = """
QMainWindow {
    background-color: #1E293B;
}

QWidget {
    background-color: #1E293B;
    color: #F8FAFC;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}

QFrame#Card {
    background-color: #334155;
    border-radius: 8px;
    border: 1px solid #475569;
}

QFrame#Card:hover {
    background-color: #3D4D63;
    border: 1px solid #0EA5E9;
}

QLabel#Secondary {
    color: #94A3B8;
}

QLabel#Title {
    font-size: 18pt;
    font-weight: bold;
    color: #F8FAFC;
}

QLineEdit {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 8px;
    color: #F8FAFC;
}

QLineEdit:focus {
    border: 1px solid #0EA5E9;
}

QPushButton {
    background-color: #0EA5E9;
    color: white;
    border-radius: 4px;
    padding: 10px 20px;
    font-weight: bold;
    border: none;
}

QPushButton:hover {
    background-color: #0284C7;
}

QPushButton:pressed {
    background-color: #0369A1;
}

QPushButton#Secondary {
    background-color: #475569;
}

QPushButton#Secondary:hover {
    background-color: #64748B;
}

QPushButton#Alert {
    background-color: #F59E0B;
}

QPushButton#Alert:hover {
    background-color: #D97706;
}

QPushButton#TableAction {
    background-color: #475569;
    padding: 4px 8px;
    font-weight: normal;
    font-size: 9pt;
}

QPushButton#TableAction:hover {
    background-color: #64748B;
}

QTableWidget {
    background-color: #1E293B;
    gridline-color: #334155;
    border: none;
    selection-background-color: #334155;
    selection-color: #0EA5E9;
    outline: none;
}

QTableWidget::item:selected {
    background-color: #334155;
    color: #0EA5E9;
    font-weight: bold;
}

QHeaderView::section {
    background-color: #334155;
    color: #94A3B8;
    padding: 5px;
    border: 1px solid #1E293B;
}

QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #1E293B;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1E293B;
    color: #0EA5E9;
    border-bottom: 2px solid #0EA5E9;
    font-weight: bold;
}

QTabBar::tab:hover {
    color: #F8FAFC;
}
"""

class Card(QFrame):
    """Contenedor estilizado tipo tarjeta con soporte de clic."""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class PrimaryButton(QPushButton):
    """Botón con el acento primario (Azul cielo)."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

class AlertButton(QPushButton):
    """Botón para acciones de alerta o stock bajo (Ámbar)."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("Alert")

class SearchField(QLineEdit):
    """Campo de búsqueda estilizado."""
    def __init__(self, placeholder="Buscar...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)

class TableActionButton(QPushButton):
    """Botón pequeño para acciones dentro de celdas de tabla."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("TableAction")
