"""
Vista de registro de accesos.
"""
from datetime import datetime, date, timedelta
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGroupBox, QComboBox, QDateEdit, QLineEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot
from PySide6.QtGui import QFont, QColor

from src.db.database import get_db
from src.db.repository import AccessLogRepository
from src.db.models import AccessLog
from src.utils.enums import AccessResult
from src.utils.dates import formato_datetime
from src.utils.export import export_to_csv, generate_export_filename


class AccessLogView(QWidget):
    """Vista para el registro de accesos."""
    
    COLUMNS = ["Fecha/Hora", "Usuario", "RFID", "Resultado", "Motivo"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Registro de Accesos")
        title.setObjectName("titleLabel")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Panel de estadísticas
        stats_group = QGroupBox("Estadísticas del Día")
        stats_layout = QHBoxLayout(stats_group)
        
        self.lbl_total = QLabel("Total: 0")
        self.lbl_total.setFont(QFont("Segoe UI", 12))
        stats_layout.addWidget(self.lbl_total)
        
        self.lbl_permitidos = QLabel("Permitidos: 0")
        self.lbl_permitidos.setFont(QFont("Segoe UI", 12))
        self.lbl_permitidos.setStyleSheet("color: #00cc00;")
        stats_layout.addWidget(self.lbl_permitidos)
        
        self.lbl_denegados = QLabel("Denegados: 0")
        self.lbl_denegados.setFont(QFont("Segoe UI", 12))
        self.lbl_denegados.setStyleSheet("color: #ff4444;")
        stats_layout.addWidget(self.lbl_denegados)
        
        stats_layout.addStretch()
        layout.addWidget(stats_group)
        
        # Panel de filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        # Fecha desde
        filters_layout.addWidget(QLabel("Desde:"))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addDays(-7))
        self.date_desde.setDisplayFormat("yyyy-MM-dd")
        filters_layout.addWidget(self.date_desde)
        
        # Fecha hasta
        filters_layout.addWidget(QLabel("Hasta:"))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setDisplayFormat("yyyy-MM-dd")
        filters_layout.addWidget(self.date_hasta)
        
        # Resultado
        filters_layout.addWidget(QLabel("Resultado:"))
        self.cmb_resultado = QComboBox()
        self.cmb_resultado.addItem("Todos", None)
        self.cmb_resultado.addItem("Permitido", AccessResult.PERMITIDO)
        self.cmb_resultado.addItem("Denegado", AccessResult.DENEGADO)
        filters_layout.addWidget(self.cmb_resultado)
        
        # RFID
        filters_layout.addWidget(QLabel("RFID:"))
        self.txt_rfid = QLineEdit()
        self.txt_rfid.setPlaceholderText("UID de tarjeta")
        self.txt_rfid.setMaximumWidth(150)
        filters_layout.addWidget(self.txt_rfid)
        
        filters_layout.addStretch()
        
        # Botón buscar
        self.btn_search = QPushButton("Buscar")
        self.btn_search.clicked.connect(self._on_search)
        filters_layout.addWidget(self.btn_search)
        
        # Botón limpiar
        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setObjectName("secondaryButton")
        self.btn_clear.clicked.connect(self._on_clear_filters)
        filters_layout.addWidget(self.btn_clear)
        
        layout.addWidget(filters_group)
        
        # Tabla de registros
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Usuario
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # RFID
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Resultado
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Motivo
        
        layout.addWidget(self.table)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.clicked.connect(self.refresh)
        buttons_layout.addWidget(self.btn_refresh)
        
        self.btn_export = QPushButton("Exportar CSV")
        self.btn_export.clicked.connect(self._on_export)
        buttons_layout.addWidget(self.btn_export)
        
        layout.addLayout(buttons_layout)
    
    def refresh(self):
        """Recarga los datos con los filtros actuales."""
        self._on_search()
    
    @Slot()
    def _on_search(self):
        """Realiza la búsqueda con los filtros."""
        fecha_desde = datetime.combine(
            self.date_desde.date().toPython(),
            datetime.min.time()
        )
        fecha_hasta = datetime.combine(
            self.date_hasta.date().toPython(),
            datetime.max.time()
        )
        resultado = self.cmb_resultado.currentData()
        rfid = self.txt_rfid.text().strip() or None
        
        db = get_db()
        try:
            repo = AccessLogRepository(db)
            logs = repo.search(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                resultado=resultado,
                rfid_uid=rfid
            )
            self._populate_table(logs)
            self._update_stats(logs)
        finally:
            db.close()
    
    @Slot()
    def _on_clear_filters(self):
        """Limpia los filtros y recarga."""
        self.date_desde.setDate(QDate.currentDate().addDays(-7))
        self.date_hasta.setDate(QDate.currentDate())
        self.cmb_resultado.setCurrentIndex(0)
        self.txt_rfid.clear()
        self.refresh()
    
    def _populate_table(self, logs: list):
        """Llena la tabla con los registros."""
        self.table.setRowCount(0)
        
        for log in logs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Fecha/Hora
            fecha_item = QTableWidgetItem(formato_datetime(log.timestamp))
            self.table.setItem(row, 0, fecha_item)
            
            # Usuario
            user_name = log.user.nombre_completo if log.user else "No registrado"
            user_item = QTableWidgetItem(user_name)
            self.table.setItem(row, 1, user_item)
            
            # RFID
            rfid_item = QTableWidgetItem(log.rfid_uid)
            self.table.setItem(row, 2, rfid_item)
            
            # Resultado
            resultado_text = "PERMITIDO" if log.resultado == AccessResult.PERMITIDO else "DENEGADO"
            resultado_item = QTableWidgetItem(resultado_text)
            
            if log.resultado == AccessResult.PERMITIDO:
                resultado_item.setForeground(QColor("#00cc00"))
            else:
                resultado_item.setForeground(QColor("#ff4444"))
            
            self.table.setItem(row, 3, resultado_item)
            
            # Motivo
            motivo_item = QTableWidgetItem(log.motivo.value)
            self.table.setItem(row, 4, motivo_item)
    
    def _update_stats(self, logs: list):
        """Actualiza las estadísticas."""
        total = len(logs)
        permitidos = sum(1 for log in logs if log.resultado == AccessResult.PERMITIDO)
        denegados = total - permitidos
        
        self.lbl_total.setText(f"Total: {total}")
        self.lbl_permitidos.setText(f"Permitidos: {permitidos}")
        self.lbl_denegados.setText(f"Denegados: {denegados}")
    
    @Slot()
    def _on_export(self):
        """Exporta los registros a CSV."""
        # Obtener datos actuales de la tabla
        if self.table.rowCount() == 0:
            QMessageBox.warning(
                self,
                "Sin Datos",
                "No hay registros para exportar.",
                QMessageBox.Ok
            )
            return
        
        # Seleccionar ubicación
        default_name = generate_export_filename("accesos")
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar CSV",
            default_name,
            "CSV Files (*.csv)"
        )
        
        if not filepath:
            return
        
        # Preparar datos
        data = []
        for row in range(self.table.rowCount()):
            data.append({
                "Fecha/Hora": self.table.item(row, 0).text(),
                "Usuario": self.table.item(row, 1).text(),
                "RFID": self.table.item(row, 2).text(),
                "Resultado": self.table.item(row, 3).text(),
                "Motivo": self.table.item(row, 4).text()
            })
        
        # Exportar
        success = export_to_csv(data, Path(filepath), self.COLUMNS)
        
        if success:
            QMessageBox.information(
                self,
                "Exportación Exitosa",
                f"Se exportaron {len(data)} registros a:\n{filepath}",
                QMessageBox.Ok
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo exportar el archivo.",
                QMessageBox.Ok
            )
