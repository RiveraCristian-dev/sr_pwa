# test_neon_directo.py (crea en la raíz)
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada")
    exit()

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"✅ PostgreSQL conectado: {result.fetchone()[0]}")
        
        # Ver tablas
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tablas = [row[0] for row in result]
        print(f"📊 Tablas en Neon: {tablas}")
        
except Exception as e:
    print(f"❌ Error de conexión: {e}")