"""
Servicio de backup diario para la base de datos SQLite.
"""
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.config import DATA_DIR, DATABASE_PATH


@dataclass
class BackupResult:
    ok: bool
    path: Path | None
    message: str


def create_daily_backup() -> BackupResult:
    """Crea (o reemplaza) el backup diario de la base de datos.

    Destino: DATA_DIR / yyyy-mm-dd / gym_access.db
    Si ya existe un archivo en esa ruta, se sobrescribe.
    """
    if not DATABASE_PATH.exists():
        return BackupResult(
            ok=False,
            path=None,
            message=f"No se encontró la base de datos en:\n{DATABASE_PATH}",
        )

    today_folder = DATA_DIR / date.today().strftime("%Y-%m-%d")
    today_folder.mkdir(parents=True, exist_ok=True)

    dest = today_folder / DATABASE_PATH.name
    try:
        shutil.copy2(DATABASE_PATH, dest)
    except OSError as exc:
        return BackupResult(ok=False, path=None, message=f"Error al copiar:\n{exc}")

    return BackupResult(ok=True, path=dest, message=f"Backup guardado en:\n{dest}")
