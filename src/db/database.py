"""
Configuración de conexión a la base de datos SQLite.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import DATABASE_URL
from src.db.models import Base


# Motor de base de datos (singleton)
_engine = None
_SessionLocal = None


def get_engine():
    """Obtiene o crea el motor de base de datos."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            echo=False,  # Cambiar a True para ver queries SQL
            connect_args={"check_same_thread": False}  # Necesario para SQLite con threads
        )
    return _engine


def get_session_factory():
    """Obtiene o crea la fábrica de sesiones."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db() -> Session:
    """
    Obtiene una nueva sesión de base de datos.
    
    Returns:
        Session: Sesión de SQLAlchemy
    
    Usage:
        db = get_db()
        try:
            # usar db
        finally:
            db.close()
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


def init_db():
    """
    Inicializa la base de datos creando todas las tablas.
    Debe llamarse al iniciar la aplicación.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print(f"Base de datos inicializada en: {DATABASE_URL}")


def close_db():
    """Cierra la conexión a la base de datos."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
