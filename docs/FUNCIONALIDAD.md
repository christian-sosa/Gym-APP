# BloomFitness - Documentación Funcional

## Descripción General

BloomFitness es una aplicación de escritorio para Windows que gestiona el control de acceso de un gimnasio mediante tarjetas RFID conectadas a un Arduino.

---

## QUÉ HACE EL SOFTWARE

### 1. Gestión de Usuarios (Miembros del Gimnasio)

| Funcionalidad | Descripción |
|---------------|-------------|
| **Listar usuarios** | Muestra todos los miembros en una tabla ordenada por apellido |
| **Agregar usuario** | Formulario para registrar nuevos miembros |
| **Editar usuario** | Modificar datos de un miembro existente (se habilita al seleccionar exactamente uno) |
| **Eliminar usuario** | Eliminar uno o varios miembros seleccionados (texto del botón se adapta a la cantidad) |
| **Ver usuario (solo lectura)** | Doble click muestra información sin permitir edición |
| **Buscar/Filtrar** | Por apellido, nombre, email, celular, plan, observaciones |
| **Filtrar activos/inactivos** | Botones para mostrar/ocultar según estado |
| **Contador de usuarios** | Muestra el total de usuarios visibles |
| **Estado vacío** | Mensaje claro cuando no hay resultados en la tabla |

### 2. Datos de Cada Usuario

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| Apellido | Texto | Sí | Apellido del miembro |
| Nombre | Texto | Sí | Nombre del miembro |
| Email | Texto | No | Correo electrónico |
| Celular | Texto | No | Número de teléfono |
| Observaciones | Texto largo | No | Notas médicas, restricciones, etc. |
| Plan | Selección | Sí | Mensual, 3 Meses, 6 Meses |
| Fecha Inicio | Fecha | Sí | Inicio del plan actual |
| Fecha Fin | Fecha | Automático | Calculada según el plan |
| Método de Pago | Selección | Sí | Efectivo, Tarjeta, MercadoPago |
| Estado | Checkbox | Sí | Activo / Inactivo |
| Tarjeta RFID | Texto | No | UID de la tarjeta asignada |

### 3. Gestión de Planes/Membresías

| Funcionalidad | Descripción |
|---------------|-------------|
| **Cálculo automático de vencimiento** | Al seleccionar plan, calcula fecha fin automáticamente |
| **Verificación de vencimiento al iniciar** | Al abrir la app, desactiva usuarios con plan vencido |
| **Indicadores visuales** | Colores en la tabla: verde (vigente), naranja (por vencer en 7 días), rojo (vencido) |

**Tipos de planes disponibles:**
- **Mensual**: +1 mes desde fecha inicio
- **3 Meses**: +3 meses desde fecha inicio
- **6 Meses**: +6 meses desde fecha inicio

### 4. Control de Acceso RFID

| Funcionalidad | Descripción |
|---------------|-------------|
| **Lectura de tarjetas** | Escucha el puerto serial (Arduino) para detectar UIDs |
| **Validación de acceso** | Verifica si el usuario existe, está activo y tiene plan vigente |
| **Registro de eventos** | Guarda cada intento de acceso (permitido/denegado) |
| **Log en tiempo real** | Muestra las últimas lecturas en pantalla |
| **Apertura manual** | Botón para abrir puerta sin tarjeta (visitantes), con feedback visual transitorio |
| **Modo debug** | Simula lecturas RFID sin hardware conectado (estilo visual controlado por QSS) |
| **Asignación de tarjetas** | Selector explícito de usuario antes de escanear la tarjeta |
| **Estado vacío** | Mensaje claro si no hay tarjetas asignadas |

**Resultados posibles de acceso:**
| Resultado | Motivo | Descripción |
|-----------|--------|-------------|
| PERMITIDO | OK | Usuario activo con plan vigente |
| DENEGADO | NO_EXISTE | Tarjeta no registrada en el sistema |
| DENEGADO | VENCIDO | Usuario tiene plan vencido |
| DENEGADO | INACTIVO | Usuario marcado como inactivo |
| PERMITIDO | MANUAL | Apertura manual para visitante |

### 5. Registro de Accesos

| Funcionalidad | Descripción |
|---------------|-------------|
| **Historial de accesos** | Tabla con todos los intentos de ingreso |
| **Filtros** | Por rango de fechas, resultado (permitido/denegado), UID RFID |
| **Estadísticas dinámicas** | Panel con título que refleja el período seleccionado ("del Día" o "del Período dd/MM - dd/MM") |
| **Exportar a CSV** | Descargar el historial filtrado para análisis externo |
| **Estado vacío** | Mensaje claro si no hay registros para el período y filtros seleccionados |

### 6. Backup de Base de Datos

| Funcionalidad | Descripción |
|---------------|-------------|
| **Botón en sidebar** | Ubicado debajo de "Registro Accesos", con color diferenciado (azul) |
| **Backup diario** | Crea `data/yyyy-mm-dd/gym_access.db` con la fecha del día |
| **Sobrescritura** | Un solo archivo por día; si ya existe, se reemplaza |
| **Feedback** | Mensaje emergente indicando éxito (con ruta) o error |

### 7. Comunicación con Arduino

| Configuración | Valor por defecto |
|---------------|-------------------|
| Puerto serial | COM3 |
| Baudrate | 9600 |
| Timeout | 1 segundo |

**Comandos:**
- Arduino -> PC: Envía UID de tarjeta como texto (ej: "A1B2C3D4")
- PC -> Arduino: Envía "OPEN\n" para abrir puerta manualmente

### 8. Navegación e Interfaz

| Funcionalidad | Descripción |
|---------------|-------------|
| **Sidebar con constantes** | Navegación interna usa constantes (VIEW_USUARIOS, VIEW_TARJETAS, VIEW_ACCESOS) en lugar de índices mágicos |
| **Sincronización sidebar** | `show_view()` actualiza automáticamente el botón activo del sidebar |
| **Tooltips** | Todos los botones principales tienen tooltips descriptivos |
| **Estilos centralizados** | Tema oscuro consolidado en `dark_theme.qss`; botones especiales (backup, debug, apertura de puerta) usan propiedades QSS en vez de estilos inline |
| **Botones contextuales** | El botón "Editar" se habilita/deshabilita según selección; "Eliminar" ajusta su texto según cantidad seleccionada |

---

## QUÉ NO HACE EL SOFTWARE

### Funcionalidades NO Incluidas

| Funcionalidad | Estado |
|---------------|--------|
| **Gestión de pagos/cobros** | No incluido - Solo registra método de pago |
| **Facturación/Recibos** | No incluido |
| **Control de asistencia por día** | No incluido - Solo registra acceso |
| **Límite de días por semana** | No incluido (existía en sistema anterior) |
| **Reserva de clases/turnos** | No incluido |
| **Gestión de empleados** | No incluido |
| **Múltiples sucursales** | No incluido - Una sola ubicación |
| **Sincronización en la nube** | No incluido - Solo local |
| **Notificaciones/Alertas** | No incluido - No envía emails ni SMS |
| **Reportes gráficos** | No incluido - Datos crudos disponibles para BI externo |
| **Control de inventario** | No incluido |
| **Gestión de rutinas/ejercicios** | No incluido |

### Limitaciones Técnicas

| Limitación | Descripción |
|------------|-------------|
| **Solo Windows** | No compatible con Mac o Linux |
| **Base de datos local** | SQLite, no se sincroniza entre PCs |
| **Un solo lector RFID** | No soporta múltiples puertas/lectores |
| **Sin autenticación** | Cualquiera con acceso al .exe puede usarlo |
| **Sin auditoría de cambios** | No registra quién modificó qué |
| **Backup manual** | El backup se dispara con el botón; no hay programación automática |

### Diferencias con Sistema Anterior (Java)

| Característica | Sistema Anterior | BloomFitness |
|----------------|------------------|--------------|
| Plan "std" (3 días/semana) | Sí | No - Migrado como mensual |
| Control de uso semanal | Sí | No |
| Interfaz | Java Swing | PySide6 (Qt) |
| Ejecutable | Requiere Java | .exe independiente |
| Backup | Manual (copiar archivo) | Botón integrado en la app |

---

## Flujo de Trabajo Típico

### Alta de Nuevo Miembro
1. Ir a "Usuarios" -> "Agregar Usuario"
2. Completar apellido, nombre y datos de contacto
3. Seleccionar plan (Mensual/3 Meses/6 Meses)
4. Fecha inicio se pone automáticamente como hoy
5. Seleccionar método de pago
6. (Opcional) Asignar tarjeta RFID escaneando
7. Guardar

### Renovación de Plan
1. Buscar usuario en la lista
2. Seleccionar -> "Editar Usuario"
3. Cambiar fecha de inicio a la fecha de renovación
4. El sistema calcula nueva fecha de fin
5. Guardar

### Consulta de Accesos
1. Ir a "Registro Accesos"
2. Aplicar filtros de fecha si es necesario
3. Ver historial de ingresos y estadísticas del período
4. Exportar a CSV si se requiere análisis

### Backup de la Base de Datos
1. Presionar el botón "Backup DB" en la barra lateral
2. Se crea la copia en `data/yyyy-mm-dd/gym_access.db`
3. Se muestra mensaje con la ruta del respaldo

---

## Arquitectura del Sistema

```
+------------------+     +------------------+     +------------------+
|   Arduino +      |---->|   BloomFitness   |---->|   SQLite DB      |
|   Lector RFID    |     |   (Python/Qt)    |     |   (Local)        |
+------------------+     +------------------+     +------------------+
                                |                         |
                                v                         v
                         +------------------+     +------------------+
                         |   Cerradura      |     |   Backups        |
                         |   Eléctrica      |     |   data/yyyy-mm-dd|
                         +------------------+     +------------------+
```

---

## Archivos Importantes

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| BloomFitness.exe | Carpeta principal | Ejecutable de la aplicación |
| gym_access.db | data/ | Base de datos SQLite |
| logo.png | assets/ o junto al .exe | Logo del gimnasio (opcional) |
| dark_theme.qss | src/ui/styles/ | Tema visual centralizado |
| backup_service.py | src/services/ | Lógica de respaldo diario |

---

*Documentación actualizada: Marzo 2026*
