"""
Configuración global de la aplicación BloomFitness.
"""
import sys
import os
from pathlib import Path

# Detectar si estamos corriendo desde PyInstaller (.exe)
if getattr(sys, 'frozen', False):
    # Ejecutando desde .exe - usar directorio del ejecutable
    APP_DIR = Path(sys.executable).parent
    # Los assets están empaquetados en _MEIPASS
    ASSETS_DIR = Path(sys._MEIPASS) / "assets"
else:
    # Ejecutando desde Python - usar directorio del proyecto
    APP_DIR = Path(__file__).parent.parent
    ASSETS_DIR = APP_DIR / "assets"

# Data siempre junto al ejecutable o proyecto
DATA_DIR = APP_DIR / "data"

# Crear directorio de datos si no existe
DATA_DIR.mkdir(exist_ok=True)

# Base de datos
DATABASE_PATH = DATA_DIR / "gym_access.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Configuración del puerto serial para Arduino
SERIAL_PORT = "COM3"  # Cambiar según el puerto donde está conectado el Arduino
BAUDRATE = 9600
SERIAL_TIMEOUT = 1  # Timeout en segundos para lectura serial

# Modo debug - simula lecturas RFID sin Arduino conectado
DEBUG_MODE = os.environ.get("BLOOM_DEBUG", "0") == "1"
DEBUG_RFID_INTERVAL = 5  # Segundos entre UIDs simulados en modo debug

# Configuración de la aplicación
APP_NAME = "BloomFitness"
APP_VERSION = "1.0.0"
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700
