"""
Vista de gestión de usuarios.
"""
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QAbstractItemView, QLabel
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QColor

from src.db.database import get_db
from src.db.repository import UserRepository
from src.db.models import User
from src.ui.widgets.search_bar import SearchBar
from src.ui.dialogs.user_dialog import UserDialog
from src.utils.dates import formato_fecha
from src.services.plan_calculator import PlanCalculator


class UsersView(QWidget):
    """Vista principal para gestión de usuarios."""
    
    # Columnas de la tabla
    COLUMNS = ["ID", "Apellido", "Nombre", "Email", "Celular", "Membresía", "Observaciones", "Fecha Fin", "Estado"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._users: List[User] = []
        self._show_inactive = True  # Por defecto mostrar inactivos
        self._show_active = True    # Por defecto mostrar activos
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Barra de búsqueda
        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.clear_triggered.connect(self.refresh)
        layout.addWidget(self.search_bar)
        
        # Tabla de usuarios
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_view_user)
        
        # Configurar encabezado vertical (números de fila) con más ancho
        vertical_header = self.table.verticalHeader()
        vertical_header.setDefaultSectionSize(35)  # Altura de filas
        vertical_header.setMinimumWidth(50)  # Ancho mínimo para números de fila
        
        # Configurar columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Apellido
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Email
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Celular
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Membresía
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Observaciones
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Fecha Fin
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Estado
        
        # Ocultar columna ID
        self.table.setColumnHidden(0, True)
        
        layout.addWidget(self.table)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        # Botón para mostrar/ocultar inactivos
        self.btn_toggle_inactive = QPushButton("Ocultar Inactivos")
        self.btn_toggle_inactive.setObjectName("secondaryButton")
        self.btn_toggle_inactive.setCheckable(True)
        self.btn_toggle_inactive.clicked.connect(self._on_toggle_inactive)
        buttons_layout.addWidget(self.btn_toggle_inactive)
        
        # Botón para mostrar/ocultar activos
        self.btn_toggle_active = QPushButton("Ocultar Activos")
        self.btn_toggle_active.setObjectName("secondaryButton")
        self.btn_toggle_active.setCheckable(True)
        self.btn_toggle_active.clicked.connect(self._on_toggle_active)
        buttons_layout.addWidget(self.btn_toggle_active)
        
        # Contador de usuarios
        self.lbl_counter = QLabel("Total: 0")
        self.lbl_counter.setStyleSheet("color: #aaaaaa; font-size: 12px; margin-left: 10px;")
        buttons_layout.addWidget(self.lbl_counter)
        
        buttons_layout.addStretch()
        
        self.btn_add = QPushButton("Agregar Usuario")
        self.btn_add.clicked.connect(self._on_add_user)
        buttons_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("Editar Usuario")
        self.btn_edit.clicked.connect(self._on_edit_user)
        buttons_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("Eliminar Seleccionado")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(self._on_delete_users)
        buttons_layout.addWidget(self.btn_delete)
        
        layout.addLayout(buttons_layout)
    
    def refresh(self):
        """Recarga los datos de la tabla."""
        db = get_db()
        try:
            repo = UserRepository(db)
            all_users = repo.get_all(include_inactive=True)
            
            # Aplicar filtros de activos/inactivos
            self._users = self._filter_users(all_users)
            self._populate_table(self._users)
            self._update_counter()
        finally:
            db.close()
    
    def _filter_users(self, users: List[User]) -> List[User]:
        """Filtra usuarios según los toggles de activos/inactivos."""
        filtered = []
        for user in users:
            if user.activo and not self._show_active:
                continue
            if not user.activo and not self._show_inactive:
                continue
            filtered.append(user)
        return filtered
    
    def _update_counter(self):
        """Actualiza el contador de usuarios mostrados."""
        count = len(self._users)
        self.lbl_counter.setText(f"Total: {count}")
    
    @Slot()
    def _on_toggle_inactive(self):
        """Alterna la visualización de usuarios inactivos."""
        self._show_inactive = not self.btn_toggle_inactive.isChecked()
        
        if self._show_inactive:
            self.btn_toggle_inactive.setText("Ocultar Inactivos")
        else:
            self.btn_toggle_inactive.setText("Mostrar Inactivos")
        
        self.refresh()
    
    @Slot()
    def _on_toggle_active(self):
        """Alterna la visualización de usuarios activos."""
        self._show_active = not self.btn_toggle_active.isChecked()
        
        if self._show_active:
            self.btn_toggle_active.setText("Ocultar Activos")
        else:
            self.btn_toggle_active.setText("Mostrar Activos")
        
        self.refresh()
    
    @Slot(dict)
    def _on_search(self, filters: dict):
        """Realiza búsqueda con los filtros proporcionados."""
        db = get_db()
        try:
            repo = UserRepository(db)
            all_users = repo.search(**filters)
            self._users = self._filter_users(all_users)
            self._populate_table(self._users)
            self._update_counter()
        finally:
            db.close()
    
    def _populate_table(self, users: List[User]):
        """
        Llena la tabla con los usuarios proporcionados.
        
        Args:
            users: Lista de usuarios a mostrar
        """
        self.table.setRowCount(0)
        
        for user in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ID (oculto)
            id_item = QTableWidgetItem(str(user.id))
            self.table.setItem(row, 0, id_item)
            
            # Apellido
            apellido_item = QTableWidgetItem(user.apellido)
            self.table.setItem(row, 1, apellido_item)
            
            # Nombre
            nombre_item = QTableWidgetItem(user.nombre)
            self.table.setItem(row, 2, nombre_item)
            
            # Email
            email_item = QTableWidgetItem(user.email or "")
            self.table.setItem(row, 3, email_item)
            
            # Celular
            celular_item = QTableWidgetItem(user.celular or "")
            self.table.setItem(row, 4, celular_item)
            
            # Membresía
            plan_item = QTableWidgetItem(user.plan.display_name)
            self.table.setItem(row, 5, plan_item)
            
            # Observaciones
            obs_item = QTableWidgetItem(user.observaciones or "")
            self.table.setItem(row, 6, obs_item)
            
            # Fecha Fin
            fecha_item = QTableWidgetItem(formato_fecha(user.fecha_fin_plan))
            
            # Colorear según vigencia
            if not user.plan_vigente:
                fecha_item.setForeground(QColor("#ff4444"))
            elif user.dias_restantes <= 7:
                fecha_item.setForeground(QColor("#ffaa00"))
            else:
                fecha_item.setForeground(QColor("#00cc00"))
            
            self.table.setItem(row, 7, fecha_item)
            
            # Estado
            estado_text = "Activo" if user.activo else "Inactivo"
            estado_item = QTableWidgetItem(estado_text)
            if user.activo:
                estado_item.setForeground(QColor("#00cc00"))
            else:
                estado_item.setForeground(QColor("#ff4444"))
            self.table.setItem(row, 8, estado_item)
    
    def _get_selected_user_ids(self) -> List[int]:
        """Obtiene los IDs de los usuarios seleccionados."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        user_ids = []
        for row in selected_rows:
            id_item = self.table.item(row, 0)
            if id_item:
                user_ids.append(int(id_item.text()))
        
        return user_ids
    
    def _get_selected_user(self) -> Optional[User]:
        """Obtiene el usuario seleccionado (primero si hay múltiples)."""
        user_ids = self._get_selected_user_ids()
        if not user_ids:
            return None
        
        db = get_db()
        try:
            repo = UserRepository(db)
            return repo.get_by_id(user_ids[0])
        finally:
            db.close()
    
    @Slot()
    def _on_add_user(self):
        """Abre el diálogo para agregar un nuevo usuario."""
        dialog = UserDialog(parent=self)
        dialog.user_saved.connect(self.refresh)
        dialog.exec()
    
    @Slot()
    def _on_view_user(self):
        """Abre el diálogo para ver el usuario seleccionado (solo lectura)."""
        user = self._get_selected_user()
        if not user:
            return
        
        dialog = UserDialog(user=user, parent=self, view_only=True)
        dialog.exec()
    
    @Slot()
    def _on_edit_user(self):
        """Abre el diálogo para editar el usuario seleccionado."""
        user = self._get_selected_user()
        if not user:
            QMessageBox.warning(
                self,
                "Selección Requerida",
                "Seleccione un usuario para editar.",
                QMessageBox.Ok
            )
            return
        
        dialog = UserDialog(user=user, parent=self)
        dialog.user_saved.connect(self.refresh)
        dialog.exec()
    
    @Slot()
    def _on_delete_users(self):
        """Elimina los usuarios seleccionados."""
        user_ids = self._get_selected_user_ids()
        if not user_ids:
            QMessageBox.warning(
                self,
                "Selección Requerida",
                "Seleccione al menos un usuario para eliminar.",
                QMessageBox.Ok
            )
            return
        
        count = len(user_ids)
        msg = f"¿Está seguro que desea eliminar {count} usuario(s)?\n\nEsta acción no se puede deshacer."
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db = get_db()
            try:
                repo = UserRepository(db)
                deleted = 0
                for user_id in user_ids:
                    if repo.delete(user_id):
                        deleted += 1
                
                QMessageBox.information(
                    self,
                    "Eliminación Completada",
                    f"Se eliminaron {deleted} usuario(s).",
                    QMessageBox.Ok
                )
                self.refresh()
            finally:
                db.close()
