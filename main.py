#!/usr/bin/env python3
"""
BloomFitness - Sistema de Control de Acceso para Gimnasio

Aplicación de escritorio para gestión de usuarios, membresías y control
de acceso mediante tarjetas RFID conectadas via Arduino.

Usage:
    python main.py                  # Modo normal
    BLOOM_DEBUG=1 python main.py    # Modo debug (simula RFID)
"""
import sys
import os

# Agregar el directorio raíz al path para imports
if getattr(sys, 'frozen', False):
    # Ejecutando desde .exe
    sys.path.insert(0, sys._MEIPASS)
else:
    # Ejecutando desde Python
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.config import APP_NAME, DATA_DIR
from src.ui.main_window import MainWindow


def main():
    """Punto de entrada principal de la aplicación."""
    # Crear directorio de datos si no existe
    DATA_DIR.mkdir(exist_ok=True)
    
    # Configurar alta DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Crear aplicación
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")  # Estilo consistente en todas las plataformas
    
    # Fuente por defecto
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
