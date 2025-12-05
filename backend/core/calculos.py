"""Cálculos simple de tiempo, costo y energía basados en distancia."""
def calcular_tiempo(dist_km: float, velocidad_kmh: float = 40.0) -> float:
    if velocidad_kmh <= 0:
        raise ValueError('velocidad debe ser > 0')
    return dist_km / velocidad_kmh

def calcular_costo(dist_km: float, costo_por_km: float = 1.5) -> float:
    return dist_km * costo_por_km

def calcular_energia(dist_km: float, energia_por_km: float = 0.8) -> float:
    return dist_km * energia_por_km
