"""
Utilidades para manejo de fechas.
"""
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from src.utils.enums import PlanType


def calcular_fecha_fin(fecha_inicio: date, plan_type: PlanType) -> date:
    """
    Calcula la fecha de fin del plan basándose en el tipo de plan.
    
    Args:
        fecha_inicio: Fecha de inicio del plan
        plan_type: Tipo de plan (mensual, x3, x6)
    
    Returns:
        Fecha de fin del plan
    """
    meses = plan_type.months
    return fecha_inicio + relativedelta(months=meses)


def plan_vigente(fecha_fin: date) -> bool:
    """
    Verifica si un plan está vigente.
    
    Args:
        fecha_fin: Fecha de fin del plan
    
    Returns:
        True si el plan está vigente, False si venció
    """
    return date.today() <= fecha_fin


def dias_restantes(fecha_fin: date) -> int:
    """
    Calcula los días restantes de un plan.
    
    Args:
        fecha_fin: Fecha de fin del plan
    
    Returns:
        Días restantes (negativo si ya venció)
    """
    return (fecha_fin - date.today()).days


def formato_fecha(fecha: date) -> str:
    """
    Formatea una fecha para mostrar en la UI.
    
    Args:
        fecha: Fecha a formatear
    
    Returns:
        Fecha formateada como string (YYYY-MM-DD)
    """
    return fecha.strftime("%Y-%m-%d")


def formato_datetime(dt: datetime) -> str:
    """
    Formatea un datetime para mostrar en la UI.
    
    Args:
        dt: Datetime a formatear
    
    Returns:
        Datetime formateado como string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")
