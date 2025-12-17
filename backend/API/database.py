# backend/API/database.py
"""
Configuración de la conexión a PostgreSQL (Neon.tech)
Este archivo es ESSENCIAL para conectar tu API con la BD
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env en la raíz del proyecto
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

# URL de conexión a Neon PostgreSQL (OBTÉN ESTA DE TU DASHBOARD DE NEON)
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar que la URL existe
if not DATABASE_URL:
    raise ValueError(
        "❌ DATABASE_URL no encontrada en .env\n"
        "1. Ve a Neon.tech → tu proyecto → Connection Details\n"
        "2. Copia la URL que empieza con: postgresql://...\n"
        "3. Pégala en tu archivo .env"
    )

# Configurar SQLAlchemy para PostgreSQL (optimizado para Neon)
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Número máximo de conexiones en el pool
    max_overflow=20,        # Conexiones extra si se necesitan
    pool_pre_ping=True,     # Verifica conexiones antes de usarlas
    pool_recycle=3600,      # Recicla conexiones cada hora (Neon tiene timeout)
    echo=False              # Cambia a True para DEBUG (ver queries SQL)
)

# Crear fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para FastAPI (se usa en los routers)
def get_db():
    """
    Provee una sesión de base de datos para cada request.
    Se cierra automáticamente al terminar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para verificar conexión
def test_connection():
    """Prueba rápida de conexión a la BD"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Conexión a Neon PostgreSQL exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print(f"📌 URL usada: {DATABASE_URL[:50]}...")  # Muestra parte de la URL
        return False