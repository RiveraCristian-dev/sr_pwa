from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import folium

# Importamos solo las funciones necesarias de dijkstra
from backend.core.dijkstra import obtener_ruta_multiparada, construir_grafo_logico, obtener_incidencias_trafico

router = APIRouter()
load_dotenv()

class SimulacionRequest(BaseModel):
    origen: str
    destino: str

@router.post("/render", response_class=HTMLResponse)
def simular_ruta_render(request: SimulacionRequest):
    """
    Calcula ruta, obtiene tráfico y devuelve el HTML del mapa completo.
    (Versión sin traducción de eventos)
    """
    API_KEY = os.getenv("MAPQUEST_API_KEY", "0wSs0qcTStL21HNT4VhipGi7CDsjXnkw")
    
    lugares = [request.origen, request.destino]
    
    # 1. Obtener datos de la ruta y el Bounding Box
    maniobras, geometria, bbox, orden = obtener_ruta_multiparada(API_KEY, lugares)
    
    if not maniobras:
        raise HTTPException(status_code=400, detail="No se pudo calcular la ruta.")
    
    # 2. Obtener datos de tráfico
    incidentes = []
    if bbox:
        try:
            incidentes = obtener_incidencias_trafico(API_KEY, bbox)
        except Exception as e:
            print(f"Advertencia: No se pudo obtener tráfico: {e}")

    # 3. Configurar el mapa base
    sw = [18.80, -100.20] 
    ne = [20.20, -98.80]
    centro = [(sw[0]+ne[0])/2, (sw[1]+ne[1])/2]
    
    m = folium.Map(location=centro, zoom_start=11, tiles='OpenStreetMap')

    # 4. Dibujar la Ruta (Azul)
    if geometria:
        folium.PolyLine(geometria, color="#0055FF", weight=5, opacity=0.7).add_to(m)
    
    # 5. Dibujar Incidentes de Tráfico (Texto original)
    for inc in incidentes:
        lat, lng = inc['lat'], inc['lng']
        
        # Filtro geográfico
        if sw[0] < lat < ne[0] and sw[1] < lng < ne[1]:
            # Usamos directamente la descripción original de la API
            desc = inc.get('fullDesc') or "Sin detalles"
            tipo = inc['type']
            
            popup_html = f"<div style='font-family:Arial; width:200px'><b>Evento:</b> {desc}</div>"
            
            # Tipo 4: Congestión
            if tipo == 4: 
                folium.Circle(
                    location=(lat, lng), radius=300, color='red', fill=True, 
                    fill_opacity=0.4, popup=popup_html
                ).add_to(m)
            # Tipo 1: Construcción
            elif tipo == 1: 
                folium.Marker(
                    location=(lat, lng), 
                    icon=folium.Icon(color='orange', icon='wrench', prefix='fa'), 
                    popup=popup_html
                ).add_to(m)
            # Otros
            else: 
                folium.Marker(
                    location=(lat, lng), 
                    icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa'), 
                    popup=popup_html
                ).add_to(m)

    # 6. Marcadores de Inicio y Fin
    if orden:
        folium.Marker(
            location=orden[0]['pos'], 
            popup=f"<b>SALIDA</b><br>{orden[0]['dir']}", 
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(m)
        
        folium.Marker(
            location=orden[-1]['pos'], 
            popup=f"<b>DESTINO</b><br>{orden[-1]['dir']}", 
            icon=folium.Icon(color='blue', icon='flag', prefix='fa')
        ).add_to(m)

    m.fit_bounds([sw, ne])
    
    return m.get_root().render()