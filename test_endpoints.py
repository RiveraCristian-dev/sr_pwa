print("=== VERIFICACIÓN DE ENDPOINTS ===")
print("API: http://localhost:8000")
print("")

import requests
base_url = "http://localhost:8000"

endpoints = [
    ("GET",  "/",              "Estado API"),
    ("GET",  "/docs",          "Documentación Swagger"),
    ("GET",  "/auth/",         "Router Autenticación"),
    ("POST", "/auth/login",    "Login (placeholder)"),
    ("GET",  "/ruta/",         "Router Rutas"),
    ("POST", "/ruta/calcular", "Cálculo de Ruta"),
    ("GET",  "/simulacion/test", "Prueba Simulación"),
]

for method, endpoint, description in endpoints:
    try:
        url = base_url + endpoint
        print(f"{description:25} {method:6} {endpoint:20}", end="")
        
        if method == "POST" and endpoint == "/ruta/calcular":
            # Datos reales para prueba
            response = requests.post(url, json={
                "origen": "UMB Cuautitlán",
                "destino": "Zócalo CDMX"
            }, timeout=5)
        elif method == "POST" and endpoint == "/auth/login":
            # Datos dummy para login
            response = requests.post(url, json={
                "username": "test",
                "password": "test"
            }, timeout=5)
        else:
            response = requests.request(method, url, timeout=5)
        
        if response.status_code == 200:
            print(f" ✅ 200 OK")
        elif response.status_code == 404:
            print(f" ⚠️  404 (Puede ser normal)")
        elif response.status_code == 422:
            print(f" ⚠️  422 Validation Error")
        else:
            print(f" ❌ {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f" ❌ API no responde")
    except Exception as e:
        print(f" ❌ Error: {str(e)[:30]}")

print("")
print("=== RESULTADO ===")
print("1. Si /ruta/calcular da ✅: ¡BACKEND COMPLETO!")
print("2. Si da ❌: Revisar logs de uvicorn")
print("3. Si API no responde: Verificar que uvicorn está corriendo")
