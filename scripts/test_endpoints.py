#!/usr/bin/env python3
"""
PRUEBA DE ENDPOINTS - Simulador de Rutas PWA

"""

import requests
import sys

def test_endpoints():
    print("=== PRUEBA DE ENDPOINTS DE LA API ===")
    print("URL Base: http://localhost:8000")
    print("")
    
    base_url = "http://localhost:8000"
    
    tests = [
        ("Estado API", "GET", "/", None, [200, 404]),
        ("Documentacion Swagger", "GET", "/docs", None, [200]),
        ("Router Autenticacion", "GET", "/auth/", None, [404, 405]),
        ("Router Rutas", "GET", "/ruta/", None, [404, 405]),
        ("Prueba Simulacion", "GET", "/simulacion/test", None, [200]),
    ]
    
    for name, method, url, data, expected in tests:
        print(f"-> {name}")
        print(f"   {method} {url}")
        
        try:
            if method == "POST" and data:
                resp = requests.post(base_url + url, json=data, timeout=5)
            else:
                resp = requests.request(method, base_url + url, timeout=5)
            
            if resp.status_code in expected:
                if resp.status_code == 200:
                    print(f"   [OK] 200 OK")
                elif resp.status_code == 404:
                    print(f"   [WARN] 404 (normal)")
            else:
                print(f"   [ERROR] {resp.status_code} (inesperado)")
                
        except requests.exceptions.ConnectionError:
            print(f"   [ERROR] API no responde")
        except Exception as e:
            print(f"   [ERROR] {str(e)[:30]}")
    
    print("\n" + "="*60)
    print("PARA PRUEBAS COMPLETAS:")
    print("1. Inicia servidor: uvicorn backend.API.main:app --reload")
    print("2. Abre http://localhost:8000/docs")
    print("3. Prueba POST /ruta/calcular desde Swagger")

if __name__ == "__main__":
    test_endpoints()
