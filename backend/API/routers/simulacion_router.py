from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, json
from backend.core.simulacion import simulate_aba
router = APIRouter()

class SimRequest(BaseModel):
    origen: str
    destino: str
    steps_per_segment: int = 20
# BASE_DIR = carpeta /backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# GRAPH_PATH = /backend/data/graph.json
GRAPH_PATH = os.path.join(BASE_DIR, "data", "graph.json")

with open(GRAPH_PATH, "r") as f:
    GRAPH = json.load(f)


@router.post('/simular')
def simular(payload: SimRequest):
    try:
        result = simulate_aba(GRAPH, payload.origen, payload.destino, payload.steps_per_segment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
