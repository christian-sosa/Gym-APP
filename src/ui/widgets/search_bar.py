"""
Widget de barra de búsqueda con múltiples filtros.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QComboBox,
    QPushButton, QLabel, QDateEdit
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QFont

from src.utils.enums import PlanType


class SearchBar(QWidget):
    """Barra de búsqueda con filtros para usuarios."""
    
    # Señal emitida cuando se realiza una búsqueda
    search_triggered = Signal(dict)  # Emite diccionario con filtros
    clear_triggered = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchContainer")
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Título
        title = QLabel("Gestión de Usuarios")
        title.setObjectName("titleLabel")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        main_layout.addWidget(title)
        
        # Fila de filtros
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)
        
        # Apellido (primero para consistencia con la tabla)
        self.txt_apellido = QLineEdit()
        self.txt_apellido.setPlaceholderText("Apellido")
        self.txt_apellido.setMinimumWidth(100)
        self.txt_apellido.returnPressed.connect(self._on_search)
        filters_layout.addWidget(self.txt_apellido)
        
        # Nombre
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre")
        self.txt_nombre.setMinimumWidth(100)
        self.txt_nombre.returnPressed.connect(self._on_search)
        filters_layout.addWidget(self.txt_nombre)
        
        # Email
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Email")
        self.txt_email.setMinimumWidth(120)
        self.txt_email.returnPressed.connect(self._on_search)
        filters_layout.addWidget(self.txt_email)
        
        # Celular
        self.txt_celular = QLineEdit()
        self.txt_celular.setPlaceholderText("Celular")
        self.txt_celular.setMinimumWidth(100)
        self.txt_celular.returnPressed.connect(self._on_search)
        filters_layout.addWidget(self.txt_celular)
        
        # Membresía (Plan)
        self.cmb_plan = QComboBox()
        self.cmb_plan.addItem("Membresía", None)
        for plan in PlanType:
            self.cmb_plan.addItem(plan.display_name, plan)
        self.cmb_plan.setMinimumWidth(100)
        filters_layout.addWidget(self.cmb_plan)
        
        # Observaciones
        self.txt_observaciones = QLineEdit()
        self.txt_observaciones.setPlaceholderText("Observaciones")
        self.txt_observaciones.setMinimumWidth(120)
        self.txt_observaciones.returnPressed.connect(self._on_search)
        filters_layout.addWidget(self.txt_observaciones)
        
        # Fecha de pago
        self.date_pago = QDateEdit()
        self.date_pago.setCalendarPopup(True)
        self.date_pago.setDate(QDate.currentDate())
        self.date_pago.setDisplayFormat("yyyy-MM-dd")
        self.date_pago.setSpecialValueText("Última Fecha de Pago")
        self.date_pago.setMinimumDate(QDate(2000, 1, 1))
        filters_layout.addWidget(self.date_pago)
        
        # Botón buscar
        self.btn_buscar = QPushButton("Buscar")
        self.btn_buscar.setMinimumWidth(80)
        self.btn_buscar.clicked.connect(self._on_search)
        filters_layout.addWidget(self.btn_buscar)
        
        # Botón limpiar
        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.setObjectName("secondaryButton")
        self.btn_limpiar.setMinimumWidth(80)
        self.btn_limpiar.clicked.connect(self._on_clear)
        filters_layout.addWidget(self.btn_limpiar)
        
        main_layout.addLayout(filters_layout)
    
    def _on_search(self):
        """Emite señal de búsqueda con los filtros actuales."""
        filters = self.get_filters()
        self.search_triggered.emit(filters)
    
    def _on_clear(self):
        """Limpia todos los filtros."""
        self.txt_nombre.clear()
        self.txt_apellido.clear()
        self.txt_email.clear()
        self.txt_celular.clear()
        self.cmb_plan.setCurrentIndex(0)
        self.txt_observaciones.clear()
        self.date_pago.setDate(QDate.currentDate())
        self.clear_triggered.emit()
    
    def get_filters(self) -> dict:
        """
        Obtiene los valores actuales de los filtros.
        
        Returns:
            Diccionario con los filtros
        """
        plan_data = self.cmb_plan.currentData()
        
        return {
            "nombre": self.txt_nombre.text().strip() or None,
            "apellido": self.txt_apellido.text().strip() or None,
            "email": self.txt_email.text().strip() or None,
            "celular": self.txt_celular.text().strip() or None,
            "plan": plan_data,
            "observaciones": self.txt_observaciones.text().strip() or None,
            "fecha_fin_hasta": self.date_pago.date().toPython() if self.date_pago.date() != QDate.currentDate() else None
        }
