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
| **Editar usuario** | Modificar datos de un miembro existente |
| **Eliminar usuario** | Eliminar uno o varios miembros seleccionados |
| **Ver usuario (solo lectura)** | Doble click muestra información sin permitir edición |
| **Buscar/Filtrar** | Por apellido, nombre, email, celular, plan, observaciones |
| **Filtrar activos/inactivos** | Botones para mostrar/ocultar según estado |
| **Contador de usuarios** | Muestra el total de usuarios visibles |

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
| **Indicadores visuales** | Colores en la tabla: verde (vigente), naranja (por vencer), rojo (vencido) |

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
| **Apertura manual** | Botón para abrir puerta sin tarjeta (visitantes) |
| **Modo debug** | Simula lecturas RFID sin hardware conectado |

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
| **Filtros** | Por fecha, resultado (permitido/denegado), usuario |
| **Exportar a CSV** | Descargar el historial para análisis externo |

### 6. Comunicación con Arduino

| Configuración | Valor por defecto |
|---------------|-------------------|
| Puerto serial | COM3 |
| Baudrate | 9600 |
| Timeout | 1 segundo |

**Comandos:**
- Arduino → PC: Envía UID de tarjeta como texto (ej: "A1B2C3D4")
- PC → Arduino: Envía "OPEN\n" para abrir puerta manualmente

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
| **Reportes gráficos** | No incluido - Datos crudos disponibles |
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
| **Sin backup automático** | Requiere backup manual de gym_access.db |

### Diferencias con Sistema Anterior (Java)

| Característica | Sistema Anterior | BloomFitness |
|----------------|------------------|--------------|
| Plan "std" (3 días/semana) | Sí | No - Migrado como mensual |
| Control de uso semanal | Sí | No |
| Interfaz | Java Swing | PySide6 (Qt) |
| Ejecutable | Requiere Java | .exe independiente |

---

## Flujo de Trabajo Típico

### Alta de Nuevo Miembro
1. Ir a "Usuarios" → "Agregar Usuario"
2. Completar apellido, nombre y datos de contacto
3. Seleccionar plan (Mensual/3 Meses/6 Meses)
4. Fecha inicio se pone automáticamente como hoy
5. Seleccionar método de pago
6. (Opcional) Asignar tarjeta RFID escaneando
7. Guardar

### Renovación de Plan
1. Buscar usuario en la lista
2. Seleccionar → "Editar Usuario"
3. Cambiar fecha de inicio a la fecha de renovación
4. El sistema calcula nueva fecha de fin
5. Guardar

### Consulta de Accesos
1. Ir a "Registro Accesos"
2. Aplicar filtros de fecha si es necesario
3. Ver historial de ingresos
4. Exportar a CSV si se requiere análisis

---

## Arquitectura del Sistema

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Arduino +     │────▶│   BloomFitness  │────▶│   SQLite DB     │
│   Lector RFID   │     │   (Python/Qt)   │     │   (Local)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Cerradura     │
                        │   Eléctrica     │
                        └─────────────────┘
```

---

## Archivos Importantes

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| BloomFitness.exe | Carpeta principal | Ejecutable de la aplicación |
| gym_access.db | data/ | Base de datos SQLite |
| logo.png | assets/ o junto al .exe | Logo del gimnasio (opcional) |

---

*Documentación actualizada: Enero 2026*
