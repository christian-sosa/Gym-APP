"""
Listener para lectura de tarjetas RFID vía puerto serial (Arduino).
"""
import time
import random
import string

from PySide6.QtCore import QThread, Signal

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from src.config import SERIAL_PORT, BAUDRATE, SERIAL_TIMEOUT, DEBUG_MODE, DEBUG_RFID_INTERVAL


class RFIDListener(QThread):
    """
    Thread para escuchar lecturas de tarjetas RFID desde Arduino.
    
    En modo debug (DEBUG_MODE=True), simula lecturas RFID aleatorias.
    """
    
    # Señales
    uid_received = Signal(str)          # UID de tarjeta leído
    connection_status = Signal(bool)    # Estado de conexión
    error_occurred = Signal(str)        # Error ocurrido
    
    def __init__(self, port: str = None, baudrate: int = None, parent=None):
        super().__init__(parent)
        
        self.port = port or SERIAL_PORT
        self.baudrate = baudrate or BAUDRATE
        self.timeout = SERIAL_TIMEOUT
        
        self._running = False
        self._serial = None
        self._debug_mode = DEBUG_MODE or not SERIAL_AVAILABLE
    
    @property
    def is_debug_mode(self) -> bool:
        """Indica si está en modo debug."""
        return self._debug_mode
    
    @property
    def is_connected(self) -> bool:
        """Indica si hay conexión serial activa."""
        return self._serial is not None and self._serial.is_open
    
    def set_debug_mode(self, enabled: bool):
        """
        Activa o desactiva el modo debug.
        
        Args:
            enabled: True para activar modo debug
        """
        self._debug_mode = enabled
    
    def set_port(self, port: str):
        """
        Cambia el puerto serial.
        
        Args:
            port: Nombre del puerto (ej: COM3)
        """
        was_running = self._running
        if was_running:
            self.stop()
            self.wait()
        
        self.port = port
        
        if was_running:
            self.start()
    
    @staticmethod
    def list_available_ports() -> list:
        """
        Lista los puertos seriales disponibles.
        
        Returns:
            Lista de tuplas (puerto, descripción)
        """
        if not SERIAL_AVAILABLE:
            return []
        
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, port.description))
        return ports
    
    def run(self):
        """Ejecuta el loop de escucha."""
        self._running = True
        
        if self._debug_mode:
            self._run_debug_mode()
        else:
            self._run_serial_mode()
    
    def _run_debug_mode(self):
        """Ejecuta en modo debug (simula lecturas RFID)."""
        self.connection_status.emit(True)
        
        while self._running:
            # Simular lectura cada DEBUG_RFID_INTERVAL segundos
            time.sleep(DEBUG_RFID_INTERVAL)
            
            if self._running:
                # Generar UID aleatorio (formato típico de tarjetas RFID)
                uid = self._generate_random_uid()
                self.uid_received.emit(uid)
        
        self.connection_status.emit(False)
    
    def _run_serial_mode(self):
        """Ejecuta en modo serial real."""
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.connection_status.emit(True)
            
            while self._running:
                try:
                    if self._serial.in_waiting > 0:
                        # Leer línea del Arduino
                        line = self._serial.readline().decode('utf-8').strip()
                        
                        if line:
                            # Emitir UID recibido
                            self.uid_received.emit(line)
                    else:
                        # Pequeña pausa para no saturar CPU
                        time.sleep(0.1)
                        
                except serial.SerialException as e:
                    self.error_occurred.emit(f"Error de lectura: {e}")
                    time.sleep(1)
                    
        except serial.SerialException as e:
            self.error_occurred.emit(f"No se pudo conectar al puerto {self.port}: {e}")
            self.connection_status.emit(False)
            
        finally:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self.connection_status.emit(False)
    
    def stop(self):
        """Detiene el listener."""
        self._running = False
    
    def _generate_random_uid(self) -> str:
        """
        Genera un UID aleatorio para modo debug.
        
        Returns:
            UID en formato hexadecimal
        """
        # Formato típico: 8 caracteres hexadecimales
        return ''.join(random.choices('0123456789ABCDEF', k=8))
    
    def send_test_uid(self, uid: str):
        """
        Envía un UID de prueba (solo para testing).
        
        Args:
            uid: UID a enviar
        """
        if self._running:
            self.uid_received.emit(uid)
    
    def send_open_door_command(self) -> bool:
        """
        Envía comando al Arduino para abrir la puerta manualmente.
        
        Returns:
            True si el comando fue enviado exitosamente
        """
        if self._debug_mode:
            # En modo debug, simular éxito
            return True
        
        if self._serial and self._serial.is_open:
            try:
                # Enviar comando "OPEN" al Arduino
                self._serial.write(b"OPEN\n")
                return True
            except Exception as e:
                self.error_occurred.emit(f"Error enviando comando: {e}")
                return False
        
        return False
