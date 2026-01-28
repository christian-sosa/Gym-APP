"""
Modelos de base de datos SQLAlchemy para BloomFitness.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.utils.enums import PlanType, AccessResult, AccessReason, PaymentMethod


class Base(DeclarativeBase):
    """Clase base para todos los modelos."""
    pass


class User(Base):
    """Modelo de usuario/miembro del gimnasio."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    celular: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Plan de membresía
    plan: Mapped[PlanType] = mapped_column(SQLEnum(PlanType), nullable=False, default=PlanType.MENSUAL)
    fecha_inicio_plan: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin_plan: Mapped[date] = mapped_column(Date, nullable=False)
    metodo_pago: Mapped[Optional[PaymentMethod]] = mapped_column(SQLEnum(PaymentMethod), nullable=True, default=PaymentMethod.EFECTIVO)
    
    # Tarjeta RFID
    rfid_uid: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    
    # Estado
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relación con accesos
    access_logs: Mapped[list["AccessLog"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, nombre='{self.nombre} {self.apellido}', plan={self.plan.value})>"
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del usuario."""
        return f"{self.nombre} {self.apellido}"
    
    @property
    def plan_vigente(self) -> bool:
        """Verifica si el plan está vigente."""
        return date.today() <= self.fecha_fin_plan
    
    @property
    def dias_restantes(self) -> int:
        """Días restantes del plan."""
        return (self.fecha_fin_plan - date.today()).days


class AccessLog(Base):
    """Modelo de registro de accesos."""
    __tablename__ = "access_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    rfid_uid: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Usuario asociado (puede ser null si la tarjeta no está registrada)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped[Optional["User"]] = relationship(back_populates="access_logs")
    
    # Resultado del acceso
    resultado: Mapped[AccessResult] = mapped_column(SQLEnum(AccessResult), nullable=False)
    motivo: Mapped[AccessReason] = mapped_column(SQLEnum(AccessReason), nullable=False)
    
    def __repr__(self) -> str:
        return f"<AccessLog(id={self.id}, rfid='{self.rfid_uid}', resultado={self.resultado.value})>"
