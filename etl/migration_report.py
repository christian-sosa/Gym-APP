#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un reporte de la migracion realizada.
"""
import sqlite3
from datetime import date
from pathlib import Path

OLD_DB_PATH = Path(__file__).parent.parent / "gym_to_migrate.db"
NEW_DB_PATH = Path(__file__).parent.parent / "data" / "gym_access.db"
REPORT_PATH = Path(__file__).parent / "migration_report.txt"


def main():
    old_conn = sqlite3.connect(OLD_DB_PATH)
    new_conn = sqlite3.connect(NEW_DB_PATH)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("REPORTE DE MIGRACION - BloomFitness")
    report_lines.append(f"Fecha: {date.today()}")
    report_lines.append("=" * 70)
    
    # Conteo de registros
    old_cursor.execute("SELECT COUNT(*) FROM usuarios")
    old_count = old_cursor.fetchone()[0]
    
    new_cursor.execute("SELECT COUNT(*) FROM users")
    new_count = new_cursor.fetchone()[0]
    
    report_lines.append(f"\nRegistros en origen (gym_to_migrate.db): {old_count}")
    report_lines.append(f"Registros en destino (gym_access.db): {new_count}")
    
    # Verificar usuarios con nombres problematicos
    report_lines.append("\n" + "-" * 70)
    report_lines.append("USUARIOS CON ADVERTENCIAS:")
    report_lines.append("-" * 70)
    
    # Buscar usuarios con apellido vacio o generico
    new_cursor.execute("""
        SELECT id, apellido, nombre, email 
        FROM users 
        WHERE apellido = '' OR apellido = 'Sin Apellido' OR apellido IS NULL
    """)
    problematic = new_cursor.fetchall()
    
    if problematic:
        report_lines.append(f"\nUsuarios sin apellido claro ({len(problematic)}):")
        for u in problematic:
            report_lines.append(f"  ID {u[0]}: '{u[1]}' '{u[2]}' - {u[3] or 'sin email'}")
    else:
        report_lines.append("\nNo hay usuarios con apellido problematico.")
    
    # Buscar usuarios con plan vencido
    today = date.today().isoformat()
    new_cursor.execute(f"""
        SELECT id, apellido, nombre, fecha_fin_plan, activo
        FROM users 
        WHERE fecha_fin_plan < '{today}'
    """)
    expired = new_cursor.fetchall()
    
    report_lines.append(f"\nUsuarios con plan vencido ({len(expired)}):")
    if expired:
        for u in expired[:20]:
            status = "activo" if u[4] else "inactivo"
            report_lines.append(f"  ID {u[0]}: {u[1]} {u[2]} - vencio {u[3]} ({status})")
        if len(expired) > 20:
            report_lines.append(f"  ... y {len(expired) - 20} mas")
    else:
        report_lines.append("  Ninguno")
    
    # Verificar tarjetas RFID
    old_cursor.execute("SELECT COUNT(*) FROM tarjetas_rfid WHERE uid IS NOT NULL AND activa = 1")
    old_rfid = old_cursor.fetchone()[0]
    
    new_cursor.execute("SELECT COUNT(*) FROM users WHERE rfid_uid IS NOT NULL AND rfid_uid != ''")
    new_rfid = new_cursor.fetchone()[0]
    
    report_lines.append(f"\nTarjetas RFID migradas: {new_rfid} de {old_rfid}")
    
    # Verificar registros de acceso
    old_cursor.execute("SELECT COUNT(*) FROM registros_ingreso")
    old_access = old_cursor.fetchone()[0]
    
    new_cursor.execute("SELECT COUNT(*) FROM access_logs")
    new_access = new_cursor.fetchone()[0]
    
    report_lines.append(f"Registros de acceso migrados: {new_access} de {old_access}")
    if old_access == 0:
        report_lines.append("  (La tabla origen estaba vacia)")
    
    # Resumen de mapeo de membresias
    report_lines.append("\n" + "-" * 70)
    report_lines.append("MAPEO DE MEMBRESIAS:")
    report_lines.append("-" * 70)
    report_lines.append("  Tipo original   ->  Tipo nuevo")
    report_lines.append("  'full' (id=1)   ->  'mensual'")
    report_lines.append("  'std'  (id=2)   ->  'mensual'")
    report_lines.append("\n  NOTA: El tipo 'std' (3 dias/semana) no tiene equivalente")
    report_lines.append("  en el nuevo sistema y se migro como 'mensual'.")
    
    # Lista de campos no migrados
    report_lines.append("\n" + "-" * 70)
    report_lines.append("CAMPOS/DATOS NO MIGRADOS:")
    report_lines.append("-" * 70)
    report_lines.append("  - uso_semanal_std: Control de dias usados por semana (no aplica)")
    report_lines.append("  - Limite de 3 dias/semana para plan 'std' (no soportado)")
    report_lines.append("  - Metodo de pago: Se asigno 'efectivo' por defecto a todos")
    
    # Estadisticas finales
    report_lines.append("\n" + "=" * 70)
    report_lines.append("RESUMEN FINAL:")
    report_lines.append("=" * 70)
    report_lines.append(f"  Total usuarios migrados: {new_count}")
    report_lines.append(f"  Usuarios con plan vigente: {new_count - len(expired)}")
    report_lines.append(f"  Usuarios con plan vencido: {len(expired)}")
    report_lines.append(f"  Usuarios con tarjeta RFID: {new_rfid}")
    
    if old_count == new_count:
        report_lines.append("\n  [OK] MIGRACION COMPLETA - Todos los usuarios fueron migrados")
    else:
        report_lines.append(f"\n  [!] ATENCION - Diferencia de {old_count - new_count} registros")
    
    old_conn.close()
    new_conn.close()
    
    # Guardar reporte
    report_content = "\n".join(report_lines)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # Mostrar en consola
    print(report_content)
    print(f"\nReporte guardado en: {REPORT_PATH}")


if __name__ == "__main__":
    main()
