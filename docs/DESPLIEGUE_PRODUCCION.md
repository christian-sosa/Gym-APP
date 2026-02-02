# BloomFitness – Despliegue a Producción

Guía paso a paso para llevar BloomFitness a producción: qué copiar, cómo migrar la base de datos antigua y cómo dejar el sistema listo para usar.

---

## Resumen rápido

| Pregunta | Respuesta |
|----------|-----------|
| ¿Llevo el .exe o el proyecto? | **Solo el .exe + carpeta `data`** (recomendado). O el proyecto completo si quieres migrar en el mismo equipo. |
| ¿Dónde se migra la base de datos? | En tu PC de desarrollo, **antes** de generar el .exe. Luego copias `data/gym_access.db` ya migrada. |
| ¿Qué hace falta en producción? | Windows 10/11, carpeta con `BloomFitness.exe` y `data/gym_access.db`. Arduino opcional. |

---

## 1. Requisitos previos (en tu PC de desarrollo)

- Windows 10/11  
- Python 3.11+ (solo para generar el .exe y correr la migración)  
- Base de datos antigua del gimnasio: **`gym_to_migrate.db`** (en la raíz del proyecto o donde indiques en el script)

---

## 2. Migrar la base de datos (en desarrollo)

La migración se hace **en tu PC**, antes de generar el .exe. Así en producción solo copias el .exe y la carpeta `data` con la base ya migrada.

### Paso 2.1 – Ubicar la base antigua

- Coloca el archivo de la base antigua en la raíz del proyecto con el nombre **`gym_to_migrate.db`**  
  Ejemplo: `C:\Users\Christian\Documents\BloomFitness\gym_to_migrate.db`  
- Si la tienes con otro nombre o en otra ruta, puedes copiarla o renombrarla a `gym_to_migrate.db` en la raíz.

### Paso 2.2 – Crear la base nueva (vacía con tablas)

La base nueva debe **existir y tener tablas** antes de migrar. La aplicación las crea al abrirse.

1. Abre una terminal en la raíz del proyecto:
   ```bash
   cd C:\Users\Christian\Documents\BloomFitness
   ```
2. Activa el entorno virtual si lo usas:
   ```bash
   venv\Scripts\activate
   ```
3. Ejecuta la aplicación **una vez** y ciérrala:
   ```bash
   python main.py
   ```
   Se creará `data\gym_access.db` con las tablas vacías.

### Paso 2.3 – Ejecutar la migración

1. Con la aplicación **cerrada**, en la misma carpeta del proyecto:
   ```bash
   python etl/migrate_from_old_db.py
   ```
2. Revisa la salida en consola:
   - Total de usuarios en origen
   - Migrados OK / con advertencias / fallidos
   - Si la base destino ya tenía usuarios, te preguntará si quieres agregar más (s/n).
3. Si hay errores, corrígelos y vuelve a ejecutar si hace falta (ten en cuenta si te preguntó “agregar más”).
4. Dependencia extra para el script de migración (por si no la tienes):
   ```bash
   pip install python-dateutil
   ```

### Paso 2.4 – Verificar datos migrados

- Vuelve a abrir la app y comprueba en “Usuarios” que aparezcan los datos.  
- O abre `data\gym_access.db` con DBeaver/DB Browser y revisa las tablas `users` y `access_logs`.

---

## 3. Generar el ejecutable (.exe)

Solo después de tener **`data\gym_access.db`** ya migrada:

1. En la raíz del proyecto:
   ```bash
   build.bat
   ```
   O manualmente:
   ```bash
   pip install -r requirements.txt
   pyinstaller BloomFitness.spec
   ```
2. El .exe quedará en: **`dist\BloomFitness.exe`**.

---

## 4. Qué llevar a producción

En producción **no hace falta Python** si usas el .exe.

### Opción A – Solo ejecutable + datos (recomendado)

Lleva solo estos elementos al equipo del gimnasio:

1. **`dist\BloomFitness.exe`**  
2. **Carpeta `data`** completa, con la base ya migrada:
   - `data\gym_access.db`

Estructura en el equipo de producción:

```
C:\BloomFitness\          (o la ruta que elijas)
├── BloomFitness.exe
└── data\
    └── gym_access.db
```

Pasos en el equipo de producción:

1. Crear la carpeta (ej. `C:\BloomFitness`).  
2. Copiar ahí `BloomFitness.exe` y la carpeta `data` (con `gym_access.db` dentro).  
3. Ejecutar `BloomFitness.exe`.  
4. (Opcional) Conectar el Arduino y, desde la app, en “Tarjetas RFID” elegir el puerto COM correcto.

No copies la base antigua `gym_to_migrate.db` a producción; no la usa la aplicación.

### Opción B – Proyecto completo (por si quieres migrar en el mismo PC de producción)

Solo tiene sentido si en el gimnasio tienes Python instalado y quieres hacer la migración ahí.

1. Copiar todo el proyecto (incluido `gym_to_migrate.db`).  
2. Instalar Python 3.11+ y dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar la app una vez para crear `data\gym_access.db`.  
4. Ejecutar la migración:
   ```bash
   python etl/migrate_from_old_db.py
   ```
5. Luego usar:
   - `python main.py`, o  
   - el .exe generado en ese mismo PC (`build.bat` y luego `dist\BloomFitness.exe`).

Para uso normal en producción suele ser más simple la **Opción A**.

---

## 5. Configuración en producción

- **Puerto del Arduino**  
  Por defecto la app usa `COM3`. Si el Arduino está en otro puerto:
  - Abre la aplicación → “Tarjetas RFID” → selecciona el puerto correcto en la interfaz.  
  - No hace falta tocar código ni config si eliges el puerto desde la app.

- **Modo debug (sin Arduino)**  
  Para probar sin hardware:
  - En la app: “Tarjetas RFID” → activar “Modo Debug: ON”.  
  - O antes de abrir la app: `set BLOOM_DEBUG=1` y luego ejecutar el .exe (si quieres usarlo desde un .bat).

- **Respaldo de la base de datos**  
  Recomendación: copiar periódicamente la carpeta `data` (o al menos `data\gym_access.db`) a un pendrive o red. Es la única base que usa la aplicación en producción.

---

## 6. Checklist antes de ir a producción

- [ ] Base antigua `gym_to_migrate.db` en la raíz del proyecto (o path correcto en el script).  
- [ ] Ejecutada la app una vez para crear `data\gym_access.db`.  
- [ ] Ejecutado `python etl/migrate_from_old_db.py` sin errores críticos.  
- [ ] Revisados usuarios y datos en la app o en la base.  
- [ ] Ejecutado `build.bat` y comprobado que existe `dist\BloomFitness.exe`.  
- [ ] Copiados a producción: `BloomFitness.exe` + carpeta `data` con `gym_access.db`.  
- [ ] En producción: probado que la app abre y se ven los usuarios.  
- [ ] (Opcional) Probado Arduino y selección de puerto COM en “Tarjetas RFID”.

---

## 7. Resumen del flujo de datos

```
Base antigua (gym)     Migración (en tu PC)     Base nueva (BloomFitness)
gym_to_migrate.db  →  etl/migrate_from_old_db  →  data/gym_access.db
                              ↓
                    Ejecutar app 1 vez antes
                    para crear tablas en data/gym_access.db
```

En producción solo existe y se usa **`data/gym_access.db`**. El archivo `gym_to_migrate.db` es solo para la migración en desarrollo.

---

## 8. Solución de problemas

| Problema | Qué hacer |
|----------|-----------|
| “No se encontró la base de datos origen” | Comprueba que `gym_to_migrate.db` está en la raíz del proyecto (o ajusta `OLD_DB_PATH` en `etl/migrate_from_old_db.py`). |
| “No se encontró la base de datos destino” | Ejecuta antes `python main.py` una vez y cierra la app para que se cree `data/gym_access.db`. |
| Error con `relativedelta` al migrar | Instala: `pip install python-dateutil`. |
| En producción la app no ve usuarios | Asegúrate de haber copiado la carpeta `data` con el `gym_access.db` **ya migrado**, no una base vacía recién creada. |
| Arduino no detectado | En “Tarjetas RFID” elige el puerto COM correcto; revisa el Administrador de dispositivos. |

Si quieres, en un siguiente paso se puede añadir una sección de “Primera vez en el gimnasio” (encender PC, conectar Arduino, abrir app, verificar un acceso de prueba).
