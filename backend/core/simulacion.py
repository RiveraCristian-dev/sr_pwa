# NOMBRE DEL ARCHIVO: simulacion.py
import folium
from . import dijkstra

def traducir_detalles_trafico(texto_original):
    """Traduce descripciones de tráfico del inglés al español"""
    if not texto_original or not isinstance(texto_original, str):
        return "Sin detalles disponibles"
    
    diccionario = {
        # Tipos de eventos
        "Road construction": "Construcción vial",
        "Construction work": "Trabajos de construcción",
        "Lane closed": "Carril cerrado",
        "Road closed": "Vía cerrada",
        "Accident": "Accidente",
        "Congestion": "Congestión",
        "Heavy traffic": "Tráfico pesado",
        "Slow traffic": "Tráfico lento",
        "Hazard": "Peligro en la vía",
        "Obstruction": "Obstrucción",
        "Event": "Evento especial",
        "Mass Transit": "Tránsito masivo",
        "Planned Event": "Evento programado",
        "Road Closure": "Cierre de carretera",
        "Weather": "Condiciones climáticas",
        "Miscellaneous": "Incidente misceláneo",
        "Other News": "Otras noticias",
        
        # Términos generales
        "At ": "En ",
        "Between ": "Entre ",
        " near ": " cerca de ",
        "approaching": "acercándose a",
        "vehicles": "vehículos",
        "blocked": "bloqueado",
        "minor": "leve",
        "moderate": "moderado",
        "major": "grave",
        "delay": "retraso",
        "expected": "esperado",
        "incident": "incidente",
        "clear": "despejado",
        "Detour": "Desvío",
        "reported": "reportado",
        "avoid": "evitar",
        "area": "área",
        "lane": "carril",
        "lanes": "carriles",
        "shoulder": "acotamiento",
        "shoulders": "acotamientos",
        "intersection": "intersección",
        "highway": "carretera",
        "freeway": "autopista",
        "expressway": "vía expresa",
        "roadway": "calzada",
        "bridge": "puente",
        "tunnel": "túnel",
        "overpass": "paso elevado",
        "underpass": "paso inferior",
        "exit": "salida",
        "entrance": "entrada",
        "ramp": "rampa",
        "merge": "incorporación",
        "divergence": "bifurcación",
        
        # Términos de tránsito
        "transit": "tránsito",
        "bus": "autobús",
        "train": "tren",
        "rail": "ferrocarril",
        "subway": "metro",
        "station": "estación",
        
        # Términos climáticos
        "rain": "lluvia",
        "snow": "nieve",
        "ice": "hielo",
        "fog": "niebla",
        "flood": "inundación",
        "storm": "tormenta",
        "wind": "viento",
        "visibility": "visibilidad",
        "flooding": "inundaciones",
        
        # Direcciones
        "northbound": "sentido norte",
        "southbound": "sentido sur",
        "eastbound": "sentido este",
        "westbound": "sentido oeste",
        "north": "norte",
        "south": "sur",
        "east": "este",
        "west": "oeste",
        "left": "izquierda",
        "right": "derecha",
        "center": "centro",
        
        # Tiempo
        "until": "hasta",
        "from": "desde",
        "to": "a",
        "beginning": "comienzo",
        "ending": "finalización",
        "expected to last": "se espera que dure",
        "duration": "duración",
        "hours": "horas",
        "minutes": "minutos",
        "days": "días",
        
        # Gravedad/impacto
        "severe": "severo",
        "critical": "crítico",
        "blocking": "bloqueando",
        "affecting": "afectando",
        "impacting": "impactando",
        "causing": "causando",
        "resulting in": "resultando en",
        
        # Términos de seguridad
        "emergency": "emergencia",
        "police": "policía",
        "fire": "bomberos",
        "medical": "médico",
        "response": "respuesta",
        "crew": "equipo",
        "workers": "trabajadores",
    }
    
    texto = texto_original
    
    # Primero reemplazar términos específicos manteniendo mayúsculas/minúsculas
    for en, es in diccionario.items():
        # Reemplazar manteniendo capitalización
        if en in texto:
            texto = texto.replace(en, es)
        elif en.lower() in texto.lower():
            # Encontrar la posición y mantener capitalización original
            inicio = texto.lower().find(en.lower())
            if inicio != -1:
                # Reemplazar manteniendo el caso original
                texto = texto[:inicio] + es + texto[inicio + len(en):]
    
    # Si no hubo traducciones significativas, intentar con enfoque más simple
    if texto == texto_original:
        # Reemplazo simple ignorando mayúsculas/minúsculas
        for en, es in diccionario.items():
            texto = texto.replace(en, es).replace(en.lower(), es.lower())
    
    # Limpiar espacios dobles
    texto = ' '.join(texto.split())
    
    # Capitalizar primera letra
    if texto and len(texto) > 0:
        texto = texto[0].upper() + texto[1:]
    
    return texto

def generar_mapa_visual(G, ruta_geometria, incidentes, paradas_ordenadas, nombre_archivo="simulacion_logistica.html"):
    if not G or not ruta_geometria: 
        print("Datos insuficientes para generar mapa.")
        return

    # Límites CDMX/Edomex
    sw = [18.80, -100.20] 
    ne = [20.20, -98.80]
    centro = [(sw[0]+ne[0])/2, (sw[1]+ne[1])/2]

    mapa = folium.Map(location=centro, zoom_start=11, tiles='OpenStreetMap',
                      min_zoom=9, max_bounds=True, min_lat=sw[0], max_lat=ne[0], min_lon=sw[1], max_lon=ne[1])

    # Ruta Azul
    folium.PolyLine(ruta_geometria, color="#0055FF", weight=5, opacity=0.7).add_to(mapa)

    # Tráfico
    print(f"   -> Procesando {len(incidentes)} eventos de tráfico...")
    for inc in incidentes:
        lat, lng = inc['lat'], inc['lng']
        if sw[0] < lat < ne[0] and sw[1] < lng < ne[1]:
            desc = traducir_detalles_trafico(inc['fullDesc'])
            tipo = inc['type']
            
            popup_html = f"<div style='font-family:Arial; width:200px'><b>Evento:</b> {desc}</div>"
            
            if tipo == 4: # Congestion
                folium.Circle(location=(lat, lng), radius=300, color='red', fill=True, fill_opacity=0.4, popup=popup_html).add_to(mapa)
            elif tipo == 1: # Construccion
                folium.Marker(location=(lat, lng), icon=folium.Icon(color='orange', icon='wrench', prefix='fa'), popup=popup_html).add_to(mapa)
            else: # Accidente/Otro
                folium.Marker(location=(lat, lng), icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa'), popup=popup_html).add_to(mapa)

    # Marcadores de Logística (Almacén y Entregas)
    for i, p in enumerate(paradas_ordenadas):
        # Icono
        if i == 0:
            folium.Marker(location=p['pos'], popup=f"<b>ALMACÉN</b><br>{p['dir']}", icon=folium.Icon(color='green', icon='home', prefix='fa')).add_to(mapa)
        elif i < len(paradas_ordenadas) - 1:
            folium.Marker(location=p['pos'], popup=f"<b>ENTREGA #{i}</b><br>{p['dir']}", icon=folium.Icon(color='blue', icon='truck', prefix='fa')).add_to(mapa)
            # Numero flotante
            folium.Marker(location=p['pos'], icon=folium.DivIcon(html=f"""<div style="color:white; background:darkblue; border-radius:50%; width:20px; height:20px; text-align:center; font-weight:bold; border:1px solid white; font-size:12px; line-height:20px;">{i}</div>""")).add_to(mapa)

    # Nodos intermedios (Puntos de la ruta)
    for node_id in G.nodes():
        datos = G.nodes[node_id]
        folium.CircleMarker(location=datos['pos'], radius=3, color='blue', fill=True, fill_color='white', fill_opacity=1, popup=datos['desc']).add_to(mapa)
        
    mapa.fit_bounds([sw, ne])
    mapa.save(nombre_archivo)
    print(f"\nMapa generado exitosamente: {nombre_archivo}")

if __name__ == "__main__":
    API_KEY = "0wSs0qcTStL21HNT4VhipGi7CDsjXnkw"
    
    print("--- SISTEMA LOGÍSTICO DE RUTAS ---")
    lugares = []
    
    inicio = input("1. Salida (Almacén): ") or "Zocalo, Mexico City"
    lugares.append(inicio)
    
    c = 1
    while True:
        d = input(f"2. Entrega #{c} (o 'fin'): ")
        if d.lower() == 'fin': break
        lugares.append(d)
        c += 1
    lugares.append(inicio) # Regreso al almacén
    
    if len(lugares) < 3:
        print("Se requieren destinos para calcular ruta.")
    else:
        print("\nCalculando ruta optimizada...")
        maniobras, geom, bbox, orden = dijkstra.obtener_ruta_multiparada(API_KEY, lugares)
        
        if maniobras:
            print("Obteniendo datos de tráfico...")
            trafico = dijkstra.obtener_incidencias_trafico(API_KEY, bbox)
            
            grafo = dijkstra.construir_grafo_logico(maniobras)
            generar_mapa_visual(grafo, geom, trafico, orden)
        else:
            print("Error al obtener ruta.")