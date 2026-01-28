"""
Servicio para cálculo de planes de membresía.
"""
from datetime import date
from src.utils.enums import PlanType
from src.utils.dates import calcular_fecha_fin, plan_vigente, dias_restantes


class PlanCalculator:
    """Calculadora de planes de membresía."""
    
    @staticmethod
    def calculate_end_date(start_date: date, plan_type: PlanType) -> date:
        """
        Calcula la fecha de fin del plan.
        
        Args:
            start_date: Fecha de inicio
            plan_type: Tipo de plan
        
        Returns:
            Fecha de fin del plan
        """
        return calcular_fecha_fin(start_date, plan_type)
    
    @staticmethod
    def is_plan_active(end_date: date) -> bool:
        """
        Verifica si el plan está vigente.
        
        Args:
            end_date: Fecha de fin del plan
        
        Returns:
            True si el plan está activo
        """
        return plan_vigente(end_date)
    
    @staticmethod
    def days_remaining(end_date: date) -> int:
        """
        Calcula los días restantes del plan.
        
        Args:
            end_date: Fecha de fin del plan
        
        Returns:
            Días restantes (negativo si venció)
        """
        return dias_restantes(end_date)
    
    @staticmethod
    def get_plan_status_text(end_date: date) -> str:
        """
        Obtiene texto descriptivo del estado del plan.
        
        Args:
            end_date: Fecha de fin del plan
        
        Returns:
            Texto descriptivo del estado
        """
        days = dias_restantes(end_date)
        
        if days < 0:
            return f"Vencido hace {abs(days)} días"
        elif days == 0:
            return "Vence hoy"
        elif days == 1:
            return "Vence mañana"
        elif days <= 7:
            return f"Vence en {days} días"
        elif days <= 30:
            return f"Vence en {days} días"
        else:
            return f"Vigente ({days} días restantes)"
    
    @staticmethod
    def get_plan_months(plan_type: PlanType) -> int:
        """
        Obtiene la cantidad de meses del plan.
        
        Args:
            plan_type: Tipo de plan
        
        Returns:
            Cantidad de meses
        """
        return plan_type.months
