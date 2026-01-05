import requests
import json

API_URL = "http://localhost:8000/api"

def test_endpoints():
    print("🚀 Probando endpoints de pedidos...")
    
    # 1. Ver repartidores
    print("\n1. Repartidores:")
    response = requests.get(f"{API_URL}/pedidos/repartidores")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 2. Ver vehículos
    print("\n2. Vehículos:")
    response = requests.get(f"{API_URL}/pedidos/vehiculos")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 3. Ver estadísticas
    print("\n3. Estadísticas:")
    response = requests.get(f"{API_URL}/pedidos/estadisticas")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 4. Crear pedido
    print("\n4. Crear pedido:")
    pedido_data = {
        "numero_pedido": f"PED-TEST-001",
        "id_repartidor": 2,
        "id_vehiculo": 1,
        "destino_entrega": "Av. Principal #123, Col. Centro",
        "capacidad_paquetes": 10,
        "estado": "pendiente"
    }
    
    response = requests.post(f"{API_URL}/pedidos/crear", json=pedido_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   ✅ Pedido creado: {response.json()}")
    else:
        print(f"   ❌ Error: {response.json()}")
    
    # 5. Listar pedidos
    print("\n5. Listar pedidos:")
    response = requests.get(f"{API_URL}/pedidos/")
    print(f"   Status: {response.status_code}")
    print(f"   Total pedidos: {len(response.json())}")

if __name__ == "__main__":
    test_endpoints()