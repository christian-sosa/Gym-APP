"""
Utilidades para validacion y normalizacion de UIDs RFID.
"""
import re
from typing import Optional


# Formato canonico esperado por la app: "AA-BB-CC-DD" (4 a 10 bytes)
_UID_CANONICAL_RE = re.compile(r"^(?:[0-9A-F]{2})(?:-[0-9A-F]{2}){3,9}$")


def normalize_rfid_uid(uid: Optional[str]) -> Optional[str]:
    """
    Convierte un UID en formato canonico "AA-BB-...".

    Acepta separadores comunes ('-', ':', espacio) o sin separadores.
    Retorna None si el valor no parece un UID hexadecimal valido.
    """
    if uid is None:
        return None

    raw = uid.strip().upper()
    if not raw:
        return None

    # Si ya viene con separadores, unificar y validar.
    if any(sep in raw for sep in ("-", ":", " ")):
        parts = [p for p in re.split(r"[-:\s]+", raw) if p]
        if not parts or not all(re.fullmatch(r"[0-9A-F]{2}", p) for p in parts):
            return None
        canonical = "-".join(parts)
        return canonical if _UID_CANONICAL_RE.fullmatch(canonical) else None

    # Si viene compacto, debe tener longitud par y representar entre 4 y 10 bytes.
    if len(raw) % 2 != 0 or not re.fullmatch(r"[0-9A-F]+", raw):
        return None

    bytes_count = len(raw) // 2
    if bytes_count < 4 or bytes_count > 10:
        return None

    parts = [raw[i:i + 2] for i in range(0, len(raw), 2)]
    return "-".join(parts)


def is_valid_rfid_uid(uid: Optional[str]) -> bool:
    """Indica si el UID es valido segun formato hexadecimal RFID."""
    return normalize_rfid_uid(uid) is not None

