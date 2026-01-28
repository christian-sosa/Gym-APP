"""
Diálogo para crear/editar usuarios.
"""
from datetime import date
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QCheckBox,
    QPushButton, QLabel, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont

from src.db.database import get_db
from src.db.repository import UserRepository
from src.db.models import User
from src.utils.enums import PlanType, PaymentMethod
from src.services.plan_calculator import PlanCalculator


class UserDialog(QDialog):
    """Diálogo para crear o editar un usuario."""
    
    # Señal emitida cuando se guarda exitosamente
    user_saved = Signal(int)  # Emite el ID del usuario
    
    # Señal para solicitar escaneo de tarjeta RFID
    request_rfid_scan = Signal()
    
    def __init__(self, user: User = None, parent=None, view_only: bool = False):
        super().__init__(parent)
        
        self.user = user
        self.is_editing = user is not None
        self.view_only = view_only
        self.scanned_rfid = None
        
        if view_only:
            self.setWindowTitle("Ver Usuario")
        else:
            self.setWindowTitle("Editar Usuario" if self.is_editing else "Nuevo Usuario")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._setup_ui()
        
        if self.is_editing:
            self._load_user_data()
        
        if view_only:
            self._set_readonly_mode()
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Editar Usuario" if self.is_editing else "Nuevo Usuario")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #f0c020;")
        layout.addWidget(title)
        
        # Formulario de datos personales
        personal_group = QGroupBox("Datos Personales")
        personal_layout = QFormLayout(personal_group)
        
        self.txt_apellido = QLineEdit()
        self.txt_apellido.setPlaceholderText("Apellido")
        personal_layout.addRow("Apellido *:", self.txt_apellido)
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre")
        personal_layout.addRow("Nombre *:", self.txt_nombre)
        
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("email@ejemplo.com")
        personal_layout.addRow("Email:", self.txt_email)
        
        self.txt_celular = QLineEdit()
        self.txt_celular.setPlaceholderText("1123456789")
        personal_layout.addRow("Celular:", self.txt_celular)
        
        self.txt_observaciones = QTextEdit()
        self.txt_observaciones.setPlaceholderText("Observaciones médicas, restricciones, etc.")
        self.txt_observaciones.setMaximumHeight(80)
        personal_layout.addRow("Observaciones:", self.txt_observaciones)
        
        layout.addWidget(personal_group)
        
        # Formulario de membresía
        plan_group = QGroupBox("Membresía")
        plan_layout = QFormLayout(plan_group)
        
        self.cmb_plan = QComboBox()
        for plan in PlanType:
            self.cmb_plan.addItem(plan.display_name, plan)
        self.cmb_plan.currentIndexChanged.connect(self._on_plan_changed)
        plan_layout.addRow("Plan:", self.cmb_plan)
        
        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDate(QDate.currentDate())
        self.date_inicio.setDisplayFormat("yyyy-MM-dd")
        self.date_inicio.dateChanged.connect(self._on_date_changed)
        plan_layout.addRow("Fecha Inicio:", self.date_inicio)
        
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(False)
        self.date_fin.setReadOnly(True)
        self.date_fin.setEnabled(False)
        self.date_fin.setDisplayFormat("yyyy-MM-dd")
        plan_layout.addRow("Fecha Fin:", self.date_fin)
        
        self.cmb_metodo_pago = QComboBox()
        for metodo in PaymentMethod:
            self.cmb_metodo_pago.addItem(metodo.display_name, metodo)
        plan_layout.addRow("Método de Pago:", self.cmb_metodo_pago)
        
        self.chk_activo = QCheckBox("  Activo")
        self.chk_activo.setChecked(True)
        self.chk_activo.stateChanged.connect(self._on_activo_changed)
        self._update_activo_style()
        plan_layout.addRow("Estado:", self.chk_activo)
        
        layout.addWidget(plan_group)
        
        # Formulario de tarjeta RFID
        rfid_group = QGroupBox("Tarjeta RFID")
        rfid_layout = QHBoxLayout(rfid_group)
        
        self.txt_rfid = QLineEdit()
        self.txt_rfid.setPlaceholderText("UID de la tarjeta")
        self.txt_rfid.setReadOnly(True)
        rfid_layout.addWidget(self.txt_rfid)
        
        self.btn_scan_rfid = QPushButton("Escanear")
        self.btn_scan_rfid.clicked.connect(self._on_scan_rfid)
        rfid_layout.addWidget(self.btn_scan_rfid)
        
        self.btn_clear_rfid = QPushButton("Quitar")
        self.btn_clear_rfid.setObjectName("secondaryButton")
        self.btn_clear_rfid.clicked.connect(self._on_clear_rfid)
        rfid_layout.addWidget(self.btn_clear_rfid)
        
        layout.addWidget(rfid_group)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("Guardar")
        self.btn_save.clicked.connect(self._on_save)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)
        
        # Calcular fecha fin inicial
        self._update_fecha_fin()
    
    def _load_user_data(self):
        """Carga los datos del usuario en el formulario."""
        if not self.user:
            return
        
        self.txt_nombre.setText(self.user.nombre)
        self.txt_apellido.setText(self.user.apellido)
        self.txt_email.setText(self.user.email or "")
        self.txt_celular.setText(self.user.celular or "")
        self.txt_observaciones.setPlainText(self.user.observaciones or "")
        
        # Plan
        index = self.cmb_plan.findData(self.user.plan)
        if index >= 0:
            self.cmb_plan.setCurrentIndex(index)
        
        self.date_inicio.setDate(QDate(
            self.user.fecha_inicio_plan.year,
            self.user.fecha_inicio_plan.month,
            self.user.fecha_inicio_plan.day
        ))
        
        self.date_fin.setDate(QDate(
            self.user.fecha_fin_plan.year,
            self.user.fecha_fin_plan.month,
            self.user.fecha_fin_plan.day
        ))
        
        # Método de pago
        if self.user.metodo_pago:
            index_pago = self.cmb_metodo_pago.findData(self.user.metodo_pago)
            if index_pago >= 0:
                self.cmb_metodo_pago.setCurrentIndex(index_pago)
        
        self.chk_activo.setChecked(self.user.activo)
        self._update_activo_style()
        self.txt_rfid.setText(self.user.rfid_uid or "")
    
    def _set_readonly_mode(self):
        """Configura todos los campos como solo lectura."""
        # Deshabilitar campos de texto
        self.txt_nombre.setReadOnly(True)
        self.txt_apellido.setReadOnly(True)
        self.txt_email.setReadOnly(True)
        self.txt_celular.setReadOnly(True)
        self.txt_observaciones.setReadOnly(True)
        
        # Deshabilitar combos y fechas
        self.cmb_plan.setEnabled(False)
        self.cmb_metodo_pago.setEnabled(False)
        self.date_inicio.setEnabled(False)
        self.chk_activo.setEnabled(False)
        
        # Ocultar botones de RFID
        self.btn_scan_rfid.setVisible(False)
        self.btn_clear_rfid.setVisible(False)
        
        # Cambiar botón Guardar por Cerrar
        self.btn_save.setText("Cerrar")
        self.btn_save.clicked.disconnect()
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.setVisible(False)
    
    def _on_activo_changed(self, state: int):
        """Actualiza el estilo del checkbox cuando cambia."""
        self._update_activo_style()
    
    def _update_activo_style(self):
        """Actualiza el texto y estilo del checkbox de activo."""
        if self.chk_activo.isChecked():
            self.chk_activo.setText("  ✓ Activo")
            self.chk_activo.setStyleSheet("""
                QCheckBox {
                    color: #00cc00;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        else:
            self.chk_activo.setText("  ✗ Inactivo")
            self.chk_activo.setStyleSheet("""
                QCheckBox {
                    color: #ff4444;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
    
    def _on_plan_changed(self, index: int):
        """Actualiza la fecha fin cuando cambia el plan."""
        self._update_fecha_fin()
    
    def _on_date_changed(self, date: QDate):
        """Actualiza la fecha fin cuando cambia la fecha de inicio."""
        self._update_fecha_fin()
    
    def _update_fecha_fin(self):
        """Calcula y actualiza la fecha de fin del plan."""
        plan = self.cmb_plan.currentData()
        fecha_inicio = self.date_inicio.date().toPython()
        
        if plan and fecha_inicio:
            fecha_fin = PlanCalculator.calculate_end_date(fecha_inicio, plan)
            self.date_fin.setDate(QDate(fecha_fin.year, fecha_fin.month, fecha_fin.day))
    
    def _on_scan_rfid(self):
        """Solicita escaneo de tarjeta RFID."""
        self.request_rfid_scan.emit()
        QMessageBox.information(
            self,
            "Escanear Tarjeta",
            "Acerque la tarjeta RFID al lector.\n\n"
            "El UID se capturará automáticamente.",
            QMessageBox.Ok
        )
    
    def _on_clear_rfid(self):
        """Limpia el campo RFID."""
        self.txt_rfid.clear()
        self.scanned_rfid = None
    
    def set_rfid_uid(self, uid: str):
        """
        Establece el UID de la tarjeta RFID.
        
        Args:
            uid: UID de la tarjeta
        """
        # Verificar que no esté asignada a otro usuario
        db = get_db()
        try:
            repo = UserRepository(db)
            existing = repo.get_by_rfid(uid)
            
            if existing and (not self.user or existing.id != self.user.id):
                QMessageBox.warning(
                    self,
                    "Tarjeta Asignada",
                    f"Esta tarjeta ya está asignada a: {existing.nombre_completo}",
                    QMessageBox.Ok
                )
                return
            
            self.txt_rfid.setText(uid)
            self.scanned_rfid = uid
            
        finally:
            db.close()
    
    def _on_save(self):
        """Guarda el usuario."""
        # Validar nombre
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(
                self,
                "Datos Incompletos",
                "El nombre es obligatorio.",
                QMessageBox.Ok
            )
            self.txt_nombre.setFocus()
            return
        
        # Validar apellido
        apellido = self.txt_apellido.text().strip()
        if not apellido:
            QMessageBox.warning(
                self,
                "Datos Incompletos",
                "El apellido es obligatorio.",
                QMessageBox.Ok
            )
            self.txt_apellido.setFocus()
            return
        
        # Obtener datos
        email = self.txt_email.text().strip() or None
        celular = self.txt_celular.text().strip() or None
        observaciones = self.txt_observaciones.toPlainText().strip() or None
        plan = self.cmb_plan.currentData()
        fecha_inicio = self.date_inicio.date().toPython()
        activo = self.chk_activo.isChecked()
        rfid_uid = self.txt_rfid.text().strip() or None
        metodo_pago = self.cmb_metodo_pago.currentData()
        
        db = get_db()
        try:
            repo = UserRepository(db)
            
            if self.is_editing:
                # Actualizar usuario existente
                user = repo.update(
                    user_id=self.user.id,
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    celular=celular,
                    observaciones=observaciones,
                    plan=plan,
                    fecha_inicio_plan=fecha_inicio,
                    rfid_uid=rfid_uid,
                    activo=activo,
                    metodo_pago=metodo_pago
                )
                if user:
                    self.user_saved.emit(user.id)
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "No se pudo actualizar el usuario.")
            else:
                # Crear nuevo usuario
                user = repo.create(
                    nombre=nombre,
                    apellido=apellido,
                    plan=plan,
                    fecha_inicio_plan=fecha_inicio,
                    email=email,
                    celular=celular,
                    observaciones=observaciones,
                    rfid_uid=rfid_uid,
                    activo=activo,
                    metodo_pago=metodo_pago
                )
                self.user_saved.emit(user.id)
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            db.close()
