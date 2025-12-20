# scripts/vehiculos_depuracion_crist.py
"""
Script ESPECÍFICO para tu estructura de carpetas
C:\Users\crist\Programas\clon\sr_pwa\backend\API
"""
import sys
import os
import requests
import json
from pathlib import Path

# Configurar para TU estructura específica
# Tu carpeta scripts está en: C:\Users\crist\Programas\clon\sr_pwa\scripts
# Tu API está en: C:\Users\crist\Programas\clon\sr_pwa\backend\API
SCRIPT_DIR = Path(__file__).parent.absolute()  # C:\...\scripts
BASE_DIR = SCRIPT_DIR.parent / "backend" / "API"  # C:\...\backend\API
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/vehiculos"

# Agregar el directorio al path para imports
sys.path.append(str(BASE_DIR))

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def verificar_estructura():
    """Verifica tu estructura de carpetas específica"""
    print_header("📁 TU ESTRUCTURA DE CARPETAS")
    
    print(f"📍 Directorio scripts: {SCRIPT_DIR}")
    print(f"📍 Directorio API: {BASE_DIR}")
    
    if not BASE_DIR.exists():
        print(f"❌ ERROR: No se encuentra la carpeta API en: {BASE_DIR}")
        print("💡 Verifica que la ruta sea correcta")
        return False
    
    print(f"✅ Carpeta API encontrada")
    
    archivos_importantes = [
        ("main.py", "Archivo principal FastAPI"),
        ("database.py", "Conexión a BD"),
        ("routers/", "Carpeta de routers"),
        ("routers/vehiculos_router.py", "Router de vehículos"),
        (".env", "Variables de entorno"),
    ]
    
    todos_ok = True
    for archivo, descripcion in archivos_importantes:
        ruta = BASE_DIR / archivo
        if ruta.exists():
            print(f"✅ {descripcion}: {ruta.name}")
        else:
            print(f"❌ {descripcion}: NO ENCONTRADO")
            print(f"   Ruta esperada: {ruta}")
            todos_ok = False
    
    return todos_ok

def test_database_connection():
    """Prueba la conexión a tu database.py específico"""
    print_header("🔗 CONEXIÓN A DATABASE.PY")
    
    db_path = BASE_DIR / "database.py"
    
    if not db_path.exists():
        print("❌ database.py no encontrado en la ruta esperada")
        return False
    
    print(f"✅ database.py encontrado en: {db_path}")
    
    try:
        # Leer el contenido
        with open(db_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar contenido crítico
        checks = [
            ("DATABASE_URL", "Variable de conexión"),
            ("get_db", "Función para obtener sesión"),
            ("SessionLocal", "Session maker"),
            ("create_engine", "Motor SQLAlchemy"),
        ]
        
        print("📋 Contenido verificado:")
        for texto, descripcion in checks:
            if texto in contenido:
                print(f"   ✅ {descripcion}")
            else:
                print(f"   ❌ {descripcion} (no encontrado)")
        
        # Verificar URL de Neon
        import re
        url_match = re.search(r"DATABASE_URL\s*=\s*['\"]([^'\"]+)['\"]", contenido)
        if url_match:
            url = url_match.group(1)
            print(f"\n🔗 DATABASE_URL encontrada:")
            print(f"   {url}")
            if "neon.tech" in url:
                print("   ✅ Es una URL de Neon PostgreSQL")
            else:
                print("   ⚠️  No parece una URL de Neon")
        else:
            print("   ❌ No se encontró DATABASE_URL en el archivo")
            print("💡 Revisa tu archivo .env")
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo database.py: {e}")
        return False

def test_servidor():
    """Prueba si el servidor está corriendo"""
    print_header("🚀 PRUEBA DE SERVIDOR FASTAPI")
    
    print(f"🌐 URL del servidor: {BASE_URL}")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Servidor respondiendo: Status {response.status_code}")
        
        try:
            data = response.json()
            print(f"   Mensaje: {data}")
        except:
            print(f"   Respuesta: {response.text[:100]}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al servidor en {BASE_URL}")
        print("\n💡 El servidor NO está corriendo.")
        print("📌 Ejecuta en una NUEVA terminal:")
        print(f"   cd \"{BASE_DIR}\"")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_endpoints_vehiculos():
    """Prueba los endpoints de vehículos"""
    print_header("📡 TESTEO DE ENDPOINTS DE VEHÍCULOS")
    
    endpoints = [
        ("Test", "/api/vehiculos/test/", "Verifica que el router funciona"),
        ("Todos vehículos", "/api/vehiculos/", "Lista todos los vehículos"),
        ("Vehículos disponibles", "/api/vehiculos/disponibles/", "Vehículos sin asignar"),
        ("Repartidores", "/api/vehiculos/repartidores/", "Lista repartidores"),
        ("Asignaciones", "/api/vehiculos/asignaciones/", "Todas las asignaciones"),
    ]
    
    for nombre, endpoint, descripcion in endpoints:
        url = BASE_URL + endpoint
        print(f"\n🔍 {nombre}")
        print(f"   Descripción: {descripcion}")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ OK - Endpoint funcionando")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 Elementos: {len(data)}")
                    elif isinstance(data, dict):
                        if 'repartidores' in data:
                            print(f"   📊 {len(data['repartidores'])} repartidores")
                        elif 'vehiculos_disponibles' in data:
                            print(f"   📊 {len(data['vehiculos_disponibles'])} vehículos disponibles")
                        elif 'asignaciones' in data:
                            print(f"   📊 {len(data['asignaciones'])} asignaciones")
                except:
                    print(f"   📊 Respuesta: {response.text[:50]}")
                    
            elif response.status_code == 404:
                print("   ❌ 404 - Endpoint no encontrado")
                print("   💡 Problemas posibles:")
                print("      1. Router no incluido en main.py")
                print("      2. Endpoint no existe en vehiculos_router.py")
                print("      3. Prefijo incorrecto en main.py")
            else:
                print(f"   ❌ {response.status_code} - {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ No se pudo conectar (servidor caído)")
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {str(e)[:50]}")

def verificar_main_py():
    """Verifica tu main.py específico"""
    print_header("🔍 ANALIZANDO MAIN.PY")
    
    main_path = BASE_DIR / "main.py"
    
    if not main_path.exists():
        print("❌ main.py no encontrado")
        return False
    
    print(f"✅ main.py encontrado en: {main_path}")
    
    try:
        with open(main_path, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        # Buscar importaciones críticas
        print("\n📦 IMPORTACIONES ENCONTRADAS:")
        imports_vehiculos = False
        for i, linea in enumerate(lineas):
            linea_limpia = linea.strip()
            if 'import' in linea_limpia or 'from' in linea_limpia:
                if 'vehiculos_router' in linea_limpia or 'vehiculos' in linea_limpia:
                    print(f"   ✅ Línea {i+1}: {linea_limpia}")
                    imports_vehiculos = True
                elif 'router' in linea_limpia:
                    print(f"   📌 Línea {i+1}: {linea_limpia}")
        
        if not imports_vehiculos:
            print("   ❌ No se encontró importación de vehiculos_router")
        
        # Buscar inclusión del router
        print("\n🔗 INCLUSIÓN DE ROUTERS:")
        router_incluido = False
        prefijo_correcto = False
        for i, linea in enumerate(lineas):
            linea_limpia = linea.strip()
            if 'include_router' in linea_limpia:
                print(f"   Línea {i+1}: {linea_limpia}")
                if 'vehiculos' in linea_limpia:
                    router_incluido = True
                if 'prefix="/api/vehiculos"' in linea_limpia:
                    prefijo_correcto = True
        
        if not router_incluido:
            print("   ❌ No se encontró app.include_router para vehículos")
        
        if not prefijo_correcto:
            print("   ⚠️  Prefijo puede ser incorrecto")
        
        # Verificar CORS
        print("\n🌐 CONFIGURACIÓN CORS:")
        cors_encontrado = False
        for i, linea in enumerate(lineas):
            if 'CORS' in linea or 'cors' in linea or 'CORSMiddleware' in linea:
                print(f"   Línea {i+1}: {linea.strip()}")
                cors_encontrado = True
        
        if not cors_encontrado:
            print("   ⚠️  No se encontró configuración CORS")
            print("   💡 Agrega CORS para que el frontend funcione")
        
        return imports_vehiculos and router_incluido
        
    except Exception as e:
        print(f"❌ Error leyendo main.py: {e}")
        return False

def verificar_vehiculos_router():
    """Verifica el router de vehículos"""
    print_header("🛠️  ANALIZANDO VEHICULOS_ROUTER.PY")
    
    router_path = BASE_DIR / "routers" / "vehiculos_router.py"
    
    if not router_path.exists():
        print("❌ vehiculos_router.py no encontrado")
        print(f"   Ruta esperada: {router_path}")
        return False
    
    print(f"✅ Router encontrado en: {router_path}")
    
    try:
        with open(router_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Contar endpoints
        endpoints = [
            ('@router.get("/")', 'GET todos vehículos'),
            ('@router.post("/")', 'POST crear vehículo'),
            ('@router.get("/disponibles/")', 'GET vehículos disponibles'),
            ('@router.get("/repartidores/")', 'GET repartidores'),
            ('@router.get("/asignaciones/")', 'GET asignaciones'),
            ('@router.post("/asignaciones/")', 'POST crear asignación'),
            ('@router.put("/asignaciones/', 'PUT liberar asignación'),
        ]
        
        print("\n📋 ENDPOINTS ENCONTRADOS:")
        encontrados = 0
        for endpoint, desc in endpoints:
            if endpoint in contenido:
                print(f"   ✅ {desc}")
                encontrados += 1
            else:
                print(f"   ❌ {desc} (no encontrado)")
        
        print(f"\n📊 Resumen: {encontrados}/{len(endpoints)} endpoints")
        
        if encontrados < 3:
            print("⚠️  Muy pocos endpoints - Revisa tu vehiculos_router.py")
        
        return encontrados > 0
        
    except Exception as e:
        print(f"❌ Error leyendo router: {e}")
        return False

def test_frontend_config():
    """Verifica la configuración del frontend"""
    print_header("🌐 CONFIGURACIÓN DEL FRONTEND")
    
    # Buscar configuracion.html (relativo a scripts/)
    posibles_rutas = [
        SCRIPT_DIR.parent / "configuracion.html",  # C:\...\sr_pwa\
        SCRIPT_DIR.parent / "backend" / "configuracion.html",
        BASE_DIR / "configuracion.html",
    ]
    
    frontend_path = None
    for ruta in posibles_rutas:
        if ruta.exists():
            frontend_path = ruta
            break
    
    if not frontend_path:
        print("❌ configuracion.html no encontrado")
        print("💡 Busca manualmente en:")
        for ruta in posibles_rutas:
            print(f"   - {ruta}")
        return False
    
    print(f"✅ configuracion.html encontrado en: {frontend_path}")
    
    try:
        with open(frontend_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar URL de API
        print("\n🔗 CONFIGURACIÓN API:")
        api_base_line = None
        for linea in contenido.split('\n'):
            if 'API_BASE' in linea and '=' in linea:
                api_base_line = linea.strip()
                print(f"   📌 {api_base_line}")
                break
        
        if not api_base_line:
            print("   ❌ No se encontró API_BASE en el archivo")
        
        # Verificar errores comunes
        errores = []
        if 'https://localhost' in contenido:
            errores.append("Usa HTTPS en localhost (debe ser HTTP)")
        if 'API_BASE_URL' in contenido and 'API_BASE' not in contenido:
            errores.append("Variable debería ser API_BASE, no API_BASE_URL")
        if 'localhost:8000/api/vehiculos' not in contenido:
            errores.append("URL de API puede ser incorrecta")
        
        if errores:
            print("\n⚠️  POSIBLES ERRORES:")
            for error in errores:
                print(f"   ❌ {error}")
        else:
            print("   ✅ Configuración API parece correcta")
        
        # Verificar funciones fetch
        print("\n📞 LLAMADAS FETCH ENCONTRADAS:")
        fetch_count = 0
        for i, linea in enumerate(contenido.split('\n')):
            if 'fetch' in linea and 'API_BASE' in linea:
                fetch_count += 1
                print(f"   ✅ Línea ~{i+1}: fetch encontrado")
        
        print(f"\n📊 Total llamadas fetch: {fetch_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo frontend: {e}")
        return False

def prueba_conexion_completa():
    """Prueba completa de conexión"""
    print_header("🔄 PRUEBA DE CONEXIÓN COMPLETA (Simulando navegador)")
    
    print("🔍 Esta prueba simula lo que hace tu navegador cuando abres configuracion.html")
    
    endpoints = [
        ("Repartidores", f"{API_BASE}/repartidores/", "Carga lista de repartidores"),
        ("Vehículos disponibles", f"{API_BASE}/disponibles/", "Carga vehículos para asignar"),
        ("Todos los vehículos", f"{API_BASE}/", "Carga tabla principal"),
        ("Asignaciones activas", f"{API_BASE}/asignaciones/", "Carga asignaciones para liberar"),
    ]
    
    resultados = []
    
    for nombre, url, descripcion in endpoints:
        print(f"\n📡 {nombre}")
        print(f"   Descripción: {descripcion}")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            resultados.append((nombre, response.status_code))
            
            if response.status_code == 200:
                print("   ✅ 200 OK - El navegador cargará estos datos")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 Recibió {len(data)} elementos")
                    elif isinstance(data, dict):
                        keys = list(data.keys())
                        print(f"   📊 Estructura: {keys}")
                except:
                    print(f"   📊 Respuesta: {response.text[:50]}")
                    
            elif response.status_code == 404:
                print("   ❌ 404 - El navegador mostrará error")
                print("   💡 Este endpoint no existe o no está bien configurado")
            else:
                print(f"   ❌ {response.status_code} - {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ No se pudo conectar - Servidor no está corriendo")
            resultados.append((nombre, "NO_CONNECT"))
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}")
            resultados.append((nombre, "ERROR"))
    
    # Resumen
    print_header("📊 RESUMEN DE CONEXIÓN")
    exitos = sum(1 for _, status in resultados if status == 200)
    total = len(resultados)
    
    print(f"\n✅ Conexiones exitosas: {exitos}/{total}")
    
    if exitos == total:
        print("🎉 ¡Todos los endpoints funcionan! El frontend debería cargar correctamente.")
    elif exitos == 0:
        print("😞 Ningún endpoint funciona. Revisa:")
        print("   1. ¿El servidor está corriendo?")
        print("   2. ¿El router está incluido en main.py?")
        print("   3. ¿Los endpoints existen en vehiculos_router.py?")
    else:
        print("⚠️  Algunos endpoints funcionan, otros no.")
        print("   Revisa los endpoints con error específicamente.")

def generar_solucion():
    """Genera solución específica para ti"""
    print_header("🔧 SOLUCIÓN PASO A PASO")
    
    print(f"""
📍 TU ESTRUCTURA CONFIRMADA:
   Scripts: {SCRIPT_DIR}
   API: {BASE_DIR}

📌 PASOS PARA ARREGLAR:

1. 🚀 INICIAR SERVIDOR (Terminal 1):
   Abre una NUEVA terminal como Administrador y ejecuta:
   
   cd "{BASE_DIR}"
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   Debes ver: "Uvicorn running on http://127.0.0.1:8000"

2. 🔍 VERIFICAR ENDPOINTS (Terminal 2):
   En OTRA terminal, ejecuta:
   
   cd "{SCRIPT_DIR}"
   python vehiculos_depuracion_crist.py
   
   Revisa qué endpoints fallan.

3. 📝 CORREGIR MAIN.PY SI ES NECESARIO:
   Asegúrate que main.py tenga:
   
   from routers import vehiculos_router
   app.include_router(vehiculos_router.router, prefix="/api/vehiculos")

4. 🌐 CONFIGURAR CORS (si no está):
   En main.py agrega al inicio:
   
   from fastapi.middleware.cors import CORSMiddleware
   
   Y después de app = FastAPI():
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

5. 📱 PROBAR FRONTEND:
   Abre en tu navegador:
   file:///C:/Users/crist/Programas/clon/sr_pwa/configuracion.html
   
   Presiona F12 → Consola para ver errores.

🔥 COMANDOS RÁPIDOS:
   Terminal 1 (Servidor): cd "{BASE_DIR}" && uvicorn main:app --reload
   Terminal 2 (Tests): cd "{SCRIPT_DIR}" && python vehiculos_depuracion_crist.py
""")

def main():
    """Función principal"""
    print("🚚 DEPURACIÓN COMPLETA - SISTEMA DE VEHÍCULOS")
    print("="*60)
    print(f"📍 Desde scripts: {SCRIPT_DIR}")
    print(f"📍 Hacia API: {BASE_DIR}")
    
    # Verificar estructura primero
    if not verificar_estructura():
        print("\n❌ Estructura de carpetas incorrecta.")
        print("💡 Asegúrate que la carpeta API exista en la ruta esperada")
        return
    
    # Ejecutar verificaciones
    test_database_connection()
    servidor_ok = test_servidor()
    
    if servidor_ok:
        test_endpoints_vehiculos()
        prueba_conexion_completa()
    else:
        print("\n⚠️  No se pueden probar endpoints sin servidor")
    
    verificar_main_py()
    verificar_vehiculos_router()
    test_frontend_config()
    
    # Generar solución
    generar_solucion()
    
    print_header("🎯 RESUMEN FINAL")
    print("""
Sigue estos pasos en orden:

1. ✅ Verifica que la estructura de carpetas sea correcta
2. 🚀 Inicia el servidor FastAPI en una terminal
3. 🔍 Ejecuta este script para verificar endpoints
4. 📝 Corrige lo que el script indique
5. 🌐 Prueba el frontend en el navegador

📌 Si ves errores específicos, compártelos para ayudarte mejor.
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Depuración interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()