from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text  # IMPORTANTE: Añadir esta importación
from .routers import auth_router, ruta_router, simulacion_router
import os
from datetime import datetime  # Añadir para timestamp real

# Crear app FastAPI
app = FastAPI(
    title="Simulador de Rutas PWA - RutaTec",
    version="2.0",
    description="API para gestión de rutas con PostgreSQL Neon",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: ["http://localhost", "https://tudominio.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# INICIALIZACIÓN DE BASE DE DATOS POSTGRESQL
try:
    from .database import Base, engine
    
    # Crear tablas si no existen (usando tus nuevos modelos)
    print("🔄 Inicializando base de datos PostgreSQL Neon...")
    Base.metadata.create_all(bind=engine)
    
    # Verificar conexión y tablas
    with engine.connect() as conn:
        # Ver versión PostgreSQL - CORREGIDO: usar text()
        result = conn.execute(text("SELECT version()"))
        version_info = result.fetchone()[0]
        print(f"✅ PostgreSQL: {version_info.split(',')[0]}")
        
        # Ver tablas creadas - CORREGIDO: usar text()
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tablas = [row[0] for row in result.fetchall()]
        print(f"📊 Tablas disponibles: {', '.join(tablas)}")
        
except Exception as e:
    print(f"⚠️  Advertencia en inicialización BD: {e}")
    print("💡 Las tablas pueden ya existir, continuando...")

# Registrar routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(ruta_router.router, prefix="/api/ruta", tags=["Rutas y Tráfico"])
app.include_router(simulacion_router.router, prefix="/api/simulacion", tags=["Simulación"])

# Endpoints básicos
@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "message": "API Simulador de Rutas PWA - RutaTec",
        "status": "activo",
        "version": "2.0",
        "database": "PostgreSQL Neon",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/api/auth/login",
            "rutas": "/api/ruta/calcular"
        }
    }

@app.get("/health")
def health_check():
    """Verificación de salud del sistema"""
    try:
        from .database import engine
        with engine.connect() as conn:
            # CORREGIDO: usar text()
            conn.execute(text("SELECT 1"))
        db_status = "conectado"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),  # CORREGIDO: llamar a la función
        "database": db_status,
        "api_key_configured": bool(os.getenv("MAPQUEST_API_KEY")),
        "environment": "development" if os.getenv("DEBUG") == "True" else "production"
    }

@app.get("/api/status")
def api_status():
    """Estado detallado de la API"""
    db_status = "desconocido"
    try:
        from .database import engine
        with engine.connect() as conn:
            # CORREGIDO: usar text()
            conn.execute(text("SELECT 1"))
        db_status = "operacional"
    except:
        db_status = "error"
    
    return {
        "api": "operacional",
        "database": db_status,
        "mapquest_api": "configurada" if os.getenv("MAPQUEST_API_KEY") else "no configurada",
        "endpoints_activos": 3,
        "mensaje": "Sistema listo para recibir peticiones"
    }

# Nuevo endpoint para verificar tablas específicas
@app.get("/api/database/tables")
def list_tables():
    """Lista todas las tablas en la base de datos"""
    try:
        from .database import engine
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tablas = [{"nombre": row[0], "tipo": row[1]} for row in result.fetchall()]
            
        return {
            "total": len(tablas),
            "tablas": tablas
        }
    except Exception as e:
        return {"error": str(e)}