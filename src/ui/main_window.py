"""
Ventana principal de la aplicación BloomFitness.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCloseEvent

from src.config import APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from src.db.database import init_db, get_db, close_db
from src.db.repository import UserRepository
from src.ui.widgets.sidebar import Sidebar
from src.ui.views.users_view import UsersView
from src.ui.views.rfid_view import RFIDView
from src.ui.views.access_log_view import AccessLogView
from src.services.rfid_listener import RFIDListener
from src.services.access_control import AccessControlService


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar base de datos
        init_db()
        
        # Verificar y desactivar planes vencidos al iniciar
        self._check_expired_plans()
        
        # Configurar ventana
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Cargar estilos
        self._load_styles()
        
        # Servicios
        self.rfid_listener = RFIDListener()
        self.access_control = AccessControlService()
        
        # Conectar señales de RFID
        self.rfid_listener.uid_received.connect(self._on_rfid_received)
        
        # Configurar UI
        self._setup_ui()
        
        # Iniciar listener RFID
        self.rfid_listener.start()
    
    def _check_expired_plans(self):
        """Verifica y desactiva usuarios con planes vencidos."""
        db = get_db()
        try:
            repo = UserRepository(db)
            count = repo.deactivate_expired_plans()
            if count > 0:
                print(f"Se desactivaron {count} usuario(s) con plan vencido.")
        finally:
            db.close()
    
    def _load_styles(self):
        """Carga el archivo de estilos QSS."""
        import sys
        
        # Detectar ruta correcta según si es .exe o Python
        if getattr(sys, 'frozen', False):
            # Ejecutando desde .exe
            base_path = Path(sys._MEIPASS)
        else:
            # Ejecutando desde Python
            base_path = Path(__file__).parent
        
        style_path = base_path / "src" / "ui" / "styles" / "dark_theme.qss"
        
        # Fallback a ruta relativa si no existe
        if not style_path.exists():
            style_path = Path(__file__).parent / "styles" / "dark_theme.qss"
        
        if style_path.exists():
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.usuarios_clicked.connect(lambda: self.show_view(0))
        self.sidebar.tarjetas_clicked.connect(lambda: self.show_view(1))
        self.sidebar.accesos_clicked.connect(lambda: self.show_view(2))
        self.sidebar.salir_clicked.connect(self.close)
        main_layout.addWidget(self.sidebar)
        
        # Stack de vistas
        self.view_stack = QStackedWidget()
        
        # Crear vistas
        self.users_view = UsersView()
        self.rfid_view = RFIDView(self.rfid_listener)
        self.access_log_view = AccessLogView()
        
        # Agregar vistas al stack
        self.view_stack.addWidget(self.users_view)
        self.view_stack.addWidget(self.rfid_view)
        self.view_stack.addWidget(self.access_log_view)
        
        main_layout.addWidget(self.view_stack)
        
        # Mostrar vista inicial
        self.show_view(0)
    
    @Slot(int)
    def show_view(self, index: int):
        """
        Muestra una vista específica.
        
        Args:
            index: Índice de la vista (0=Usuarios, 1=RFID, 2=Accesos)
        """
        self.view_stack.setCurrentIndex(index)
        
        # Refrescar la vista actual
        current_widget = self.view_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
    
    @Slot(str)
    def _on_rfid_received(self, uid: str):
        """
        Maneja la recepción de un UID RFID.
        
        Args:
            uid: UID de la tarjeta RFID
        """
        # Procesar acceso
        result = self.access_control.process_access(uid)
        
        # Actualizar vista de accesos si está visible
        if self.view_stack.currentIndex() == 2:
            self.access_log_view.refresh()
        
        # Actualizar vista RFID
        self.rfid_view.on_uid_received(uid, result)
    
    def closeEvent(self, event: QCloseEvent):
        """Maneja el evento de cierre de la ventana."""
        reply = QMessageBox.question(
            self,
            "Confirmar salida",
            "¿Está seguro que desea salir?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Detener listener RFID
            self.rfid_listener.stop()
            self.rfid_listener.wait()
            
            # Cerrar conexión a base de datos
            close_db()
            
            event.accept()
        else:
            event.ignore()
