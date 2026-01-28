"""
Widget de barra lateral (sidebar) para navegación.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QPixmap

from src.config import ASSETS_DIR


class Sidebar(QWidget):
    """Barra lateral con botones de navegación."""
    
    # Señales para navegación
    usuarios_clicked = Signal()
    tarjetas_clicked = Signal()
    accesos_clicked = Signal()
    salir_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Contenedor del logo
        logo_container = QWidget()
        logo_container.setStyleSheet("background-color: #0d0d0d;")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(10, 20, 10, 20)
        logo_layout.setAlignment(Qt.AlignCenter)
        
        # Logo - placeholder para imagen del gimnasio
        self.logo_label = QLabel()
        self.logo_label.setObjectName("logoLabel")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setMinimumSize(150, 100)
        self.logo_label.setMaximumSize(180, 120)
        
        # Intentar cargar logo - buscar en múltiples ubicaciones
        import sys
        logo_loaded = False
        
        # Lista de posibles ubicaciones del logo
        logo_paths = [ASSETS_DIR / "logo.png"]
        
        # Si estamos en .exe, también buscar junto al ejecutable
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).parent
            logo_paths.insert(0, exe_dir / "assets" / "logo.png")
            logo_paths.insert(0, exe_dir / "logo.png")
        
        for logo_path in logo_paths:
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    self.logo_label.setPixmap(
                        pixmap.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    )
                    logo_loaded = True
                    break
        
        if not logo_loaded:
            # Placeholder cuando no hay logo
            self.logo_label.setText("LOGO\nGIMNASIO")
            self.logo_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
            self.logo_label.setStyleSheet("""
                QLabel {
                    color: #f0c020;
                    border: 2px dashed #f0c020;
                    border-radius: 10px;
                    padding: 20px;
                }
            """)
        
        logo_layout.addWidget(self.logo_label)
        layout.addWidget(logo_container)
        
        # Separador
        layout.addSpacing(20)
        
        # Botones de navegación
        self.btn_usuarios = self._create_nav_button("Usuarios", "👥")
        self.btn_usuarios.setChecked(True)
        self.btn_usuarios.clicked.connect(self._on_usuarios_clicked)
        layout.addWidget(self.btn_usuarios)
        
        self.btn_tarjetas = self._create_nav_button("Tarjetas RFID", "💳")
        self.btn_tarjetas.clicked.connect(self._on_tarjetas_clicked)
        layout.addWidget(self.btn_tarjetas)
        
        self.btn_accesos = self._create_nav_button("Registro Accesos", "📋")
        self.btn_accesos.clicked.connect(self._on_accesos_clicked)
        layout.addWidget(self.btn_accesos)
        
        # Espaciador flexible
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Botón salir
        self.btn_salir = QPushButton("Salir")
        self.btn_salir.setObjectName("exitButton")
        self.btn_salir.setMinimumHeight(45)
        self.btn_salir.clicked.connect(self.salir_clicked.emit)
        layout.addWidget(self.btn_salir)
        
        layout.addSpacing(20)
    
    def _create_nav_button(self, text: str, icon: str = "") -> QPushButton:
        """Crea un botón de navegación."""
        btn = QPushButton(f"  {icon}  {text}" if icon else text)
        btn.setCheckable(True)
        btn.setMinimumHeight(50)
        btn.setFont(QFont("Segoe UI", 11))
        return btn
    
    def _uncheck_all(self):
        """Desmarca todos los botones."""
        self.btn_usuarios.setChecked(False)
        self.btn_tarjetas.setChecked(False)
        self.btn_accesos.setChecked(False)
    
    def _on_usuarios_clicked(self):
        """Maneja clic en botón Usuarios."""
        self._uncheck_all()
        self.btn_usuarios.setChecked(True)
        self.usuarios_clicked.emit()
    
    def _on_tarjetas_clicked(self):
        """Maneja clic en botón Tarjetas."""
        self._uncheck_all()
        self.btn_tarjetas.setChecked(True)
        self.tarjetas_clicked.emit()
    
    def _on_accesos_clicked(self):
        """Maneja clic en botón Accesos."""
        self._uncheck_all()
        self.btn_accesos.setChecked(True)
        self.accesos_clicked.emit()
    
    def select_usuarios(self):
        """Selecciona programáticamente la vista de usuarios."""
        self._on_usuarios_clicked()
    
    def select_tarjetas(self):
        """Selecciona programáticamente la vista de tarjetas."""
        self._on_tarjetas_clicked()
    
    def select_accesos(self):
        """Selecciona programáticamente la vista de accesos."""
        self._on_accesos_clicked()
