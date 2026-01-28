#!/usr/bin/env python3
"""
ETL - Extracción de datos de BloomFitness a CSV

Este script conecta directamente a la base de datos SQLite y exporta
los datos a archivos CSV para análisis externo.

Uso:
    python etl/extract_to_csv.py

Los archivos CSV se generarán en la carpeta etl/output/
"""
import csv
import sqlite3
from datetime import datetime
from pathlib import Path

# Configuración
DB_PATH = Path(__file__).parent.parent / "data" / "gym_access.db"
OUTPUT_DIR = Path(__file__).parent / "output"


def ensure_output_dir():
    """Crea el directorio de salida si no existe."""
    OUTPUT_DIR.mkdir(exist_ok=True)


def get_connection():
    """
    Obtiene una conexión a la base de datos SQLite.
    
    Returns:
        sqlite3.Connection: Conexión a la base de datos
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Base de datos no encontrada en: {DB_PATH}\n"
            "Asegúrese de haber ejecutado la aplicación al menos una vez."
        )
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn


def extract_users(conn: sqlite3.Connection) -> list:
    """
    Extrae todos los usuarios de la base de datos.
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        Lista de diccionarios con los datos de usuarios
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id,
            nombre,
            apellido,
            email,
            celular,
            observaciones,
            plan,
            fecha_inicio_plan,
            fecha_fin_plan,
            rfid_uid,
            activo,
            created_at,
            updated_at
        FROM users
        ORDER BY apellido, nombre
    """)
    
    users = []
    for row in cursor.fetchall():
        users.append({
            "id": row["id"],
            "nombre": row["nombre"],
            "apellido": row["apellido"],
            "nombre_completo": f"{row['nombre']} {row['apellido']}",
            "email": row["email"] or "",
            "celular": row["celular"] or "",
            "observaciones": row["observaciones"] or "",
            "plan": row["plan"],
            "fecha_inicio_plan": row["fecha_inicio_plan"],
            "fecha_fin_plan": row["fecha_fin_plan"],
            "rfid_uid": row["rfid_uid"] or "",
            "activo": "Sí" if row["activo"] else "No",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })
    
    return users


def extract_access_logs(conn: sqlite3.Connection) -> list:
    """
    Extrae todos los registros de acceso con información del usuario.
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        Lista de diccionarios con los registros de acceso
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.id,
            a.timestamp,
            a.rfid_uid,
            a.user_id,
            u.nombre as user_nombre,
            u.apellido as user_apellido,
            a.resultado,
            a.motivo
        FROM access_logs a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
    """)
    
    logs = []
    for row in cursor.fetchall():
        user_name = ""
        if row["user_nombre"] and row["user_apellido"]:
            user_name = f"{row['user_nombre']} {row['user_apellido']}"
        elif row["user_nombre"]:
            user_name = row["user_nombre"]
        
        logs.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "rfid_uid": row["rfid_uid"],
            "user_id": row["user_id"] or "",
            "usuario": user_name or "No registrado",
            "resultado": row["resultado"],
            "motivo": row["motivo"]
        })
    
    return logs


def extract_stats(conn: sqlite3.Connection) -> dict:
    """
    Extrae estadísticas generales.
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        Diccionario con estadísticas
    """
    cursor = conn.cursor()
    
    # Total usuarios
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Usuarios activos
    cursor.execute("SELECT COUNT(*) FROM users WHERE activo = 1")
    active_users = cursor.fetchone()[0]
    
    # Usuarios con plan vigente
    cursor.execute("""
        SELECT COUNT(*) FROM users 
        WHERE activo = 1 AND fecha_fin_plan >= date('now')
    """)
    valid_plans = cursor.fetchone()[0]
    
    # Total accesos
    cursor.execute("SELECT COUNT(*) FROM access_logs")
    total_access = cursor.fetchone()[0]
    
    # Accesos permitidos
    cursor.execute("SELECT COUNT(*) FROM access_logs WHERE resultado = 'PERMITIDO'")
    allowed_access = cursor.fetchone()[0]
    
    # Accesos por plan
    cursor.execute("""
        SELECT plan, COUNT(*) as cantidad
        FROM users
        GROUP BY plan
    """)
    users_by_plan = {row[0]: row[1] for row in cursor.fetchall()}
    
    return {
        "total_usuarios": total_users,
        "usuarios_activos": active_users,
        "planes_vigentes": valid_plans,
        "total_accesos": total_access,
        "accesos_permitidos": allowed_access,
        "accesos_denegados": total_access - allowed_access,
        "tasa_acceso": round(allowed_access / total_access * 100, 2) if total_access > 0 else 0,
        "usuarios_por_plan": users_by_plan
    }


def write_csv(data: list, filename: str, fieldnames: list = None):
    """
    Escribe datos a un archivo CSV.
    
    Args:
        data: Lista de diccionarios
        filename: Nombre del archivo
        fieldnames: Lista de nombres de campos (opcional)
    """
    if not data:
        print(f"  ⚠ No hay datos para {filename}")
        return
    
    filepath = OUTPUT_DIR / filename
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"  ✓ {filename} - {len(data)} registros")


def main():
    """Función principal del ETL."""
    print("=" * 50)
    print("BloomFitness ETL - Extracción a CSV")
    print("=" * 50)
    print()
    
    # Crear directorio de salida
    ensure_output_dir()
    print(f"Directorio de salida: {OUTPUT_DIR}")
    print()
    
    try:
        # Conectar a la base de datos
        print(f"Conectando a: {DB_PATH}")
        conn = get_connection()
        print("Conexión exitosa!")
        print()
        
        # Timestamp para los archivos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extraer usuarios
        print("Extrayendo datos...")
        users = extract_users(conn)
        write_csv(users, f"usuarios_{timestamp}.csv")
        
        # Extraer registros de acceso
        logs = extract_access_logs(conn)
        write_csv(logs, f"accesos_{timestamp}.csv")
        
        # Extraer estadísticas
        stats = extract_stats(conn)
        
        # Escribir estadísticas
        stats_data = [
            {"metrica": "Total Usuarios", "valor": stats["total_usuarios"]},
            {"metrica": "Usuarios Activos", "valor": stats["usuarios_activos"]},
            {"metrica": "Planes Vigentes", "valor": stats["planes_vigentes"]},
            {"metrica": "Total Accesos", "valor": stats["total_accesos"]},
            {"metrica": "Accesos Permitidos", "valor": stats["accesos_permitidos"]},
            {"metrica": "Accesos Denegados", "valor": stats["accesos_denegados"]},
            {"metrica": "Tasa de Acceso (%)", "valor": stats["tasa_acceso"]},
        ]
        
        # Agregar usuarios por plan
        for plan, cantidad in stats.get("usuarios_por_plan", {}).items():
            stats_data.append({
                "metrica": f"Usuarios Plan {plan}",
                "valor": cantidad
            })
        
        write_csv(stats_data, f"estadisticas_{timestamp}.csv")
        
        # Cerrar conexión
        conn.close()
        
        print()
        print("=" * 50)
        print("ETL completado exitosamente!")
        print(f"Archivos generados en: {OUTPUT_DIR}")
        print("=" * 50)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
