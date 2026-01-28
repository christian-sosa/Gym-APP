# BloomFitness - Documentación Técnica para Analítica

## Estructura de la Base de Datos

La base de datos es SQLite y se encuentra en: `data/gym_access.db`

---

## Tablas Disponibles

### 1. Tabla `users` (Usuarios/Miembros)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    celular VARCHAR(20),
    observaciones VARCHAR(500),
    plan VARCHAR(10) NOT NULL,           -- ENUM: MENSUAL, X3, X6
    fecha_inicio_plan DATE NOT NULL,
    fecha_fin_plan DATE NOT NULL,
    metodo_pago VARCHAR(15),             -- ENUM: EFECTIVO, TARJETA, MERCADOPAGO
    rfid_uid VARCHAR(50) UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);
```

| Campo | Tipo | Valores Posibles | Descripción |
|-------|------|------------------|-------------|
| id | INTEGER | Autoincremental | ID único del usuario |
| nombre | VARCHAR(50) | Texto | Nombre(s) del usuario |
| apellido | VARCHAR(50) | Texto | Apellido(s) del usuario |
| email | VARCHAR(100) | Texto o NULL | Correo electrónico |
| celular | VARCHAR(20) | Texto o NULL | Número de teléfono |
| observaciones | VARCHAR(500) | Texto o NULL | Notas adicionales |
| plan | VARCHAR(10) | MENSUAL, X3, X6 | Tipo de membresía |
| fecha_inicio_plan | DATE | YYYY-MM-DD | Inicio del plan actual |
| fecha_fin_plan | DATE | YYYY-MM-DD | Vencimiento del plan |
| metodo_pago | VARCHAR(15) | EFECTIVO, TARJETA, MERCADOPAGO | Forma de pago |
| rfid_uid | VARCHAR(50) | Texto o NULL | UID de tarjeta RFID |
| activo | BOOLEAN | 0 o 1 | Estado del usuario |
| created_at | DATETIME | ISO 8601 | Fecha de creación |
| updated_at | DATETIME | ISO 8601 | Última modificación |

### 2. Tabla `access_logs` (Registro de Accesos)

```sql
CREATE TABLE access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    rfid_uid VARCHAR(50) NOT NULL,
    user_id INTEGER,                     -- FK a users.id (puede ser NULL)
    resultado VARCHAR(10) NOT NULL,      -- ENUM: PERMITIDO, DENEGADO
    motivo VARCHAR(15) NOT NULL,         -- ENUM: OK, NO_EXISTE, VENCIDO, INACTIVO, MANUAL
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

| Campo | Tipo | Valores Posibles | Descripción |
|-------|------|------------------|-------------|
| id | INTEGER | Autoincremental | ID único del registro |
| timestamp | DATETIME | ISO 8601 | Fecha y hora del intento |
| rfid_uid | VARCHAR(50) | Texto | UID de tarjeta o "MANUAL-xxx" |
| user_id | INTEGER | ID o NULL | Usuario asociado (NULL si no existe) |
| resultado | VARCHAR(10) | PERMITIDO, DENEGADO | Resultado del acceso |
| motivo | VARCHAR(15) | OK, NO_EXISTE, VENCIDO, INACTIVO, MANUAL | Razón del resultado |

---

## Conexión a la Base de Datos

### Python (sqlite3)
```python
import sqlite3
from pathlib import Path

DB_PATH = Path("data/gym_access.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ejecutar consultas
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

conn.close()
```

### Python (pandas)
```python
import pandas as pd
import sqlite3

conn = sqlite3.connect("data/gym_access.db")

# Cargar tabla completa
df_users = pd.read_sql_query("SELECT * FROM users", conn)
df_access = pd.read_sql_query("SELECT * FROM access_logs", conn)

conn.close()
```

### DBeaver / SQL Client
1. Nueva conexión → SQLite
2. Archivo: `C:\...\BloomFitness\data\gym_access.db`
3. Conectar

---

## Consultas SQL Útiles para Analítica

### Usuarios

#### Total de usuarios por estado
```sql
SELECT 
    CASE WHEN activo = 1 THEN 'Activo' ELSE 'Inactivo' END as estado,
    COUNT(*) as cantidad
FROM users
GROUP BY activo;
```

#### Usuarios por tipo de plan
```sql
SELECT 
    plan,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users), 2) as porcentaje
FROM users
GROUP BY plan
ORDER BY cantidad DESC;
```

#### Usuarios por método de pago
```sql
SELECT 
    metodo_pago,
    COUNT(*) as cantidad
FROM users
WHERE activo = 1
GROUP BY metodo_pago;
```

#### Usuarios con plan por vencer (próximos 7 días)
```sql
SELECT 
    apellido || ', ' || nombre as usuario,
    email,
    celular,
    fecha_fin_plan,
    julianday(fecha_fin_plan) - julianday('now') as dias_restantes
FROM users
WHERE activo = 1
  AND fecha_fin_plan >= date('now')
  AND fecha_fin_plan <= date('now', '+7 days')
ORDER BY fecha_fin_plan;
```

#### Usuarios con plan vencido (aún activos)
```sql
SELECT 
    id,
    apellido || ', ' || nombre as usuario,
    fecha_fin_plan,
    julianday('now') - julianday(fecha_fin_plan) as dias_vencido
FROM users
WHERE activo = 1
  AND fecha_fin_plan < date('now')
ORDER BY fecha_fin_plan;
```

#### Nuevos usuarios por mes
```sql
SELECT 
    strftime('%Y-%m', created_at) as mes,
    COUNT(*) as nuevos_usuarios
FROM users
GROUP BY strftime('%Y-%m', created_at)
ORDER BY mes DESC;
```

### Accesos

#### Accesos por día
```sql
SELECT 
    date(timestamp) as fecha,
    COUNT(*) as total_accesos,
    SUM(CASE WHEN resultado = 'PERMITIDO' THEN 1 ELSE 0 END) as permitidos,
    SUM(CASE WHEN resultado = 'DENEGADO' THEN 1 ELSE 0 END) as denegados
FROM access_logs
GROUP BY date(timestamp)
ORDER BY fecha DESC;
```

#### Accesos por hora del día
```sql
SELECT 
    strftime('%H', timestamp) as hora,
    COUNT(*) as cantidad
FROM access_logs
WHERE resultado = 'PERMITIDO'
GROUP BY strftime('%H', timestamp)
ORDER BY hora;
```

#### Accesos por día de la semana
```sql
SELECT 
    CASE strftime('%w', timestamp)
        WHEN '0' THEN 'Domingo'
        WHEN '1' THEN 'Lunes'
        WHEN '2' THEN 'Martes'
        WHEN '3' THEN 'Miércoles'
        WHEN '4' THEN 'Jueves'
        WHEN '5' THEN 'Viernes'
        WHEN '6' THEN 'Sábado'
    END as dia_semana,
    COUNT(*) as cantidad
FROM access_logs
WHERE resultado = 'PERMITIDO'
GROUP BY strftime('%w', timestamp)
ORDER BY strftime('%w', timestamp);
```

#### Motivos de denegación
```sql
SELECT 
    motivo,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM access_logs WHERE resultado = 'DENEGADO'), 2) as porcentaje
FROM access_logs
WHERE resultado = 'DENEGADO'
GROUP BY motivo
ORDER BY cantidad DESC;
```

#### Usuarios más frecuentes (último mes)
```sql
SELECT 
    u.apellido || ', ' || u.nombre as usuario,
    COUNT(a.id) as visitas
FROM access_logs a
JOIN users u ON a.user_id = u.id
WHERE a.resultado = 'PERMITIDO'
  AND a.timestamp >= date('now', '-30 days')
GROUP BY a.user_id
ORDER BY visitas DESC
LIMIT 20;
```

#### Usuarios inactivos (sin accesos en 30 días)
```sql
SELECT 
    u.id,
    u.apellido || ', ' || u.nombre as usuario,
    u.email,
    u.fecha_fin_plan,
    MAX(a.timestamp) as ultimo_acceso,
    julianday('now') - julianday(MAX(a.timestamp)) as dias_sin_venir
FROM users u
LEFT JOIN access_logs a ON u.id = a.user_id AND a.resultado = 'PERMITIDO'
WHERE u.activo = 1
GROUP BY u.id
HAVING ultimo_acceso IS NULL 
   OR julianday('now') - julianday(MAX(a.timestamp)) > 30
ORDER BY dias_sin_venir DESC;
```

### Métricas Combinadas

#### Dashboard resumen
```sql
SELECT 
    (SELECT COUNT(*) FROM users WHERE activo = 1) as usuarios_activos,
    (SELECT COUNT(*) FROM users WHERE activo = 0) as usuarios_inactivos,
    (SELECT COUNT(*) FROM users WHERE activo = 1 AND fecha_fin_plan < date('now')) as planes_vencidos,
    (SELECT COUNT(*) FROM users WHERE activo = 1 AND fecha_fin_plan BETWEEN date('now') AND date('now', '+7 days')) as por_vencer_7d,
    (SELECT COUNT(*) FROM access_logs WHERE date(timestamp) = date('now')) as accesos_hoy,
    (SELECT COUNT(*) FROM access_logs WHERE timestamp >= date('now', '-30 days') AND resultado = 'PERMITIDO') as accesos_mes;
```

#### Tasa de retención mensual
```sql
WITH meses AS (
    SELECT DISTINCT strftime('%Y-%m', timestamp) as mes
    FROM access_logs
    ORDER BY mes DESC
    LIMIT 12
)
SELECT 
    m.mes,
    COUNT(DISTINCT a.user_id) as usuarios_unicos
FROM meses m
LEFT JOIN access_logs a ON strftime('%Y-%m', a.timestamp) = m.mes
    AND a.resultado = 'PERMITIDO'
GROUP BY m.mes
ORDER BY m.mes;
```

---

## Exportación de Datos

### Script ETL incluido
El proyecto incluye un script para exportar datos a CSV:

```bash
python etl/extract_to_csv.py
```

Genera archivos en `etl/output/`:
- `usuarios_YYYYMMDD_HHMMSS.csv`
- `accesos_YYYYMMDD_HHMMSS.csv`
- `estadisticas_YYYYMMDD_HHMMSS.csv`

### Exportación manual con Python
```python
import pandas as pd
import sqlite3

conn = sqlite3.connect("data/gym_access.db")

# Exportar usuarios
df_users = pd.read_sql_query("SELECT * FROM users", conn)
df_users.to_csv("usuarios_export.csv", index=False, encoding='utf-8')

# Exportar accesos con nombre de usuario
query = """
SELECT 
    a.timestamp,
    a.rfid_uid,
    u.apellido || ', ' || u.nombre as usuario,
    a.resultado,
    a.motivo
FROM access_logs a
LEFT JOIN users u ON a.user_id = u.id
ORDER BY a.timestamp DESC
"""
df_access = pd.read_sql_query(query, conn)
df_access.to_csv("accesos_export.csv", index=False, encoding='utf-8')

conn.close()
```

---

## Consideraciones para Analítica

### Campos Calculados Útiles

| Métrica | Fórmula SQL |
|---------|-------------|
| Días restantes de plan | `julianday(fecha_fin_plan) - julianday('now')` |
| Días como miembro | `julianday('now') - julianday(created_at)` |
| Plan vigente | `fecha_fin_plan >= date('now')` |
| Antigüedad en meses | `(julianday('now') - julianday(created_at)) / 30` |

### Valores de Enums

**plan:**
- `MENSUAL` = Plan mensual (1 mes)
- `X3` = Plan trimestral (3 meses)
- `X6` = Plan semestral (6 meses)

**metodo_pago:**
- `EFECTIVO` = Pago en efectivo
- `TARJETA` = Tarjeta de débito/crédito
- `MERCADOPAGO` = Pago digital MercadoPago

**resultado:**
- `PERMITIDO` = Acceso concedido
- `DENEGADO` = Acceso rechazado

**motivo:**
- `OK` = Acceso válido
- `NO_EXISTE` = Tarjeta no registrada
- `VENCIDO` = Plan expirado
- `INACTIVO` = Usuario deshabilitado
- `MANUAL` = Apertura manual (visitante)

### Registros Especiales

- **Accesos manuales**: `rfid_uid` comienza con "MANUAL-"
- **Usuarios sin tarjeta**: `rfid_uid` es NULL
- **Accesos sin usuario**: `user_id` es NULL (tarjeta no registrada)

---

## Integración con Herramientas de BI

### Power BI
1. Obtener datos → SQLite
2. Instalar conector SQLite (si no está)
3. Seleccionar archivo `gym_access.db`
4. Importar tablas `users` y `access_logs`
5. Crear relación: `access_logs.user_id` → `users.id`

### Metabase
1. Agregar base de datos → SQLite
2. Path: `/path/to/gym_access.db`
3. Las tablas aparecerán automáticamente

### Google Sheets (via CSV)
1. Ejecutar `python etl/extract_to_csv.py`
2. Subir CSVs a Google Drive
3. Abrir con Google Sheets
4. Usar IMPORTRANGE para conectar hojas

### Python + Jupyter
```python
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

conn = sqlite3.connect("data/gym_access.db")

# Análisis de accesos por hora
df = pd.read_sql_query("""
    SELECT strftime('%H', timestamp) as hora, COUNT(*) as cantidad
    FROM access_logs WHERE resultado = 'PERMITIDO'
    GROUP BY hora
""", conn)

df.plot(x='hora', y='cantidad', kind='bar', title='Accesos por Hora')
plt.show()
```

---

## Backup y Seguridad

### Backup de la base de datos
```bash
# Windows (PowerShell)
Copy-Item "data\gym_access.db" "backup\gym_access_$(Get-Date -Format 'yyyyMMdd').db"

# O simplemente copiar el archivo gym_access.db
```

### Restaurar backup
1. Cerrar BloomFitness
2. Reemplazar `data/gym_access.db` con el backup
3. Abrir BloomFitness

---

*Documentación técnica actualizada: Enero 2026*
