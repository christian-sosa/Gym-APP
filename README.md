# BloomFitness - Sistema de Control de Acceso para Gimnasio

Sistema de escritorio para gestión de usuarios, membresías y control de acceso mediante tarjetas RFID conectadas vía Arduino.

## Características

- **Gestión de Usuarios**: Alta, baja, modificación y búsqueda de miembros
- **Planes de Membresía**: Mensual, 3 meses y 6 meses con cálculo automático de vencimiento
- **Tarjetas RFID**: Asignación y gestión de tarjetas para control de acceso
- **Registro de Accesos**: Historial completo con exportación a CSV
- **Comunicación Arduino**: Lectura de tarjetas RFID vía puerto serial
- **Modo Debug**: Simulación de lecturas RFID sin hardware

## Requisitos del Sistema

- Windows 10/11
- Python 3.11 o superior (solo para desarrollo)
- Arduino con lector RFID RC522 (opcional para modo debug)

## Instalación para Desarrollo

### 1. Clonar o descargar el proyecto

```bash
cd BloomFitness
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
python main.py
```

## Modo Debug (Sin Arduino)

Para probar la aplicación sin un Arduino conectado, active el modo debug:

### Opción 1: Variable de entorno

```bash
set BLOOM_DEBUG=1
python main.py
```

### Opción 2: Desde la interfaz

1. Abra la aplicación
2. Vaya a "Tarjetas RFID"
3. Active el botón "Modo Debug: OFF" para cambiar a "ON"
4. El sistema simulará lecturas de tarjetas aleatorias cada 5 segundos

## Configuración del Puerto Serial

Por defecto, la aplicación busca el Arduino en `COM3`. Para cambiar el puerto:

1. Edite el archivo `src/config.py`
2. Modifique la línea:
   ```python
   SERIAL_PORT = "COM3"  # Cambiar al puerto correspondiente
   ```

También puede seleccionar el puerto desde la interfaz en la sección "Tarjetas RFID".

## Generar Ejecutable (.exe)

### Opción 1: Usar el script de build

```bash
build.bat
```

### Opción 2: Comando manual

```bash
pyinstaller BloomFitness.spec
```

El ejecutable se generará en `dist/BloomFitness.exe`.

## Estructura del Proyecto

```
BloomFitness/
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias Python
├── BloomFitness.spec       # Configuración PyInstaller
├── build.bat               # Script de build
├── README.md               # Este archivo
│
├── src/
│   ├── config.py           # Configuración global
│   │
│   ├── db/                 # Base de datos
│   │   ├── models.py       # Modelos SQLAlchemy
│   │   ├── database.py     # Conexión SQLite
│   │   └── repository.py   # Operaciones CRUD
│   │
│   ├── ui/                 # Interfaz gráfica
│   │   ├── main_window.py  # Ventana principal
│   │   ├── views/          # Vistas (usuarios, RFID, accesos)
│   │   ├── dialogs/        # Diálogos modales
│   │   ├── widgets/        # Componentes reutilizables
│   │   └── styles/         # Tema oscuro QSS
│   │
│   ├── services/           # Lógica de negocio
│   │   ├── rfid_listener.py    # Comunicación serial
│   │   ├── access_control.py   # Control de acceso
│   │   └── plan_calculator.py  # Cálculo de planes
│   │
│   └── utils/              # Utilidades
│       ├── enums.py        # Enumeraciones
│       ├── dates.py        # Manejo de fechas
│       └── export.py       # Exportación CSV
│
├── assets/                 # Recursos (logo, iconos)
│
└── data/                   # Base de datos SQLite
    └── gym_access.db       # (generado automáticamente)
```

## Código Arduino (Ejemplo)

```cpp
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
}

void loop() {
  // Verificar si hay una tarjeta presente
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Construir UID como string hexadecimal
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  // Enviar UID por Serial
  Serial.println(uid);

  // Evitar lecturas duplicadas
  delay(1000);

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}
```

### Conexiones del Arduino

| RC522 | Arduino Uno |
|-------|-------------|
| SDA   | Pin 10      |
| SCK   | Pin 13      |
| MOSI  | Pin 11      |
| MISO  | Pin 12      |
| IRQ   | No conectar |
| GND   | GND         |
| RST   | Pin 9       |
| 3.3V  | 3.3V        |

## Base de Datos

La aplicación utiliza SQLite. La base de datos se crea automáticamente en `data/gym_access.db`.

### Tablas

**users**
- id, nombre, email, celular, observaciones
- plan (mensual/x3/x6)
- fecha_inicio_plan, fecha_fin_plan
- rfid_uid, activo
- created_at, updated_at

**access_logs**
- id, timestamp
- rfid_uid, user_id
- resultado (permitido/denegado)
- motivo (ok/no_existe/vencido/inactivo)

## Solución de Problemas

### La aplicación no detecta el Arduino

1. Verifique que el Arduino esté conectado
2. Compruebe el puerto COM en el Administrador de dispositivos
3. Actualice el puerto en `src/config.py` o en la interfaz

### Error al generar ejecutable

1. Asegúrese de tener todas las dependencias instaladas
2. Ejecute como administrador si hay problemas de permisos
3. Verifique que no haya antivirus bloqueando PyInstaller

### La base de datos no se crea

1. Verifique permisos de escritura en el directorio
2. Compruebe que el directorio `data/` existe

## Licencia

Este proyecto es de uso privado para el gimnasio BloomFitness.

## Contacto

Para soporte técnico o consultas sobre el sistema, contacte al desarrollador.
