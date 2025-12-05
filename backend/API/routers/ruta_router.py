from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json, os
from core.dijktra import dijkstra, path_distance
from core.calculos import calcular_tiempo, calcular_costo, calcular_energia

router = APIRouter()

class RutaRequest(BaseModel):
    origen: str
    destino: str

# load graph once (relative path)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
GRAPH_PATH = os.path.join(BASE_DIR, "backend", "data", "graph.json")

with open(GRAPH_PATH, "r") as f:
    GRAPH = json.load(f)

@router.post('/ruta')
def obtener_ruta(payload: RutaRequest):
    try:
        path = dijkstra(GRAPH, payload.origen, payload.destino)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not path:
        raise HTTPException(status_code=404, detail='Ruta no encontrada')

    dist = path_distance(GRAPH, path)
    return {
        'ruta': path,
        'distancia_total': dist,
        'tiempo_est': calcular_tiempo(dist),
        'costo_est': calcular_costo(dist),
        'energia_est': calcular_energia(dist)
    }
