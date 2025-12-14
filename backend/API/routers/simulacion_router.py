from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse # Importante para devolver el mapa directo
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import folium

# Importamos las funciones del core
from backend.core.simulacion import generar_mapa_visual
from backend.core.dijkstra import obtener_ruta_multiparada, construir_grafo_logico

router = APIRouter()
load_dotenv()

class SimulacionRequest(BaseModel):
    origen: str
    destino: str
    # Ya no necesitamos nombre_mapa porque no guardaremos archivo físico

@router.post("/render", response_class=HTMLResponse)
def simular_ruta_render(request: SimulacionRequest):
    """
    Calcula la ruta y devuelve el HTML del mapa directamente al navegador.
    """
    API_KEY = os.getenv("MAPQUEST_API_KEY", "0wSs0qcTStL21HNT4VhipGi7CDsjXnkw")
    
    # CORRECCIÓN 1: Pasar lista de lugares, no strings sueltos
    lugares = [request.origen, request.destino]
    
    # Obtenemos datos de la ruta
    maniobras, geometria, bbox, orden = obtener_datos_ruta(API_KEY, lugares)
    
    if not maniobras:
        raise HTTPException(status_code=400, detail="No se pudo calcular la ruta. Verifica las direcciones.")
    
    # Construimos el grafo y obtenemos tráfico (si es necesario)
    grafo = construir_grafo_logico(maniobras)
    
    # usando la lógica de tu simulacion.py pero devolviendo el objeto.
    
    # Recreación rápida de la lógica de visualización para devolver string
    import folium
    
    # Centrar mapa (lógica simplificada de tu archivo)
    sw = [18.80, -100.20]
    ne = [20.20, -98.80]
    centro = [(sw[0]+ne[0])/2, (sw[1]+ne[1])/2]
    
    m = folium.Map(location=centro, zoom_start=11, tiles='OpenStreetMap')
    
    # Dibujar ruta
    folium.PolyLine(geometria, color="#0055FF", weight=5, opacity=0.7).add_to(m)
    
    # Marcadores (Inicio y Fin)
    if orden:
        # Inicio
        folium.Marker(location=orden[0]['pos'], popup=f"Inicio: {orden[0]['dir']}", icon=folium.Icon(color='green', icon='home', prefix='fa')).add_to(m)
        # Fin
        folium.Marker(location=orden[-1]['pos'], popup=f"Destino: {orden[-1]['dir']}", icon=folium.Icon(color='red', icon='flag', prefix='fa')).add_to(m)

    m.fit_bounds([sw, ne])
    
    # Devolver el HTML como string
    return m.get_root().render()