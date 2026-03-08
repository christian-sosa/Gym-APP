# BloomFitness - Sistema de Control de Acceso para Gimnasio

Sistema de escritorio para gestión de usuarios, membresías y control de acceso mediante tarjetas RFID conectadas vía Arduino.

## Características

- **Gestión de Usuarios**: Alta, baja, modificación y búsqueda de miembros con filtros avanzados
- **Planes de Membresía**: Mensual, 3 meses y 6 meses con cálculo automático de vencimiento
- **Tarjetas RFID**: Asignación (con selección explícita de usuario) y gestión de tarjetas
- **Registro de Accesos**: Historial completo con estadísticas del período y exportación a CSV
- **Comunicación Arduino**: Lectura de tarjetas RFID vía puerto serial
- **Modo Debug**: Simulación de lecturas RFID sin hardware
- **Backup Diario**: Respaldo de la base de datos con un clic (un backup por día en `data/yyyy-mm-dd/`)
- **Tema Oscuro**: Interfaz con tema oscuro consolidado vía QSS

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

## Backup de la Base de Datos

La aplicación incluye un botón de backup en la barra lateral (sidebar). Al presionarlo:

- Se crea una copia de `data/gym_access.db` en `data/yyyy-mm-dd/gym_access.db`.
- Solo se mantiene un archivo por día; si ya existe, se sobrescribe.
- Se muestra un mensaje con la ruta del backup o el error encontrado.

Para restaurar un backup, cierre la aplicación y reemplace `data/gym_access.db` con el archivo de respaldo deseado.

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

### Estructura en producción (compilado)

```
bloom/
├── BloomFitness.exe
├── logo/
│   └── logo.png
└── data/
    ├── gym_access.db
    └── 2026-03-08/          (backups diarios)
        └── gym_access.db
```

## Estructura del Proyecto

```
BloomFitness/
├── main.py                     # Punto de entrada
├── requirements.txt            # Dependencias Python
├── BloomFitness.spec           # Configuración PyInstaller
├── build.bat                   # Script de build
├── README.md                   # Este archivo
│
├── src/
│   ├── config.py               # Configuración global (rutas, puertos, constantes)
│   │
│   ├── db/                     # Base de datos
│   │   ├── models.py           # Modelos SQLAlchemy (User, AccessLog)
│   │   ├── database.py         # Conexión y sesión SQLite
│   │   └── repository.py       # Operaciones CRUD
│   │
│   ├── ui/                     # Interfaz gráfica (PySide6 / Qt)
│   │   ├── main_window.py      # Ventana principal y navegación
│   │   ├── views/              # Vistas principales
│   │   │   ├── users_view.py       # Gestión de usuarios
│   │   │   ├── rfid_view.py        # Tarjetas RFID y control de acceso
│   │   │   └── access_log_view.py  # Registro de accesos
│   │   ├── dialogs/            # Diálogos modales
│   │   │   ├── user_dialog.py       # Alta/edición de usuario
│   │   │   └── rfid_assign_dialog.py # Asignación de tarjeta RFID
│   │   ├── widgets/            # Componentes reutilizables
│   │   │   ├── sidebar.py          # Barra lateral de navegación
│   │   │   └── search_bar.py       # Barra de búsqueda con filtros
│   │   └── styles/
│   │       └── dark_theme.qss  # Tema oscuro centralizado
│   │
│   ├── services/               # Lógica de negocio
│   │   ├── rfid_listener.py    # Comunicación serial con Arduino
│   │   ├── access_control.py   # Validación de acceso
│   │   ├── plan_calculator.py  # Cálculo de fechas de planes
│   │   └── backup_service.py   # Backup diario de la base de datos
│   │
│   └── utils/                  # Utilidades
│       ├── enums.py            # Enumeraciones (PlanType, AccessResult, etc.)
│       ├── dates.py            # Formateo de fechas
│       └── export.py           # Exportación a CSV
│
├── assets/                     # Recursos (logo, iconos)
│
├── data/                       # Base de datos SQLite (generado automáticamente)
│   └── gym_access.db
│
├── docs/                       # Documentación adicional
│   ├── FUNCIONALIDAD.md        # Qué hace y qué no hace el software
│   ├── DESPLIEGUE_PRODUCCION.md # Guía de despliegue
│   └── ANALITICA_DATOS.md      # Consultas SQL y conexión a BI
│
└── etl/                        # Scripts de extracción y migración
    ├── README.md
    ├── extract_to_csv.py       # Exporta datos a CSV
    └── migrate_from_old_db.py  # Migración desde sistema anterior (Java)
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
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  Serial.println(uid);

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
- id, nombre, apellido, email, celular, observaciones
- plan (mensual/x3/x6), metodo_pago
- fecha_inicio_plan, fecha_fin_plan
- rfid_uid, activo
- created_at, updated_at

**access_logs**
- id, timestamp
- rfid_uid, user_id
- resultado (permitido/denegado)
- motivo (ok/no_existe/vencido/inactivo/manual)

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
2. Compruebe que el directorio `data/` existe (se crea automáticamente)

## Licencia

Este proyecto es de uso privado para el gimnasio BloomFitness.

## Contacto

Para soporte técnico o consultas sobre el sistema, contacte al desarrollador.
