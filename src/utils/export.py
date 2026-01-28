"""
Utilidades para exportación de datos.
"""
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def export_to_csv(data: List[Dict[str, Any]], filepath: Path, headers: List[str] = None) -> bool:
    """
    Exporta datos a un archivo CSV.
    
    Args:
        data: Lista de diccionarios con los datos
        filepath: Ruta del archivo de salida
        headers: Lista de cabeceras (opcional, se infieren de los datos)
    
    Returns:
        True si la exportación fue exitosa
    """
    if not data:
        return False
    
    if headers is None:
        headers = list(data[0].keys())
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error exportando CSV: {e}")
        return False


def generate_export_filename(prefix: str = "export") -> str:
    """
    Genera un nombre de archivo único para exportación.
    
    Args:
        prefix: Prefijo del nombre de archivo
    
    Returns:
        Nombre de archivo con timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"
