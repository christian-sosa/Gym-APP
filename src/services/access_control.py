"""
Servicio de control de acceso.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.db.database import get_db
from src.db.repository import UserRepository, AccessLogRepository
from src.db.models import User
from src.utils.enums import AccessResult, AccessReason


@dataclass
class AccessCheckResult:
    """Resultado de una verificación de acceso."""
    resultado: AccessResult
    motivo: AccessReason
    user: Optional[User] = None
    message: str = ""


class AccessControlService:
    """Servicio para control de acceso al gimnasio."""
    
    def process_access(self, rfid_uid: str) -> AccessCheckResult:
        """
        Procesa un intento de acceso.
        
        Args:
            rfid_uid: UID de la tarjeta RFID
        
        Returns:
            Resultado del intento de acceso
        """
        db = get_db()
        try:
            user_repo = UserRepository(db)
            access_repo = AccessLogRepository(db)
            
            # Buscar usuario por RFID
            user = user_repo.get_by_rfid(rfid_uid)
            
            # Determinar resultado
            if user is None:
                result = AccessCheckResult(
                    resultado=AccessResult.DENEGADO,
                    motivo=AccessReason.NO_EXISTE,
                    message=f"Tarjeta no registrada: {rfid_uid}"
                )
            elif not user.activo:
                result = AccessCheckResult(
                    resultado=AccessResult.DENEGADO,
                    motivo=AccessReason.INACTIVO,
                    user=user,
                    message=f"Usuario inactivo: {user.nombre_completo}"
                )
            elif not user.plan_vigente:
                result = AccessCheckResult(
                    resultado=AccessResult.DENEGADO,
                    motivo=AccessReason.VENCIDO,
                    user=user,
                    message=f"Plan vencido: {user.nombre_completo} (venció {user.fecha_fin_plan})"
                )
            else:
                result = AccessCheckResult(
                    resultado=AccessResult.PERMITIDO,
                    motivo=AccessReason.OK,
                    user=user,
                    message=f"Acceso permitido: {user.nombre_completo}"
                )
            
            # Registrar en log
            access_repo.create(
                rfid_uid=rfid_uid,
                resultado=result.resultado,
                motivo=result.motivo,
                user_id=user.id if user else None
            )
            
            return result
            
        finally:
            db.close()
    
    def check_access(self, rfid_uid: str) -> AccessCheckResult:
        """
        Verifica el acceso sin registrar en log.
        Útil para verificaciones previas.
        
        Args:
            rfid_uid: UID de la tarjeta RFID
        
        Returns:
            Resultado de la verificación
        """
        db = get_db()
        try:
            user_repo = UserRepository(db)
            user = user_repo.get_by_rfid(rfid_uid)
            
            if user is None:
                return AccessCheckResult(
                    resultado=AccessResult.DENEGADO,
                    motivo=AccessReason.NO_EXISTE,
                    message="Tarjeta no registrada"
                )
            elif not user.activo:
                return AccessCheckResult(
                    resultado=AccessResult.DENEGADO,
                    motivo=AccessReason.INACTIVO,
                    user=user,
                    message="Usuario inactivo"
                )
            elif not user.plan_vigente:
                return AccessCheckResult(
                    resultado=AccessResult.DENEGADO,
                    motivo=AccessReason.VENCIDO,
                    user=user,
                    message="Plan vencido"
                )
            else:
                return AccessCheckResult(
                    resultado=AccessResult.PERMITIDO,
                    motivo=AccessReason.OK,
                    user=user,
                    message="Acceso permitido"
                )
        finally:
            db.close()
    
    def register_manual_access(self, note: str = "Visitante") -> AccessCheckResult:
        """
        Registra un acceso manual (para visitantes sin tarjeta).
        
        Args:
            note: Nota o descripción del visitante
        
        Returns:
            Resultado del acceso manual
        """
        db = get_db()
        try:
            access_repo = AccessLogRepository(db)
            
            # Registrar acceso manual con UID especial
            access_repo.create(
                rfid_uid=f"MANUAL-{note[:20]}",
                resultado=AccessResult.PERMITIDO,
                motivo=AccessReason.MANUAL,
                user_id=None
            )
            
            return AccessCheckResult(
                resultado=AccessResult.PERMITIDO,
                motivo=AccessReason.MANUAL,
                message=f"Acceso manual: {note}"
            )
            
        finally:
            db.close()
