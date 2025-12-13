#!/usr/bin/env python3
"""
DEBUG COMPLETO DEL BACKEND - Simulador de Rutas PWA
Guarda este archivo en la raÃ­z del proyecto (sr_pwa/)
"""

import sys
import os
from pathlib import Path

def print_section(title, char="="):
    """Imprime una secciÃ³n con formato"""
    line = char * 60
    print(f"\n{line}")
    print(f" {title}")
    print(f"{line}")

def main():
    print_section("DIAGNÃ“STICO COMPLETO DEL BACKEND - SIMULADOR RUTAS PWA")
    
    # Configurar path
    current_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(current_dir))
    
    # ========== 1. VERIFICAR ESTRUCTURA ==========
    print_section("1. ESTRUCTURA DE CARPETAS", "-")
    
    folders_to_check = [
        current_dir / "backend",
        current_dir / "backend/core",
        current_dir / "backend/API",
        current_dir / "backend/API/routers",
        current_dir / "database",
        current_dir / "frontend"
    ]
    
    for folder in folders_to_check:
        status = "âœ…" if folder.exists() else "âŒ"
        print(f"{status} {folder.relative_to(current_dir)}")
    
    # ========== 2. VERIFICAR ARCHIVOS CRÃTICOS ==========
    print_section("2. ARCHIVOS CRÃTICOS", "-")
    
    critical_files = [
        (current_dir / ".env", "Variables de entorno"),
        (current_dir / "requirements.txt", "Dependencias"),
        (current_dir / "backend/core/dijkstra.py", "LÃ³gica Dijkstra"),
        (current_dir / "backend/core/calculos.py", "CÃ¡lculos logÃ­sticos"),
        (current_dir / "backend/core/simulacion.py", "GeneraciÃ³n mapas"),
        (current_dir / "backend/API/main.py", "API FastAPI"),
        (current_dir / "backend/API/dependencies.py", "ConexiÃ³n BD"),
        (current_dir / "database/schema_mysql.sql", "Esquema BD"),
    ]
    
    for file_path, description in critical_files:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"âœ… {description:25} ({size} bytes)")
        else:
            print(f"âŒ {description:25} NO ENCONTRADO")
    
    # ========== 3. VERIFICAR DEPENDENCIAS ==========
    print_section("3. DEPENDENCIAS PYTHON", "-")
    
    required_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("requests", "Requests"),
        ("networkx", "NetworkX"),
        ("folium", "Folium"),
        ("pydantic", "Pydantic"),
        ("pymysql", "PyMySQL"),
        ("dotenv", "python-dotenv"),
    ]
    
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"âœ… {display_name:15} instalado")
        except ImportError:
            print(f"âŒ {display_name:15} FALTA")
    
    # ========== 4. VERIFICAR IMPORTS DE MÃ“DULOS ==========
    print_section("4. IMPORTS DE MÃ“DULOS PROPIOS", "-")
    
    modules_to_test = [
        ("backend.core.dijkstra", ["obtener_datos_ruta", "construir_grafo_logico"]),
        ("backend.core.calculos", ["calcular_pedido"]),
        ("backend.core.simulacion", ["generar_mapa_visual"]),
        ("backend.API.dependencies", ["get_db", "create_tables"]),
        ("backend.API.main", ["app"]),
    ]
    
    for module_name, functions in modules_to_test:
        try:
            module = __import__(module_name, fromlist=functions)
            for func in functions:
                if hasattr(module, func):
                    print(f"âœ… {module_name}.{func}")
                else:
                    print(f"âŒ {module_name}.{func} (no encontrado)")
        except Exception as e:
            print(f"âŒ Error importando {module_name}: {str(e)[:50]}")
    
    # ========== 5. VERIFICAR VARIABLES DE ENTORNO ==========
    print_section("5. VARIABLES DE ENTORNO", "-")
    
    env_file = current_dir / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_file)
        
        env_vars = [
            ("MAPQUEST_API_KEY", "API MapQuest"),
            ("DB_HOST", "Host BD"),
            ("DB_NAME", "Nombre BD"),
            ("DB_USER", "Usuario BD"),
        ]
        
        for var_name, description in env_vars:
            value = os.getenv(var_name)
            if value:
                masked = value[:4] + "***" + value[-4:] if len(value) > 8 else "***"
                print(f"âœ… {description:15} = {masked}")
            else:
                print(f"âŒ {description:15} NO DEFINIDA")
    else:
        print("âš ï¸  Archivo .env no encontrado")
    
    # ========== 6. VERIFICAR CONEXIÃ“N BD ==========
    print_section("6. CONEXIÃ“N BASE DE DATOS", "-")
    
    try:
        from backend.API.dependencies import engine
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print(f"âœ… BD conectada: {engine.url.database}")
    except Exception as e:
        print(f"âŒ Error BD: {str(e)[:80]}")
    
    # ========== 7. RESUMEN FINAL ==========
    print_section("RESUMEN FINAL", "=")
    print("ðŸŽ¯ SI TODOS LOS PUNTOS 1-6 MUESTRAN âœ…:")
    print("   Â¡BACKEND COMPLETAMENTE FUNCIONAL!")
    print("")
    print("ðŸš€ COMANDO PARA INICIAR API:")
    print("   uvicorn backend.API.main:app --reload --port 8000")
    print("")
    print("ðŸ”— DOCUMENTACIÃ“N:")
    print("   http://localhost:8000/docs")
    print("")
    print("ðŸ› ï¸  ENDPOINT PRINCIPAL PARA PROBAR:")
    print("   POST http://localhost:8000/ruta/calcular")

if __name__ == "__main__":
    main()
