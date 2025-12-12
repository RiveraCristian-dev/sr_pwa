from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Importar función REAL que tienes
from backend.core.simulacion import generar_mapa_visual
from backend.core.dijkstra import obtener_datos_ruta, construir_grafo_logico

router = APIRouter()
load_dotenv()

class SimulacionRequest(BaseModel):
    origen: str
    destino: str
    nombre_mapa: str = "mapa_simulacion.html"

class SimulacionResponse(BaseModel):
    mapa_generado: bool
    archivo: str
    mensaje: str

@router.post("/", response_model=SimulacionResponse)
def simular_ruta(request: SimulacionRequest):
    """Genera un mapa de la ruta usando Folium"""
    
    # Obtener API Key
    API_KEY = os.getenv("MAPQUEST_API_KEY", "0wSs0qcTStL21HNT4VhipGi7CDsjXnkw")
    
    if not API_KEY or API_KEY == "TU_API_KEY_MAPQUEST_AQUI":
        raise HTTPException(status_code=500, detail="Configura MAPQUEST_API_KEY en .env")
    
    # Obtener ruta
    maniobras, geometria, bbox = obtener_datos_ruta(API_KEY, request.origen, request.destino)
    
    if not maniobras:
        raise HTTPException(status_code=400, detail="No se pudo calcular la ruta")
    
    # Construir grafo
    grafo = construir_grafo_logico(maniobras)
    
    # Generar mapa
    try:
        generar_mapa_visual(grafo, geometria, [], request.nombre_mapa)
        return {
            "mapa_generado": True,
            "archivo": request.nombre_mapa,
            "mensaje": f"Mapa generado: {request.nombre_mapa}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando mapa: {str(e)}")

@router.get("/test")
def test_simulacion():
    return {"status": "simulacion_router funcionando", "version": "1.0"}