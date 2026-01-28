"""
Repositorios para acceso a datos (patrón Repository).
"""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from src.db.models import User, AccessLog
from src.utils.enums import PlanType, AccessResult, AccessReason, PaymentMethod
from src.utils.dates import calcular_fecha_fin


class UserRepository:
    """Repositorio para operaciones CRUD de usuarios."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, include_inactive: bool = True) -> List[User]:
        """Obtiene todos los usuarios."""
        query = self.db.query(User)
        if not include_inactive:
            query = query.filter(User.activo == True)
        return query.order_by(User.apellido, User.nombre).all()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por su ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_rfid(self, rfid_uid: str) -> Optional[User]:
        """Obtiene un usuario por su UID de tarjeta RFID."""
        return self.db.query(User).filter(User.rfid_uid == rfid_uid).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def search(
        self,
        nombre: str = None,
        apellido: str = None,
        email: str = None,
        celular: str = None,
        plan: PlanType = None,
        observaciones: str = None,
        fecha_fin_desde: date = None,
        fecha_fin_hasta: date = None,
        solo_activos: bool = False,
        solo_vigentes: bool = False
    ) -> List[User]:
        """
        Busca usuarios con múltiples filtros.
        
        Args:
            nombre: Filtro por nombre (contiene)
            apellido: Filtro por apellido (contiene)
            email: Filtro por email (contiene)
            celular: Filtro por celular (contiene)
            plan: Filtro por tipo de plan
            observaciones: Filtro por observaciones (contiene)
            fecha_fin_desde: Fecha fin del plan desde
            fecha_fin_hasta: Fecha fin del plan hasta
            solo_activos: Solo usuarios activos
            solo_vigentes: Solo usuarios con plan vigente
        
        Returns:
            Lista de usuarios que coinciden con los filtros
        """
        query = self.db.query(User)
        
        if nombre:
            query = query.filter(User.nombre.ilike(f"%{nombre}%"))
        
        if apellido:
            query = query.filter(User.apellido.ilike(f"%{apellido}%"))
        
        if email:
            query = query.filter(User.email.ilike(f"%{email}%"))
        
        if celular:
            query = query.filter(User.celular.ilike(f"%{celular}%"))
        
        if plan:
            query = query.filter(User.plan == plan)
        
        if observaciones:
            query = query.filter(User.observaciones.ilike(f"%{observaciones}%"))
        
        if fecha_fin_desde:
            query = query.filter(User.fecha_fin_plan >= fecha_fin_desde)
        
        if fecha_fin_hasta:
            query = query.filter(User.fecha_fin_plan <= fecha_fin_hasta)
        
        if solo_activos:
            query = query.filter(User.activo == True)
        
        if solo_vigentes:
            query = query.filter(User.fecha_fin_plan >= date.today())
        
        return query.order_by(User.apellido, User.nombre).all()
    
    def create(
        self,
        nombre: str,
        apellido: str,
        plan: PlanType,
        fecha_inicio_plan: date,
        email: str = None,
        celular: str = None,
        observaciones: str = None,
        rfid_uid: str = None,
        activo: bool = True,
        metodo_pago: PaymentMethod = PaymentMethod.EFECTIVO
    ) -> User:
        """
        Crea un nuevo usuario.
        
        Args:
            nombre: Nombre del usuario
            apellido: Apellido del usuario
            plan: Tipo de plan
            fecha_inicio_plan: Fecha de inicio del plan
            email: Email (opcional)
            celular: Celular (opcional)
            observaciones: Observaciones (opcional)
            rfid_uid: UID de tarjeta RFID (opcional)
            activo: Estado activo (default True)
            metodo_pago: Método de pago (default Efectivo)
        
        Returns:
            Usuario creado
        """
        fecha_fin_plan = calcular_fecha_fin(fecha_inicio_plan, plan)
        
        user = User(
            nombre=nombre,
            apellido=apellido,
            email=email,
            celular=celular,
            observaciones=observaciones,
            plan=plan,
            fecha_inicio_plan=fecha_inicio_plan,
            fecha_fin_plan=fecha_fin_plan,
            rfid_uid=rfid_uid,
            activo=activo,
            metodo_pago=metodo_pago
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(
        self,
        user_id: int,
        nombre: str = None,
        apellido: str = None,
        email: str = None,
        celular: str = None,
        observaciones: str = None,
        plan: PlanType = None,
        fecha_inicio_plan: date = None,
        rfid_uid: str = None,
        activo: bool = None,
        metodo_pago: PaymentMethod = None
    ) -> Optional[User]:
        """
        Actualiza un usuario existente.
        
        Args:
            user_id: ID del usuario a actualizar
            nombre: Nuevo nombre (opcional)
            apellido: Nuevo apellido (opcional)
            email: Nuevo email (opcional)
            celular: Nuevo celular (opcional)
            observaciones: Nuevas observaciones (opcional)
            plan: Nuevo plan (opcional)
            fecha_inicio_plan: Nueva fecha inicio (opcional)
            rfid_uid: Nuevo UID RFID (opcional)
            activo: Nuevo estado activo (opcional)
            metodo_pago: Nuevo método de pago (opcional)
        
        Returns:
            Usuario actualizado o None si no existe
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        if nombre is not None:
            user.nombre = nombre
        if apellido is not None:
            user.apellido = apellido
        if email is not None:
            user.email = email
        if celular is not None:
            user.celular = celular
        if observaciones is not None:
            user.observaciones = observaciones
        if rfid_uid is not None:
            user.rfid_uid = rfid_uid if rfid_uid else None
        if activo is not None:
            user.activo = activo
        if metodo_pago is not None:
            user.metodo_pago = metodo_pago
        
        # Si se cambia el plan o fecha inicio, recalcular fecha fin
        if plan is not None or fecha_inicio_plan is not None:
            new_plan = plan if plan is not None else user.plan
            new_fecha_inicio = fecha_inicio_plan if fecha_inicio_plan is not None else user.fecha_inicio_plan
            user.plan = new_plan
            user.fecha_inicio_plan = new_fecha_inicio
            user.fecha_fin_plan = calcular_fecha_fin(new_fecha_inicio, new_plan)
        
        user.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """
        Elimina un usuario.
        
        Args:
            user_id: ID del usuario a eliminar
        
        Returns:
            True si se eliminó, False si no existía
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def assign_rfid(self, user_id: int, rfid_uid: str) -> Optional[User]:
        """
        Asigna una tarjeta RFID a un usuario.
        
        Args:
            user_id: ID del usuario
            rfid_uid: UID de la tarjeta RFID
        
        Returns:
            Usuario actualizado o None si el UID ya está asignado
        """
        # Verificar que no esté asignada a otro usuario
        existing = self.get_by_rfid(rfid_uid)
        if existing and existing.id != user_id:
            return None
        
        return self.update(user_id, rfid_uid=rfid_uid)
    
    def remove_rfid(self, user_id: int) -> Optional[User]:
        """Remueve la tarjeta RFID de un usuario."""
        return self.update(user_id, rfid_uid="")
    
    def deactivate_expired_plans(self) -> int:
        """
        Desactiva usuarios cuyos planes han vencido.
        
        Returns:
            Cantidad de usuarios desactivados
        """
        today = date.today()
        expired_users = (
            self.db.query(User)
            .filter(User.activo == True)
            .filter(User.fecha_fin_plan < today)
            .all()
        )
        
        count = 0
        for user in expired_users:
            user.activo = False
            user.updated_at = datetime.now()
            count += 1
        
        if count > 0:
            self.db.commit()
        
        return count


class AccessLogRepository:
    """Repositorio para operaciones con registros de acceso."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, limit: int = 100) -> List[AccessLog]:
        """Obtiene los últimos registros de acceso."""
        return (
            self.db.query(AccessLog)
            .order_by(AccessLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    def get_by_user(self, user_id: int, limit: int = 50) -> List[AccessLog]:
        """Obtiene los registros de acceso de un usuario."""
        return (
            self.db.query(AccessLog)
            .filter(AccessLog.user_id == user_id)
            .order_by(AccessLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    def get_by_rfid(self, rfid_uid: str, limit: int = 50) -> List[AccessLog]:
        """Obtiene los registros de acceso por UID de tarjeta."""
        return (
            self.db.query(AccessLog)
            .filter(AccessLog.rfid_uid == rfid_uid)
            .order_by(AccessLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    def search(
        self,
        fecha_desde: datetime = None,
        fecha_hasta: datetime = None,
        resultado: AccessResult = None,
        user_id: int = None,
        rfid_uid: str = None,
        limit: int = 500
    ) -> List[AccessLog]:
        """
        Busca registros de acceso con filtros.
        
        Args:
            fecha_desde: Fecha/hora desde
            fecha_hasta: Fecha/hora hasta
            resultado: Filtrar por resultado (permitido/denegado)
            user_id: Filtrar por usuario
            rfid_uid: Filtrar por UID RFID
            limit: Límite de resultados
        
        Returns:
            Lista de registros de acceso
        """
        query = self.db.query(AccessLog)
        
        if fecha_desde:
            query = query.filter(AccessLog.timestamp >= fecha_desde)
        
        if fecha_hasta:
            query = query.filter(AccessLog.timestamp <= fecha_hasta)
        
        if resultado:
            query = query.filter(AccessLog.resultado == resultado)
        
        if user_id:
            query = query.filter(AccessLog.user_id == user_id)
        
        if rfid_uid:
            query = query.filter(AccessLog.rfid_uid.ilike(f"%{rfid_uid}%"))
        
        return query.order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    def create(
        self,
        rfid_uid: str,
        resultado: AccessResult,
        motivo: AccessReason,
        user_id: int = None
    ) -> AccessLog:
        """
        Crea un nuevo registro de acceso.
        
        Args:
            rfid_uid: UID de la tarjeta RFID
            resultado: Resultado del acceso
            motivo: Motivo del resultado
            user_id: ID del usuario (opcional)
        
        Returns:
            Registro de acceso creado
        """
        log = AccessLog(
            rfid_uid=rfid_uid,
            resultado=resultado,
            motivo=motivo,
            user_id=user_id,
            timestamp=datetime.now()
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_stats(self, fecha_desde: date = None, fecha_hasta: date = None) -> dict:
        """
        Obtiene estadísticas de acceso.
        
        Args:
            fecha_desde: Fecha desde
            fecha_hasta: Fecha hasta
        
        Returns:
            Diccionario con estadísticas
        """
        query = self.db.query(AccessLog)
        
        if fecha_desde:
            query = query.filter(AccessLog.timestamp >= datetime.combine(fecha_desde, datetime.min.time()))
        
        if fecha_hasta:
            query = query.filter(AccessLog.timestamp <= datetime.combine(fecha_hasta, datetime.max.time()))
        
        logs = query.all()
        
        total = len(logs)
        permitidos = sum(1 for log in logs if log.resultado == AccessResult.PERMITIDO)
        denegados = total - permitidos
        
        return {
            "total": total,
            "permitidos": permitidos,
            "denegados": denegados,
            "tasa_acceso": (permitidos / total * 100) if total > 0 else 0
        }
