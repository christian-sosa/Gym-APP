"""
Listener para lectura de tarjetas RFID vía puerto serial (Arduino).
"""
import time
import random
from threading import RLock

from PySide6.QtCore import QThread, Signal

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from src.config import SERIAL_PORT, BAUDRATE, SERIAL_TIMEOUT, DEBUG_MODE, DEBUG_RFID_INTERVAL
from src.utils.rfid import normalize_rfid_uid


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
        self._serial_lock = RLock()
        self._last_error = ""
        # Solo activar debug por configuración explícita.
        # Si pyserial no está disponible, se emitirá un error claro.
        self._debug_mode = DEBUG_MODE
    
    @property
    def is_debug_mode(self) -> bool:
        """Indica si está en modo debug."""
        return self._debug_mode
    
    @property
    def is_connected(self) -> bool:
        """Indica si hay conexión serial activa."""
        with self._serial_lock:
            return self._serial is not None and self._serial.is_open

    @property
    def last_error(self) -> str:
        """Último error serial registrado."""
        return self._last_error

    def _emit_error(self, message: str):
        """Guarda y emite un error al frontend."""
        self._last_error = message
        self.error_occurred.emit(message)
    
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
        was_running = self.isRunning()
        if was_running:
            self.stop()
            self.wait()
        
        self.port = port
        
        # Reiniciar el listener al cambiar puerto para forzar reconexión.
        if not self.isRunning():
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
        
        self._running = False
    
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
            while self._running:
                # Si no hay conexión activa, intentar reconectar periódicamente.
                if not self.is_connected:
                    if not self._open_serial_connection():
                        time.sleep(2)
                        continue
                    self.connection_status.emit(True)

                try:
                    line = None
                    with self._serial_lock:
                        if self._serial and self._serial.is_open and self._serial.in_waiting > 0:
                            # Leer línea del Arduino
                            line = self._serial.readline().decode('utf-8', errors='ignore').strip()

                    if line:
                        uid = normalize_rfid_uid(line)
                        if uid:
                            # Emitir UID recibido en formato canonico
                            self.uid_received.emit(uid)
                    else:
                        # Pequeña pausa para no saturar CPU
                        time.sleep(0.1)
                        
                except serial.SerialException as e:
                    self._emit_error(f"Error de lectura: {e}")
                    with self._serial_lock:
                        if self._serial and self._serial.is_open:
                            self._serial.close()
                        self._serial = None
                    self.connection_status.emit(False)
                    time.sleep(1)
                    
        finally:
            with self._serial_lock:
                if self._serial and self._serial.is_open:
                    self._serial.close()
                self._serial = None
            self.connection_status.emit(False)

    def _open_serial_connection(self) -> bool:
        """
        Intenta abrir una conexión serial con el Arduino.

        Primero prueba el puerto configurado; si falla, recorre los demás puertos
        disponibles hasta encontrar uno válido.

        Returns:
            True si se abrió una conexión, False en caso contrario.
        """
        if not SERIAL_AVAILABLE:
            self._emit_error("PySerial no está disponible. Instale 'pyserial' para usar el lector RFID.")
            self.connection_status.emit(False)
            return False

        ports_to_try = []

        # Priorizar el puerto configurado explícitamente
        if self.port:
            ports_to_try.append(self.port)

        # Agregar puertos disponibles, priorizando dispositivos Arduino/USB serial
        available_ports = list(serial.tools.list_ports.comports())
        preferred_ports = []
        other_ports = []
        keywords = ("arduino", "ch340", "cp210", "usb serial", "usb-serial", "ttyacm", "ttyusb")

        for p in available_ports:
            description = (p.description or "").lower()
            manufacturer = (p.manufacturer or "").lower()
            hwid = (p.hwid or "").lower()
            is_preferred = any(k in description or k in manufacturer or k in hwid for k in keywords)

            if is_preferred:
                preferred_ports.append(p.device)
            else:
                other_ports.append(p.device)

        for port in preferred_ports + other_ports:
            if port not in ports_to_try:
                ports_to_try.append(port)

        if not ports_to_try:
            self._emit_error(
                "No se detectaron puertos seriales. Verifique cable USB de datos y driver del Arduino (CH340/CP210x)."
            )
            self.connection_status.emit(False)
            return False

        last_error = None

        for port in ports_to_try:
            try:
                with self._serial_lock:
                    self._serial = serial.Serial(
                        port=port,
                        baudrate=self.baudrate,
                        timeout=self.timeout,
                        write_timeout=1,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        xonxoff=False,
                        rtscts=False,
                        dsrdtr=False,
                        exclusive=False,  # Permitir que Windows no bloquee el puerto en modo exclusivo
                    )

                # Guardar el puerto efectivo y dar tiempo a que el Arduino se reinicie
                self.port = port
                time.sleep(2)

                self._emit_error(f"Conectado al puerto {port} @ {self.baudrate} baudios")
                self.connection_status.emit(True)
                return True
            except (serial.SerialException, PermissionError) as e:
                last_error = e
                continue

        # Si llegamos aquí, no se pudo abrir ningún puerto
        if last_error:
            self._emit_error(
                f"No se pudo abrir ningún puerto serial (probados: {', '.join(ports_to_try)}). "
                f"Último error: {last_error}"
            )
        else:
            self._emit_error("No se encontraron puertos seriales disponibles.")

        self.connection_status.emit(False)
        return False
    
    def stop(self):
        """Detiene el listener."""
        self._running = False
    
    def _generate_random_uid(self) -> str:
        """
        Genera un UID aleatorio para modo debug.
        
        Returns:
            UID en formato hexadecimal
        """
        # Formato canonico: 4 bytes separados por guion
        raw = ''.join(random.choices('0123456789ABCDEF', k=8))
        return "-".join(raw[i:i + 2] for i in range(0, len(raw), 2))
    
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

        if not SERIAL_AVAILABLE:
            self._emit_error("No se puede enviar OPEN: pyserial no está disponible.")
            return False

        # Si no hay conexión activa, intentar reconectar automáticamente.
        if not self.is_connected and not self._open_serial_connection():
            self._emit_error("No se pudo reconectar el puerto serial para enviar OPEN.")
            return False

        try:
            with self._serial_lock:
                if not self._serial or not self._serial.is_open:
                    self._emit_error("Puerto serial no conectado.")
                    return False

                # Enviar comando "OPEN" al Arduino
                self._serial.write(b"OPEN\n")
                self._serial.flush()
                return True
        except Exception as e:
            self._emit_error(f"Error enviando comando OPEN: {e}")
            return False
