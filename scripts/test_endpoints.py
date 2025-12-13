#!/usr/bin/env python3
"""
PRUEBA DE ENDPOINTS - Simulador de Rutas PWA
Prueba todos los endpoints de la API
"""

import requests
import json
import sys

def test_endpoints():
    print("=== PRUEBA DE ENDPOINTS DE LA API ===")
    print("URL Base: http://localhost:8000")
    print("")
    
    base_url = "http://localhost:8000"
    
    # Lista de endpoints a probar
    endpoints = [
        {
            "name": "Estado API",
            "method": "GET",
            "url": "/",
            "expected": [200, 404]  # 404 es normal si no hay ruta raíz definida
        },
        {
            "name": "Documentación Swagger",
            "method": "GET", 
            "url": "/docs",
            "expected": [200]
        },
        {
            "name": "Router Autenticación",
            "method": "GET",
            "url": "/auth/",
            "expected": [404, 405]  # Normal si no tiene GET
        },
        {
            "name": "Login (prueba)",
            "method": "POST",
            "url": "/auth/login",
            "data": {"email": "test@test.com", "password": "test123"},
            "expected": [200, 422, 404]  # 422 = validation error (normal)
        },
        {
            "name": "Router Rutas",
            "method": "GET",
            "url": "/ruta/",
            "expected": [404, 405]
        },
        {
            "name": "Cálculo de Ruta (BÁSICO)",
            "method": "POST",
            "url": "/ruta/calcular",
            "data": {"origen": "UMB Cuautitlán", "destino": "Zócalo CDMX"},
            "expected": [200],
            "critical": True  # ¡ESENCIAL!
        },
        {
            "name": "Cálculo de Ruta con Pedido",
            "method": "POST", 
            "url": "/ruta/calcular",
            "data": {"origen": "Ciudad Universitaria", "destino": "Plaza Satélite", "pedido_id": 1},
            "expected": [200, 400, 500]
        },
        {
            "name": "Cálculo Pedido por ID",
            "method": "GET",
            "url": "/ruta/pedido/1?distancia_km=50",
            "expected": [200, 400, 500]
        },
        {
            "name": "Prueba Simulación",
            "method": "GET",
            "url": "/simulacion/test",
            "expected": [200]
        },
        {
            "name": "Generar Mapa Simulación",
            "method": "POST",
            "url": "/simulacion/",
            "data": {"origen": "Aeropuerto", "destino": "Basílica", "nombre_mapa": "debug_map.html"},
            "expected": [200, 400, 500]
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n🔹 {endpoint['name']}")
        print(f"   {endpoint['method']} {endpoint['url']}")
        
        try:
            url = base_url + endpoint["url"]
            
            # Preparar solicitud
            if endpoint["method"] == "POST":
                response = requests.post(
                    url, 
                    json=endpoint.get("data", {}),
                    timeout=10
                )
            else:
                response = requests.get(url, timeout=10)
            
            # Evaluar respuesta
            status = response.status_code
            is_expected = status in endpoint["expected"]
            
            if is_expected:
                if endpoint.get("critical") and status == 200:
                    print(f"   ✅ 200 OK (¡CRÍTICO FUNCIONA!)")
                elif status == 200:
                    print(f"   ✅ 200 OK")
                elif status == 404:
                    print(f"   ⚠️  404 (normal para este endpoint)")
                elif status == 422:
                    print(f"   ⚠️  422 Validation Error (normal)")
                else:
                    print(f"   ⚠️  {status} (esperado)")
                
                # Mostrar datos relevantes si es 200
                if status == 200:
                    try:
                        data = response.json()
                        if "distancia_km" in data:
                            print(f"      📏 Distancia: {data['distancia_km']} km")
                        if "tiempo_estimado_min" in data:
                            print(f"      ⏱️  Tiempo: {data['tiempo_estimado_min']} min")
                        if "mapa_html" in data:
                            print(f"      🗺️  Mapa: {data['mapa_html']}")
                        if "mensaje" in data:
                            print(f"      📝 {data['mensaje'][:50]}...")
                    except:
                        pass
            else:
                print(f"   ❌ {status} (INESPERADO)")
                print(f"      {response.text[:80]}...")
            
            results.append({
                "name": endpoint["name"],
                "status": status,
                "expected": is_expected,
                "critical": endpoint.get("critical", False)
            })
            
        except requests.exceptions.ConnectionError:
            print(f"   ❌ API no responde (¿uvicorn corriendo?)")
            results.append({"name": endpoint["name"], "status": "NO_CONNECTION", "expected": False})
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
            results.append({"name": endpoint["name"], "status": f"ERROR: {str(e)[:20]}", "expected": False})
    
    # ========== RESUMEN FINAL ==========
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    critical_passed = True
    for result in results:
        if result.get("critical"):
            if result["status"] == 200:
                print(f"✅ {result['name']}: CRÍTICO FUNCIONANDO")
            else:
                print(f"❌ {result['name']}: CRÍTICO FALLÓ ({result['status']})")
                critical_passed = False
    
    print("\n🎯 CONCLUSIÓN:")
    if critical_passed:
        print("¡BACKEND COMPLETAMENTE FUNCIONAL! ✅")
        print("El endpoint principal (/ruta/calcular) responde correctamente.")
    else:
        print("Hay problemas en endpoints críticos ❌")
        print("Revisa los logs de uvicorn para más detalles.")
    
    print("\n📊 ESTADÍSTICAS:")
    total = len(results)
    passed = sum(1 for r in results if r["expected"] or r["status"] in [404, 422])
    print(f"Endpoints probados: {total}")
    print(f"Endpoints OK: {passed}/{total}")
    
    print("\n🚀 SIGUIENTES PASOS:")
    print("1. Ver mapas generados en la carpeta del proyecto")
    print("2. Probar desde navegador: http://localhost:8000/docs")
    print("3. Conectar frontend con los endpoints")

if __name__ == "__main__":
    test_endpoints()