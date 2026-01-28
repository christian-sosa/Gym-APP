"""
Diálogo para asignar tarjeta RFID a un usuario.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from src.db.database import get_db
from src.db.repository import UserRepository
from src.db.models import User


class RFIDAssignDialog(QDialog):
    """Diálogo para asignar una tarjeta RFID a un usuario."""
    
    # Señal emitida cuando se asigna exitosamente
    rfid_assigned = Signal(str)  # Emite el UID asignado
    
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        
        self.user = user
        self.captured_uid = None
        
        self.setWindowTitle("Asignar Tarjeta RFID")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("Asignar Tarjeta RFID")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #f0c020;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Info del usuario
        user_info = QLabel(f"Usuario: {self.user.nombre_completo}")
        user_info.setFont(QFont("Segoe UI", 12))
        user_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(user_info)
        
        # Tarjeta actual
        if self.user.rfid_uid:
            current_rfid = QLabel(f"Tarjeta actual: {self.user.rfid_uid}")
            current_rfid.setStyleSheet("color: #888888;")
            current_rfid.setAlignment(Qt.AlignCenter)
            layout.addWidget(current_rfid)
        
        # Instrucciones
        instructions = QLabel("Acerque la tarjeta RFID al lector...")
        instructions.setFont(QFont("Segoe UI", 11))
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet("color: #aaaaaa; margin: 20px 0;")
        layout.addWidget(instructions)
        
        # Indicador de espera
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminado
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        
        # UID capturado
        self.lbl_uid = QLabel("")
        self.lbl_uid.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_uid.setAlignment(Qt.AlignCenter)
        self.lbl_uid.setStyleSheet("color: #00cc00; margin: 10px 0;")
        layout.addWidget(self.lbl_uid)
        
        # Estado
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        self.btn_assign = QPushButton("Asignar")
        self.btn_assign.setEnabled(False)
        self.btn_assign.clicked.connect(self._on_assign)
        buttons_layout.addWidget(self.btn_assign)
        
        layout.addLayout(buttons_layout)
    
    @Slot(str)
    def on_uid_received(self, uid: str):
        """
        Maneja la recepción de un UID.
        
        Args:
            uid: UID de la tarjeta leída
        """
        # Verificar si ya está asignada a otro usuario
        db = get_db()
        try:
            repo = UserRepository(db)
            existing = repo.get_by_rfid(uid)
            
            if existing and existing.id != self.user.id:
                self.lbl_uid.setText(uid)
                self.lbl_uid.setStyleSheet("color: #ff4444;")
                self.lbl_status.setText(f"Esta tarjeta ya está asignada a: {existing.nombre_completo}")
                self.lbl_status.setStyleSheet("color: #ff4444;")
                self.btn_assign.setEnabled(False)
            else:
                self.captured_uid = uid
                self.lbl_uid.setText(uid)
                self.lbl_uid.setStyleSheet("color: #00cc00;")
                self.lbl_status.setText("Tarjeta lista para asignar")
                self.lbl_status.setStyleSheet("color: #00cc00;")
                self.btn_assign.setEnabled(True)
                self.progress.setRange(0, 1)
                self.progress.setValue(1)
                
        finally:
            db.close()
    
    def _on_assign(self):
        """Asigna la tarjeta al usuario."""
        if not self.captured_uid:
            return
        
        db = get_db()
        try:
            repo = UserRepository(db)
            user = repo.assign_rfid(self.user.id, self.captured_uid)
            
            if user:
                self.rfid_assigned.emit(self.captured_uid)
                QMessageBox.information(
                    self,
                    "Tarjeta Asignada",
                    f"La tarjeta {self.captured_uid} fue asignada a {self.user.nombre_completo}",
                    QMessageBox.Ok
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo asignar la tarjeta.",
                    QMessageBox.Ok
                )
        finally:
            db.close()
