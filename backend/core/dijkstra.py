# NOMBRE DEL ARCHIVO: dijkstra.py
import requests
import networkx as nx

def obtener_ruta_multiparada(api_key, lista_lugares, optimizar=True):
    url = "http://www.mapquestapi.com/directions/v2/route"
    
    payload = {
        "locations": lista_lugares,
        "options": {
            "routeType": "fastest",
            "doReverseGeocode": False,
            "narrativeType": "text",
            "enhancedNarrative": True,
            "unit": "k",       
            "locale": "es_MX", 
            "routeOptimization": optimizar,
            "shapeFormat": "raw", 
            "generalize": 0       
        }
    }
    
    try:
        response = requests.post(f"{url}?key={api_key}", json=payload)
        data = response.json()
        
        if data["info"]["statuscode"] != 0:
            print(f"Error API: {data['info']['messages']}")
            return [], [], None, []

        todas_maniobras = []
        todos_puntos_shape = []
        
        # 1. RECUPERAR MANIOBRAS (Instrucciones)
        # Estas siempre vienen dentro de los "legs" (tramos)
        legs = data["route"]["legs"]
        for leg in legs:
            for man in leg["maneuvers"]:
                todas_maniobras.append(man)
        
        # 2. RECUPERAR GEOMETRÍA (La línea azul)
        # CORRECCIÓN: Buscamos la forma global en la raíz de 'route', no por tramos.
        # Esto es mucho más robusto.
        if "shape" in data["route"] and "shapePoints" in data["route"]["shape"]:
            shape_raw = data["route"]["shape"]["shapePoints"]
            # Convertimos la lista plana a pares (lat, lng)
            todos_puntos_shape = list(zip(shape_raw[0::2], shape_raw[1::2]))
        else:
            print("¡ALERTA! La API no devolvió geometría (shapePoints).")

        # 3. RECUPERAR ORDEN OPTIMIZADO
        orden_optimizado = []
        if "locations" in data["route"]:
            for location in data["route"]["locations"]:
                direccion = f"{location.get('street','')}, {location.get('adminArea5','')}"
                # Manejo seguro de latLng
                if 'latLng' in location:
                    latLng = (location['latLng']['lat'], location['latLng']['lng'])
                    orden_optimizado.append({'dir': direccion, 'pos': latLng})

        # 4. BOUNDING BOX
        bbox = data["route"]["boundingBox"]
        boundingBox_str = f"{bbox['ul']['lat']},{bbox['ul']['lng']},{bbox['lr']['lat']},{bbox['lr']['lng']}"
        
        return todas_maniobras, todos_puntos_shape, boundingBox_str, orden_optimizado

    except Exception as e:
        print(f"Error crítico en Dijkstra: {e}")
        return [], [], None, []

def obtener_incidencias_trafico(api_key, bounding_box):
    if not bounding_box: return []
    url = "http://www.mapquestapi.com/traffic/v2/incidents"
    params = {"key": api_key, "boundingBox": bounding_box, "filters": "construction,incidents,congestion"}
    try:
        res = requests.get(url, params=params)
        return res.json().get("incidents", [])
    except:
        return []

def construir_grafo_logico(maniobras):
    G = nx.DiGraph()
    node_counter = 0 
    for i in range(len(maniobras)):
        actual = maniobras[i]
        pos_actual = (actual['startPoint']['lat'], actual['startPoint']['lng'])
        desc = actual['narrative']
        distancia = actual['distance'] 
        G.add_node(node_counter, pos=pos_actual, desc=desc)
        if i < len(maniobras) - 1:
            G.add_edge(node_counter, node_counter + 1, weight=distancia)
        node_counter += 1
    return G