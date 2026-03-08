# ETL - Extracción y Migración de Datos BloomFitness

Scripts para extraer datos de la base de datos SQLite, exportarlos a CSV y migrar desde el sistema anterior.

## Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `extract_to_csv.py` | Exporta usuarios, accesos y estadísticas a CSV |
| `migrate_from_old_db.py` | Migra datos desde la base de datos del sistema anterior (Java) |

## Extracción a CSV

```bash
# Desde la carpeta raíz del proyecto
python etl/extract_to_csv.py
```

### Archivos Generados

Los archivos CSV se generan en `etl/output/` con timestamp:

- `usuarios_YYYYMMDD_HHMMSS.csv` - Lista completa de usuarios
- `accesos_YYYYMMDD_HHMMSS.csv` - Historial de accesos
- `estadisticas_YYYYMMDD_HHMMSS.csv` - Métricas resumidas

### Exportación desde la app

La vista "Registro Accesos" incluye un botón "Exportar CSV" que permite exportar directamente el historial filtrado sin necesidad de usar estos scripts.

## Migración desde Sistema Anterior

```bash
# Colocar gym_to_migrate.db en la raíz del proyecto
# Ejecutar la app una vez para crear data/gym_access.db con tablas
python main.py
# Luego migrar
python etl/migrate_from_old_db.py
```

Ver [DESPLIEGUE_PRODUCCION.md](../docs/DESPLIEGUE_PRODUCCION.md) para instrucciones detalladas.

## Consultar con DBeaver

Para abrir la base de datos con DBeaver u otro cliente SQL:

1. Abrir DBeaver
2. Nueva Conexión -> SQLite
3. Ruta del archivo: `BloomFitness/data/gym_access.db`
4. Conectar

### Queries de Ejemplo

```sql
-- Ver todos los usuarios activos
SELECT * FROM users WHERE activo = 1;

-- Usuarios con plan vencido
SELECT nombre, apellido, plan, fecha_fin_plan 
FROM users 
WHERE fecha_fin_plan < date('now') AND activo = 1;

-- Accesos del último mes
SELECT a.*, u.nombre, u.apellido
FROM access_logs a
LEFT JOIN users u ON a.user_id = u.id
WHERE a.timestamp >= datetime('now', '-30 days')
ORDER BY a.timestamp DESC;

-- Estadísticas por día
SELECT 
    date(timestamp) as fecha,
    COUNT(*) as total,
    SUM(CASE WHEN resultado = 'PERMITIDO' THEN 1 ELSE 0 END) as permitidos,
    SUM(CASE WHEN resultado = 'DENEGADO' THEN 1 ELSE 0 END) as denegados
FROM access_logs
GROUP BY date(timestamp)
ORDER BY fecha DESC;
```

Ver [ANALITICA_DATOS.md](../docs/ANALITICA_DATOS.md) para consultas avanzadas de analítica.

## Estructura de la Base de Datos

### Tabla `users`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | ID único autoincremental |
| nombre | VARCHAR(50) | Nombre del usuario |
| apellido | VARCHAR(50) | Apellido del usuario |
| email | VARCHAR(100) | Email (opcional) |
| celular | VARCHAR(20) | Celular (opcional) |
| observaciones | VARCHAR(500) | Notas médicas, etc. |
| plan | ENUM | MENSUAL, X3, X6 |
| fecha_inicio_plan | DATE | Inicio de la membresía |
| fecha_fin_plan | DATE | Vencimiento de la membresía |
| metodo_pago | ENUM | EFECTIVO, TARJETA, MERCADOPAGO |
| rfid_uid | VARCHAR(50) | UID de tarjeta RFID |
| activo | BOOLEAN | Estado del usuario |
| created_at | DATETIME | Fecha de creación |
| updated_at | DATETIME | Última modificación |

### Tabla `access_logs`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | ID único autoincremental |
| timestamp | DATETIME | Fecha y hora del acceso |
| rfid_uid | VARCHAR(50) | UID de la tarjeta usada |
| user_id | INTEGER | FK al usuario (puede ser NULL) |
| resultado | ENUM | PERMITIDO, DENEGADO |
| motivo | ENUM | OK, NO_EXISTE, VENCIDO, INACTIVO, MANUAL |
