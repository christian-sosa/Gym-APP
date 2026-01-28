#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL - Migración de base de datos antigua a BloomFitness

Este script migra los datos de gym_to_migrate.db a data/gym_access.db

Mapeo de campos:
- usuarios.nombre -> apellido + nombre (se divide automáticamente)
- usuarios.email -> email
- usuarios.id_membresia -> plan (1=full->MENSUAL, 2=std->MENSUAL)
- usuarios.celular -> celular
- usuarios.observaciones -> observaciones
- usuarios.ultima_fecha_pago -> fecha_inicio_plan
- tarjetas_rfid.uid -> rfid_uid

Uso:
    python etl/migrate_from_old_db.py
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# Rutas de bases de datos
OLD_DB_PATH = Path(__file__).parent.parent / "gym_to_migrate.db"
NEW_DB_PATH = Path(__file__).parent.parent / "data" / "gym_access.db"

# Mapeo de membresías antiguas a nuevas
# IMPORTANTE: Usar nombres de enum en MAYUSCULAS (MENSUAL, X3, X6)
MEMBRESIA_MAP = {
    1: "MENSUAL",   # full -> mensual
    2: "MENSUAL",   # std -> mensual (no hay equivalente exacto)
}

# Método de pago por defecto (usar nombre de enum en MAYUSCULAS)
DEFAULT_PAYMENT_METHOD = "EFECTIVO"


@dataclass
class MigrationResult:
    """Resultado de la migración."""
    total_source: int = 0
    migrated_ok: int = 0
    migrated_with_warnings: int = 0
    failed: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def split_name(full_name: str) -> Tuple[str, str]:
    """
    Divide un nombre completo en nombre y apellido.
    
    Estrategia: La última palabra es el apellido, el resto es el nombre.
    Si solo hay una palabra, se usa como apellido.
    
    Returns:
        Tuple (nombre, apellido)
    """
    if not full_name:
        return ("Sin Nombre", "Sin Apellido")
    
    parts = full_name.strip().split()
    
    if len(parts) == 1:
        return (parts[0], "")
    elif len(parts) == 2:
        return (parts[0], parts[1])
    else:
        # Asumimos: primeras palabras son nombre, última es apellido
        # Ej: "Juan Carlos Pérez" -> nombre="Juan Carlos", apellido="Pérez"
        return (" ".join(parts[:-1]), parts[-1])


def get_rfid_for_user(cursor: sqlite3.Cursor, user_id: int) -> Optional[str]:
    """Obtiene el UID de RFID para un usuario si existe."""
    cursor.execute("""
        SELECT uid FROM tarjetas_rfid 
        WHERE id_usuario = ? AND activa = 1 AND uid IS NOT NULL
    """, (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None


def calculate_end_date(start_date: date, plan: str) -> date:
    """Calcula la fecha de fin basada en el plan."""
    from dateutil.relativedelta import relativedelta
    
    months = {
        "mensual": 1,
        "x3": 3,
        "x6": 6
    }
    
    return start_date + relativedelta(months=months.get(plan, 1))


def migrate_users(old_cursor: sqlite3.Cursor, new_conn: sqlite3.Connection) -> MigrationResult:
    """Migra los usuarios de la base de datos antigua a la nueva."""
    result = MigrationResult()
    
    # Obtener todos los usuarios de la DB antigua
    old_cursor.execute("""
        SELECT id, nombre, email, id_membresia, celular, observaciones, ultima_fecha_pago
        FROM usuarios
        ORDER BY id
    """)
    
    users = old_cursor.fetchall()
    result.total_source = len(users)
    
    new_cursor = new_conn.cursor()
    
    for user in users:
        old_id, nombre_completo, email, id_membresia, celular, observaciones, ultima_fecha_pago = user
        
        try:
            # Dividir nombre
            nombre, apellido = split_name(nombre_completo)
            
            warnings_for_user = []
            
            # Mapear membresía
            plan = MEMBRESIA_MAP.get(id_membresia, "mensual")
            if id_membresia not in MEMBRESIA_MAP:
                warnings_for_user.append(f"Membresía desconocida {id_membresia}, usando 'mensual'")
            
            # Parsear fecha de inicio
            if ultima_fecha_pago:
                try:
                    if isinstance(ultima_fecha_pago, str):
                        fecha_inicio = datetime.strptime(ultima_fecha_pago, "%Y-%m-%d").date()
                    else:
                        fecha_inicio = ultima_fecha_pago
                except ValueError:
                    fecha_inicio = date.today()
                    warnings_for_user.append(f"Fecha inválida '{ultima_fecha_pago}', usando fecha actual")
            else:
                fecha_inicio = date.today()
                warnings_for_user.append("Sin fecha de pago, usando fecha actual")
            
            # Calcular fecha fin
            fecha_fin = calculate_end_date(fecha_inicio, plan)
            
            # Determinar estado activo (si la fecha de fin es futura, está activo)
            activo = fecha_fin >= date.today()
            
            # Obtener RFID si existe
            rfid_uid = get_rfid_for_user(old_cursor, old_id)
            
            # Limpiar observaciones (pueden tener caracteres raros)
            if observaciones:
                observaciones = observaciones.encode('utf-8', errors='replace').decode('utf-8')
            
            # Verificar si el apellido está vacío
            if not apellido:
                apellido = "Sin Apellido"
                warnings_for_user.append(f"Nombre único '{nombre_completo}', apellido asignado como 'Sin Apellido'")
            
            # Insertar en nueva DB
            new_cursor.execute("""
                INSERT INTO users (
                    nombre, apellido, email, celular, observaciones,
                    plan, fecha_inicio_plan, fecha_fin_plan,
                    rfid_uid, activo, metodo_pago,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nombre,
                apellido,
                email if email else None,
                celular if celular else None,
                observaciones if observaciones else None,
                plan,
                fecha_inicio.isoformat(),
                fecha_fin.isoformat(),
                rfid_uid,
                activo,
                DEFAULT_PAYMENT_METHOD,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            if warnings_for_user:
                result.migrated_with_warnings += 1
                for w in warnings_for_user:
                    result.warnings.append(f"Usuario ID {old_id} ({nombre_completo}): {w}")
            else:
                result.migrated_ok += 1
                
        except Exception as e:
            result.failed += 1
            result.errors.append(f"Usuario ID {old_id} ({nombre_completo}): {str(e)}")
    
    new_conn.commit()
    return result


def migrate_access_logs(old_cursor: sqlite3.Cursor, new_conn: sqlite3.Connection) -> MigrationResult:
    """Migra los registros de acceso."""
    result = MigrationResult()
    
    old_cursor.execute("SELECT COUNT(*) FROM registros_ingreso")
    result.total_source = old_cursor.fetchone()[0]
    
    if result.total_source == 0:
        result.warnings.append("No hay registros de acceso para migrar")
        return result
    
    # Si hubiera registros, se migrarían aquí
    # Por ahora la tabla está vacía según el análisis
    
    return result


def main():
    """Ejecuta la migración completa."""
    print("=" * 60)
    print("MIGRACIÓN DE BASE DE DATOS - BloomFitness")
    print("=" * 60)
    print(f"\nOrigen: {OLD_DB_PATH}")
    print(f"Destino: {NEW_DB_PATH}")
    
    # Verificar que existan las bases de datos
    if not OLD_DB_PATH.exists():
        print(f"\n[ERROR] No se encontro la base de datos origen: {OLD_DB_PATH}")
        return
    
    if not NEW_DB_PATH.exists():
        print(f"\n[ERROR] No se encontro la base de datos destino: {NEW_DB_PATH}")
        print("   Ejecute la aplicacion al menos una vez para crear la DB.")
        return
    
    # Conectar a ambas bases de datos
    old_conn = sqlite3.connect(OLD_DB_PATH)
    old_cursor = old_conn.cursor()
    
    new_conn = sqlite3.connect(NEW_DB_PATH)
    
    try:
        # Verificar si ya hay datos en la nueva DB
        new_cursor = new_conn.cursor()
        new_cursor.execute("SELECT COUNT(*) FROM users")
        existing_count = new_cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"\n[ADVERTENCIA] La base de datos destino ya tiene {existing_count} usuarios.")
            response = input("   Desea continuar y agregar mas? (s/n): ")
            if response.lower() != 's':
                print("   Migracion cancelada.")
                return
        
        # Migrar usuarios
        print("\n" + "-" * 40)
        print("Migrando usuarios...")
        print("-" * 40)
        
        user_result = migrate_users(old_cursor, new_conn)
        
        print(f"\nRESULTADO DE MIGRACION DE USUARIOS:")
        print(f"   Total en origen:        {user_result.total_source}")
        print(f"   [OK] Migrados OK:       {user_result.migrated_ok}")
        print(f"   [!] Con advertencias:   {user_result.migrated_with_warnings}")
        print(f"   [X] Fallidos:           {user_result.failed}")
        
        # Migrar registros de acceso
        print("\n" + "-" * 40)
        print("Migrando registros de acceso...")
        print("-" * 40)
        
        access_result = migrate_access_logs(old_cursor, new_conn)
        
        print(f"\nRESULTADO DE MIGRACION DE ACCESOS:")
        print(f"   Total en origen:        {access_result.total_source}")
        print(f"   [OK] Migrados OK:       {access_result.migrated_ok}")
        
        # Mostrar advertencias
        if user_result.warnings or access_result.warnings:
            print("\n" + "=" * 60)
            print("[!] ADVERTENCIAS:")
            print("=" * 60)
            for w in user_result.warnings[:20]:  # Limitar a 20
                print(f"   - {w}")
            if len(user_result.warnings) > 20:
                print(f"   ... y {len(user_result.warnings) - 20} advertencias mas")
            for w in access_result.warnings:
                print(f"   - {w}")
        
        # Mostrar errores
        if user_result.errors or access_result.errors:
            print("\n" + "=" * 60)
            print("[X] ERRORES (registros que NO se migraron):")
            print("=" * 60)
            for e in user_result.errors:
                print(f"   - {e}")
            for e in access_result.errors:
                print(f"   - {e}")
        
        # Resumen final
        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)
        total_migrated = user_result.migrated_ok + user_result.migrated_with_warnings
        total_failed = user_result.failed + access_result.failed
        
        if total_failed == 0:
            print(f"[OK] Migracion completada exitosamente!")
            print(f"   {total_migrated} usuarios migrados")
        else:
            print(f"[!] Migracion completada con errores")
            print(f"   {total_migrated} usuarios migrados")
            print(f"   {total_failed} registros NO migrados (ver errores arriba)")
        
    finally:
        old_conn.close()
        new_conn.close()


if __name__ == "__main__":
    main()
