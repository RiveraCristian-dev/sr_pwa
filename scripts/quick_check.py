#!/usr/bin/env python3
"""
VERIFICACIÃ“N RÃPIDA - 30 segundos
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

print("ðŸ” VERIFICACIÃ“N RÃPIDA DEL BACKEND")
print("-" * 40)

# 1. Verificar archivos esenciales
essentials = [
    (".env", "Variables entorno"),
    ("backend/API/main.py", "API principal"),
    ("backend/core/dijkstra.py", "LÃ³gica rutas"),
    ("backend/API/dependencies.py", "ConexiÃ³n BD"),
]

all_ok = True
for file_path, desc in essentials:
    full_path = current_dir / file_path
    if full_path.exists():
        print(f"âœ… {desc}")
    else:
        print(f"âŒ {desc} - FALTANTE")
        all_ok = False

# 2. Verificar imports bÃ¡sicos
print("\nðŸ“¦ VERIFICANDO IMPORTS...")
try:
    from backend.API.main import app
    print(f"âœ… FastAPI: {app.title}")
except Exception as e:
    print(f"âŒ FastAPI: {e}")
    all_ok = False

try:
    from backend.core.dijkstra import obtener_datos_ruta
    print("âœ… MÃ³dulo dijkstra")
except Exception as e:
    print(f"âŒ Dijkstra: {e}")
    all_ok = False

# 3. Resultado final
print("\n" + "="*40)
if all_ok:
    print("ðŸŽ‰ Â¡BACKEND LISTO!")
    print("Comando para iniciar:")
    print("uvicorn backend.API.main:app --reload --port 8000")
else:
    print("âš ï¸  PROBLEMAS DETECTADOS")
    print("Ejecuta debug_backend.py para diagnÃ³stico completo")
