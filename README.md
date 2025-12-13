PROYECTO TERCER SEMESTRE
SIMULADOR DE RUTAS DE DISTRIBUCION ENFOCADO EN TIEMPO COSTO Y ENERGIA
Hola!!
Leeer y ejecutar Scripts para debuguear

# Diagnóstico completo

python debug_backend.py

# Probar todos los endpoints (API debe estar corriendo)

python test_endpoints.py

# Verificación rápida

python quick_check.py

# servidor local host

uvicorn backend.API.main:app --reload --port 8000 / http://localhost:8000/docs
