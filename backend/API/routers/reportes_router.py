from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from backend.core.calculos import (
    calcular_pedido,
    calcular_gasolina,
    calcular_electrico,
    calcular_hibrido
)

router = APIRouter()

# =========================
# MODELOS PYDANTIC
# =========================

class ReporteRequest(BaseModel):
    tipo_vehiculo: str  # gasolina, electrico, hibrido
    velocidad_promedio_kmh: float
    distancia_km: float
    id_pedido: Optional[int] = None  # Si viene de un pedido específico

class ReporteSimpleRequest(BaseModel):
    """Para reportes sin pedido específico (solo simulación)"""
    tipo_vehiculo: str
    velocidad_promedio_kmh: float
    distancia_km: float
    # Parámetros opcionales del vehículo
    rendimiento_gasolina: Optional[float] = 8.0
    rendimiento_electrico: Optional[float] = 6.0
    precio_gasolina: Optional[float] = 22.50
    precio_kwh: Optional[float] = 2.50

class ReporteResponse(BaseModel):
    vehiculo_tipo: str
    vehiculo_modelo: str
    velocidad_kmh: float
    distancia_km: float
    tiempo_minutos: float
    tiempo_formateado: str
    eta: str
    consumo_detalle: str
    costo_energia: float
    sueldo_chofer: float
    costo_total: float
    emisiones_co2_kg: float

# =========================
# ENDPOINTS - REPORTES
# =========================

@router.post("/generar", response_model=ReporteResponse)
def generar_reporte(
    reporte: ReporteRequest,
    db: Session = Depends(get_db)
):
    """
    Genera reporte completo desde un pedido existente
    Usa calculos.py con datos reales de la BD
    """
    try:
        # Validar tipo de vehículo
        if reporte.tipo_vehiculo not in ["gasolina", "electrico", "hibrido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de vehículo no válido"
            )
        
        # Si viene id_pedido, usar calcular_pedido de calculos.py
        if reporte.id_pedido:
            resultado = calcular_pedido(reporte.id_pedido, reporte.distancia_km)
            
            if "error" in resultado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=resultado["error"]
                )
            
            # Calcular sueldo del chofer (80 MXN/hora)
            tiempo_horas = resultado["tiempo"]["horas"]
            sueldo_chofer = tiempo_horas * 80
            
            # Extraer datos del resultado
            return ReporteResponse(
                vehiculo_tipo=resultado["vehiculo"]["tipo"],
                vehiculo_modelo=resultado["vehiculo"]["modelo"],
                velocidad_kmh=resultado["vehiculo"]["velocidad_promedio_kmh"],
                distancia_km=resultado["distancia"]["km"],
                tiempo_minutos=resultado["tiempo"]["minutos"],
                tiempo_formateado=resultado["tiempo"]["formateado"],
                eta=calcular_eta(resultado["tiempo"]["minutos"]),
                consumo_detalle=formatear_consumo(resultado["consumo"]),
                costo_energia=resultado["costo"]["total"],
                sueldo_chofer=round(sueldo_chofer, 2),
                costo_total=round(resultado["costo"]["total"] + sueldo_chofer, 2),
                emisiones_co2_kg=resultado["emisiones"]["co2_kg"]
            )
        
        else:
            # Si NO viene id_pedido, buscar un vehículo del tipo solicitado
            query = text("""
                SELECT 
                    id, modelo, tipo, velocidad_promedio_kmh,
                    rendimiento_gasolina, rendimiento_electrico,
                    precio_gasolina, precio_kwh,
                    factor_emisiones_gasolina, factor_emisiones_electrico
                FROM vehiculos
                WHERE tipo = :tipo AND activo = TRUE
                LIMIT 1
            """)
            
            vehiculo = db.execute(query, {"tipo": reporte.tipo_vehiculo}).fetchone()
            
            if not vehiculo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hay vehículos de tipo '{reporte.tipo_vehiculo}' registrados"
                )
            
            # Calcular métricas manualmente
            return generar_reporte_simple_con_vehiculo(
                vehiculo, 
                reporte.velocidad_promedio_kmh,
                reporte.distancia_km
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al generar reporte: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte: {str(e)}"
        )

@router.post("/generar-simple", response_model=ReporteResponse)
def generar_reporte_simple(reporte: ReporteSimpleRequest):
    """
    Genera reporte SIN consultar BD (modo simulación puro)
    Útil para testing o cuando no hay pedidos registrados
    """
    try:
        # Validar tipo
        if reporte.tipo_vehiculo not in ["gasolina", "electrico", "hibrido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de vehículo no válido"
            )
        
        # Calcular tiempo
        tiempo_horas = reporte.distancia_km / reporte.velocidad_promedio_kmh
        tiempo_minutos = tiempo_horas * 60
        
        # Calcular consumo según tipo
        datos_mock = type('obj', (object,), {
            'rendimiento_gasolina': reporte.rendimiento_gasolina,
            'rendimiento_electrico': reporte.rendimiento_electrico,
            'precio_gasolina': reporte.precio_gasolina,
            'precio_kwh': reporte.precio_kwh,
            'factor_emisiones_gasolina': 2.31,
            'factor_emisiones_electrico': 0.45
        })()
        
        if reporte.tipo_vehiculo == "gasolina":
            resultado = calcular_gasolina(datos_mock, reporte.distancia_km)
        elif reporte.tipo_vehiculo == "electrico":
            resultado = calcular_electrico(datos_mock, reporte.distancia_km)
        else:  # hibrido
            resultado = calcular_hibrido(datos_mock, reporte.distancia_km)
        
        # Calcular sueldo
        sueldo_chofer = tiempo_horas * 80
        
        # Modelo por defecto
        modelos = {
            "gasolina": "Chevrolet Aveo 2024",
            "electrico": "BYD Eléctrico",
            "hibrido": "Mazda 2 Hybrid"
        }
        
        return ReporteResponse(
            vehiculo_tipo=reporte.tipo_vehiculo,
            vehiculo_modelo=modelos[reporte.tipo_vehiculo],
            velocidad_kmh=reporte.velocidad_promedio_kmh,
            distancia_km=reporte.distancia_km,
            tiempo_minutos=round(tiempo_minutos, 1),
            tiempo_formateado=formatear_tiempo(tiempo_minutos),
            eta=calcular_eta(tiempo_minutos),
            consumo_detalle=formatear_consumo(resultado["consumo"]),
            costo_energia=round(resultado["costo"], 2),
            sueldo_chofer=round(sueldo_chofer, 2),
            costo_total=round(resultado["costo"] + sueldo_chofer, 2),
            emisiones_co2_kg=round(resultado["emisiones"], 2)
        )
        
    except Exception as e:
        print(f"❌ Error en reporte simple: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte: {str(e)}"
        )

@router.get("/dashboard")
def obtener_dashboard(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales para el dashboard admin
    """
    try:
        query = text("""
            SELECT 
                (SELECT COUNT(*) FROM pedidos WHERE estado = 'pendiente') as pedidos_pendientes,
                (SELECT COUNT(*) FROM pedidos WHERE estado = 'en_ruta') as pedidos_en_ruta,
                (SELECT COUNT(*) FROM pedidos WHERE estado = 'entregado') as pedidos_entregados,
                (SELECT COUNT(*) FROM pedidos WHERE estado = 'cancelado') as pedidos_cancelados,
                (SELECT COUNT(*) FROM vehiculos WHERE activo = TRUE) as vehiculos_disponibles,
                (SELECT COUNT(*) FROM asignaciones WHERE estado = 'activa') as asignaciones_activas,
                (SELECT COUNT(*) FROM usuarios WHERE rol = 'repartidor' AND activo = TRUE) as repartidores_activos
        """)
        
        stats = db.execute(query).fetchone()
        
        return {
            "pedidos": {
                "pendientes": stats.pedidos_pendientes,
                "en_ruta": stats.pedidos_en_ruta,
                "entregados": stats.pedidos_entregados,
                "cancelados": stats.pedidos_cancelados,
                "total": sum([
                    stats.pedidos_pendientes,
                    stats.pedidos_en_ruta,
                    stats.pedidos_entregados,
                    stats.pedidos_cancelados
                ])
            },
            "flota": {
                "vehiculos_disponibles": stats.vehiculos_disponibles,
                "asignaciones_activas": stats.asignaciones_activas,
                "repartidores_activos": stats.repartidores_activos
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )

# =========================
# FUNCIONES AUXILIARES
# =========================

def calcular_eta(tiempo_minutos: float) -> str:
    """Calcula hora estimada de llegada"""
    from datetime import datetime, timedelta
    
    ahora = datetime.now()
    llegada = ahora + timedelta(minutes=tiempo_minutos)
    return llegada.strftime("%I:%M %p")

def formatear_tiempo(minutos: float) -> str:
    """Formatea tiempo en formato legible"""
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas}h {mins}min"

def formatear_consumo(consumo: dict) -> str:
    """Formatea el detalle de consumo según tipo"""
    if "litros" in consumo and "kwh" in consumo:
        return f"{consumo['litros']} L de gasolina + {consumo['kwh']} kWh eléctricos"
    elif "litros" in consumo:
        return f"Gasolina consumida: {consumo['litros']} L"
    elif "kwh" in consumo:
        return f"Energía eléctrica: {consumo['kwh']} kWh"
    else:
        return "Consumo no disponible"

def generar_reporte_simple_con_vehiculo(vehiculo, velocidad, distancia):
    """Genera reporte usando datos de un vehículo de la BD"""
    tiempo_horas = distancia / velocidad
    tiempo_minutos = tiempo_horas * 60
    
    # Calcular consumo
    if vehiculo.tipo == "gasolina":
        resultado = calcular_gasolina(vehiculo, distancia)
    elif vehiculo.tipo == "electrico":
        resultado = calcular_electrico(vehiculo, distancia)
    else:
        resultado = calcular_hibrido(vehiculo, distancia)
    
    sueldo_chofer = tiempo_horas * 80
    
    return ReporteResponse(
        vehiculo_tipo=vehiculo.tipo,
        vehiculo_modelo=vehiculo.modelo,
        velocidad_kmh=velocidad,
        distancia_km=distancia,
        tiempo_minutos=round(tiempo_minutos, 1),
        tiempo_formateado=formatear_tiempo(tiempo_minutos),
        eta=calcular_eta(tiempo_minutos),
        consumo_detalle=formatear_consumo(resultado["consumo"]),
        costo_energia=round(resultado["costo"], 2),
        sueldo_chofer=round(sueldo_chofer, 2),
        costo_total=round(resultado["costo"] + sueldo_chofer, 2),
        emisiones_co2_kg=round(resultado["emisiones"], 2)
    )