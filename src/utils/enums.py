"""
Enumeraciones usadas en la aplicación BloomFitness.
"""
import enum


class PlanType(enum.Enum):
    """Tipos de planes de membresía del gimnasio."""
    MENSUAL = "mensual"  # +1 mes
    X3 = "x3"            # +3 meses
    X6 = "x6"            # +6 meses
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en la UI."""
        names = {
            PlanType.MENSUAL: "Mensual",
            PlanType.X3: "3 Meses",
            PlanType.X6: "6 Meses"
        }
        return names.get(self, self.value)
    
    @property
    def months(self) -> int:
        """Cantidad de meses del plan."""
        months = {
            PlanType.MENSUAL: 1,
            PlanType.X3: 3,
            PlanType.X6: 6
        }
        return months.get(self, 1)


class AccessResult(enum.Enum):
    """Resultado de un intento de acceso."""
    PERMITIDO = "permitido"
    DENEGADO = "denegado"


class AccessReason(enum.Enum):
    """Motivo del resultado de acceso."""
    OK = "ok"                  # Acceso permitido
    NO_EXISTE = "no_existe"    # Tarjeta no registrada
    VENCIDO = "vencido"        # Plan vencido
    INACTIVO = "inactivo"      # Usuario inactivo
    MANUAL = "manual"          # Apertura manual (visitante)


class PaymentMethod(enum.Enum):
    """Métodos de pago para la membresía."""
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    MERCADOPAGO = "mercadopago"
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en la UI."""
        names = {
            PaymentMethod.EFECTIVO: "Efectivo",
            PaymentMethod.TARJETA: "Tarjeta",
            PaymentMethod.MERCADOPAGO: "MercadoPago"
        }
        return names.get(self, self.value)
