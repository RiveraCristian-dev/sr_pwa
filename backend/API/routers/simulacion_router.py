from api.routers.auth_router import get_current_user
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ...core.simulacion import simular_movimiento  # Placeholder

router = APIRouter()

class SimulacionRequest(BaseModel):
    ruta: list[str]  # De /ruta

class SimulacionResponse(BaseModel):
    posiciones: list[dict]  # Lista de {"x": float, "y": float, "tiempo": float}

@router.post("/", response_model=SimulacionResponse, dependencies=[Depends(get_current_user)])
def simular(request: SimulacionRequest):
    # Placeholder: Llama a simulator.py
    # posiciones = simular_movimiento(request.ruta)
    posiciones_mock = [{"x": 0, "y": 0, "tiempo": 0}, {"x": 5, "y": 5, "tiempo": 10}]
    return {"posiciones": posiciones_mock}