"""
Vista de gestión de tarjetas RFID.
"""
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGroupBox, QComboBox, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QColor

from src.db.database import get_db
from src.db.repository import UserRepository
from src.db.models import User
from src.services.rfid_listener import RFIDListener
from src.services.access_control import AccessControlService, AccessCheckResult
from src.utils.enums import AccessResult
from src.ui.dialogs.rfid_assign_dialog import RFIDAssignDialog


class RFIDView(QWidget):
    """Vista para gestión de tarjetas RFID."""
    
    def __init__(self, rfid_listener: RFIDListener, parent=None):
        super().__init__(parent)
        self.rfid_listener = rfid_listener
        self.last_result: Optional[AccessCheckResult] = None
        
        self._setup_ui()
        self._connect_signals()
        self.refresh()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Gestión de Tarjetas RFID")
        title.setObjectName("titleLabel")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Panel de estado de conexión
        status_group = QGroupBox("Estado del Lector")
        status_layout = QHBoxLayout(status_group)
        
        self.lbl_status = QLabel("Desconectado")
        self.lbl_status.setObjectName("statusDisconnected")
        self.lbl_status.setFont(QFont("Segoe UI", 12, QFont.Bold))
        status_layout.addWidget(self.lbl_status)
        
        status_layout.addStretch()
        
        # Selector de puerto
        status_layout.addWidget(QLabel("Puerto:"))
        self.cmb_port = QComboBox()
        self.cmb_port.setMinimumWidth(150)
        self._refresh_ports()
        status_layout.addWidget(self.cmb_port)
        
        self.btn_refresh_ports = QPushButton("Actualizar")
        self.btn_refresh_ports.setObjectName("secondaryButton")
        self.btn_refresh_ports.clicked.connect(self._refresh_ports)
        status_layout.addWidget(self.btn_refresh_ports)
        
        # Modo debug
        self.btn_debug = QPushButton("Modo Debug: OFF")
        self.btn_debug.setCheckable(True)
        self.btn_debug.setChecked(self.rfid_listener.is_debug_mode)
        self._update_debug_button()
        self.btn_debug.clicked.connect(self._on_toggle_debug)
        status_layout.addWidget(self.btn_debug)
        
        layout.addWidget(status_group)
        
        # Panel de control manual (visitantes)
        manual_group = QGroupBox("Control Manual")
        manual_layout = QHBoxLayout(manual_group)
        
        manual_info = QLabel("Abrir puerta para visitantes sin tarjeta RFID:")
        manual_info.setFont(QFont("Segoe UI", 10))
        manual_layout.addWidget(manual_info)
        
        manual_layout.addStretch()
        
        self.btn_open_door = QPushButton("   ABRIR PUERTA   ")
        self.btn_open_door.setObjectName("openDoorButton")
        self.btn_open_door.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.btn_open_door.setMinimumHeight(50)
        self.btn_open_door.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.btn_open_door.clicked.connect(self._on_open_door_manual)
        manual_layout.addWidget(self.btn_open_door)
        
        layout.addWidget(manual_group)
        
        # Panel de último acceso
        access_group = QGroupBox("Último Acceso Detectado")
        access_layout = QVBoxLayout(access_group)
        
        self.lbl_last_uid = QLabel("UID: ---")
        self.lbl_last_uid.setFont(QFont("Segoe UI", 14))
        access_layout.addWidget(self.lbl_last_uid)
        
        self.lbl_last_user = QLabel("Usuario: ---")
        self.lbl_last_user.setFont(QFont("Segoe UI", 12))
        access_layout.addWidget(self.lbl_last_user)
        
        self.lbl_last_result = QLabel("Resultado: ---")
        self.lbl_last_result.setFont(QFont("Segoe UI", 12, QFont.Bold))
        access_layout.addWidget(self.lbl_last_result)
        
        layout.addWidget(access_group)
        
        # Log de lecturas
        log_group = QGroupBox("Log de Lecturas (Tiempo Real)")
        log_layout = QVBoxLayout(log_group)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(150)
        self.txt_log.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px;")
        log_layout.addWidget(self.txt_log)
        
        btn_clear_log = QPushButton("Limpiar Log")
        btn_clear_log.setObjectName("secondaryButton")
        btn_clear_log.clicked.connect(self.txt_log.clear)
        log_layout.addWidget(btn_clear_log, alignment=Qt.AlignRight)
        
        layout.addWidget(log_group)
        
        # Tabla de tarjetas asignadas
        cards_group = QGroupBox("Tarjetas Asignadas")
        cards_layout = QVBoxLayout(cards_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Usuario", "RFID UID", "Plan", "Estado"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        cards_layout.addWidget(self.table)
        
        # Botones de tarjetas
        cards_buttons = QHBoxLayout()
        cards_buttons.addStretch()
        
        self.btn_assign = QPushButton("Asignar Tarjeta")
        self.btn_assign.clicked.connect(self._on_assign_card)
        cards_buttons.addWidget(self.btn_assign)
        
        self.btn_remove = QPushButton("Quitar Tarjeta")
        self.btn_remove.setObjectName("dangerButton")
        self.btn_remove.clicked.connect(self._on_remove_card)
        cards_buttons.addWidget(self.btn_remove)
        
        cards_layout.addLayout(cards_buttons)
        layout.addWidget(cards_group)
    
    def _connect_signals(self):
        """Conecta las señales del listener RFID."""
        self.rfid_listener.connection_status.connect(self._on_connection_status)
        self.rfid_listener.error_occurred.connect(self._on_error)
    
    def _refresh_ports(self):
        """Actualiza la lista de puertos disponibles."""
        self.cmb_port.clear()
        ports = RFIDListener.list_available_ports()
        
        if ports:
            for port, desc in ports:
                self.cmb_port.addItem(f"{port} - {desc}", port)
        else:
            self.cmb_port.addItem("No hay puertos disponibles", None)
    
    def _update_debug_button(self):
        """Actualiza el estado visual del botón de debug."""
        if self.rfid_listener.is_debug_mode:
            self.btn_debug.setText("Modo Debug: ON")
            self.btn_debug.setStyleSheet("background-color: #00cc00; color: #000;")
        else:
            self.btn_debug.setText("Modo Debug: OFF")
            self.btn_debug.setStyleSheet("")
    
    @Slot(bool)
    def _on_connection_status(self, connected: bool):
        """Actualiza el indicador de estado de conexión."""
        if connected:
            self.lbl_status.setText("Conectado")
            self.lbl_status.setObjectName("statusConnected")
        else:
            self.lbl_status.setText("Desconectado")
            self.lbl_status.setObjectName("statusDisconnected")
        
        # Forzar actualización de estilo
        self.lbl_status.style().unpolish(self.lbl_status)
        self.lbl_status.style().polish(self.lbl_status)
    
    @Slot(str)
    def _on_error(self, error: str):
        """Muestra errores del listener."""
        self._log(f"ERROR: {error}")
    
    @Slot()
    def _on_toggle_debug(self):
        """Alterna el modo debug."""
        enabled = self.btn_debug.isChecked()
        self.rfid_listener.set_debug_mode(enabled)
        self._update_debug_button()
        
        if enabled:
            self._log("Modo debug activado - Se simularán lecturas RFID")
        else:
            self._log("Modo debug desactivado")
    
    def on_uid_received(self, uid: str, result: AccessCheckResult):
        """
        Maneja la recepción de un UID y su resultado.
        
        Args:
            uid: UID de la tarjeta
            result: Resultado del control de acceso
        """
        self.last_result = result
        
        # Actualizar panel de último acceso
        self.lbl_last_uid.setText(f"UID: {uid}")
        
        if result.user:
            self.lbl_last_user.setText(f"Usuario: {result.user.nombre_completo}")
        else:
            self.lbl_last_user.setText("Usuario: No registrado")
        
        if result.resultado == AccessResult.PERMITIDO:
            self.lbl_last_result.setText("Resultado: ACCESO PERMITIDO")
            self.lbl_last_result.setStyleSheet("color: #00cc00; font-weight: bold;")
        else:
            self.lbl_last_result.setText(f"Resultado: ACCESO DENEGADO ({result.motivo.value})")
            self.lbl_last_result.setStyleSheet("color: #ff4444; font-weight: bold;")
        
        # Agregar al log
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "OK" if result.resultado == AccessResult.PERMITIDO else "DENEGADO"
        user_name = result.user.nombre_completo if result.user else "No registrado"
        self._log(f"[{timestamp}] {uid} - {user_name} - {status}")
    
    def _log(self, message: str):
        """Agrega un mensaje al log."""
        self.txt_log.append(message)
    
    def refresh(self):
        """Recarga la tabla de tarjetas asignadas."""
        db = get_db()
        try:
            repo = UserRepository(db)
            users = repo.search(solo_activos=False)
            
            # Filtrar solo usuarios con tarjeta asignada
            users_with_rfid = [u for u in users if u.rfid_uid]
            
            self.table.setRowCount(0)
            
            for user in users_with_rfid:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Nombre completo
                name_item = QTableWidgetItem(user.nombre_completo)
                name_item.setData(Qt.UserRole, user.id)
                self.table.setItem(row, 0, name_item)
                
                # RFID
                rfid_item = QTableWidgetItem(user.rfid_uid)
                self.table.setItem(row, 1, rfid_item)
                
                # Plan
                plan_item = QTableWidgetItem(user.plan.display_name)
                self.table.setItem(row, 2, plan_item)
                
                # Estado
                if not user.activo:
                    estado = "Inactivo"
                    color = "#ff4444"
                elif not user.plan_vigente:
                    estado = "Vencido"
                    color = "#ffaa00"
                else:
                    estado = "Activo"
                    color = "#00cc00"
                
                estado_item = QTableWidgetItem(estado)
                estado_item.setForeground(QColor(color))
                self.table.setItem(row, 3, estado_item)
                
        finally:
            db.close()
    
    @Slot()
    def _on_assign_card(self):
        """Abre el diálogo para asignar una tarjeta."""
        # Obtener usuarios sin tarjeta
        db = get_db()
        try:
            repo = UserRepository(db)
            users = repo.get_all()
            users_without_rfid = [u for u in users if not u.rfid_uid and u.activo]
            
            if not users_without_rfid:
                QMessageBox.information(
                    self,
                    "Sin Usuarios Disponibles",
                    "Todos los usuarios activos ya tienen tarjeta asignada.",
                    QMessageBox.Ok
                )
                return
            
            # Por simplicidad, usar el primer usuario sin tarjeta
            # En una implementación más completa, se mostraría un selector
            user = users_without_rfid[0]
            
            dialog = RFIDAssignDialog(user, parent=self)
            
            # Conectar listener RFID al diálogo
            self.rfid_listener.uid_received.connect(dialog.on_uid_received)
            
            dialog.rfid_assigned.connect(self.refresh)
            dialog.exec()
            
            # Desconectar
            self.rfid_listener.uid_received.disconnect(dialog.on_uid_received)
            
        finally:
            db.close()
    
    @Slot()
    def _on_remove_card(self):
        """Quita la tarjeta del usuario seleccionado."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self,
                "Selección Requerida",
                "Seleccione un usuario para quitar su tarjeta.",
                QMessageBox.Ok
            )
            return
        
        row = selected[0].row()
        user_id = self.table.item(row, 0).data(Qt.UserRole)
        user_name = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Quitar la tarjeta RFID de {user_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db = get_db()
            try:
                repo = UserRepository(db)
                repo.remove_rfid(user_id)
                self.refresh()
            finally:
                db.close()
    
    @Slot()
    def _on_open_door_manual(self):
        """Abre la puerta manualmente para visitantes."""
        # Enviar comando al Arduino
        success = self.rfid_listener.send_open_door_command()
        
        if success:
            # Registrar el acceso manual
            access_service = AccessControlService()
            result = access_service.register_manual_access("Visitante")
            
            # Mostrar feedback visual
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._log(f"[{timestamp}] APERTURA MANUAL - Visitante - PUERTA ABIERTA")
            
            # Actualizar panel de último acceso
            self.lbl_last_uid.setText("UID: MANUAL")
            self.lbl_last_user.setText("Usuario: Visitante")
            self.lbl_last_result.setText("Resultado: PUERTA ABIERTA")
            self.lbl_last_result.setStyleSheet("color: #2196F3; font-weight: bold;")
            
            # Feedback temporal en el botón
            original_text = self.btn_open_door.text()
            self.btn_open_door.setText("   PUERTA ABIERTA!   ")
            self.btn_open_door.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 30px;
                }
            """)
            
            # Restaurar después de 2 segundos
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self._reset_open_button(original_text))
        else:
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo enviar el comando al Arduino.\nVerifique la conexión.",
                QMessageBox.Ok
            )
    
    def _reset_open_button(self, original_text: str):
        """Restaura el botón de apertura a su estado original."""
        self.btn_open_door.setText(original_text)
        self.btn_open_door.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
