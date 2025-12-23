from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import json  # ← AGREGADO
from dotenv import load_dotenv
import requests

from backend.API.database import get_db

router = APIRouter()
load_dotenv()

# ============================================
# CONFIGURACIÓN
# ============================================

ORIGEN_BASE = "Universidad Mexiquense del Bicentenario, Manzana 005, Loma Bonita, 54879 Cuautitlán, Estado de México"

# Mapeo UMB → Dirección completa
UNIVERSIDADES = {
    "UMB Acambay": "Universidad Mexiquense del Bicentenario, Acambay de Arteaga, Estado de México",
    "UMB El oro": "Universidad Mexiquense del Bicentenario, El Oro, Estado de México",
    "UMB Temascalciongo": "Universidad Mexiquense del Bicentenario, Temascalcingo, Estado de México",
    "UMB Jilotepec": "Universidad Mexiquense del Bicentenario, Jilotepec de Molina Enríquez, Estado de México",
    "UMB Morelos": "Universidad Mexiquense del Bicentenario, Villa del Carbón, Estado de México",
    "UMB Ixtlahuaca": "Universidad Mexiquense del Bicentenario, Ixtlahuaca de Rayón, Estado de México",
    "UMB San Jose del Rincon": "Universidad Mexiquense del Bicentenario, San José del Rincón, Estado de México",
    "UMB Jiquipilco": "Universidad Mexiquense del Bicentenario, Jiquipilco, Estado de México",
    "UMB Villa Vivtoria": "Universidad Mexiquense del Bicentenario, Villa Victoria, Estado de México",
    "UMB Atenco": "Universidad Mexiquense del Bicentenario, Atenco, Estado de México",
    "UMB Chalco": "Universidad Mexiquense del Bicentenario, Chalco, Estado de México",
    "UMB Ixtapaluca": "Universidad Mexiquense del Bicentenario, Ixtapaluca, Estado de México",
    "UMB La Paz": "Universidad Mexiquense del Bicentenario, La Paz, Estado de México",
    "UMB Huixquilucan": "Universidad Mexiquense del Bicentenario, Huixquilucan de Degollado, Estado de México",
    "UMB Lerma": "Universidad Mexiquense del Bicentenario, Lerma de Villada, Estado de México",
    "UMB Temoaya": "Universidad Mexiquense del Bicentenario, Temoaya, Estado de México",
    "UMB Tenango del Valle": "Universidad Mexiquense del Bicentenario, Tenango del Valle, Estado de México",
    "UMB Xalatlaco": "Universidad Mexiquense del Bicentenario, Xalatlaco, Estado de México",
    "UMB Ecatepec": "Universidad Mexiquense del Bicentenario, Ecatepec de Morelos, Estado de México",
    "UMB Tecámac": "Universidad Mexiquense del Bicentenario, Tecámac, Estado de México",
    "UMB Tepotzotlán": "Universidad Mexiquense del Bicentenario, Tepotzotlán, Estado de México",
    "UMB Tultitlán": "Universidad Mexiquense del Bicentenario, Tultitlán de Mariano Escobedo, Estado de México",
    "UMB Tultepec": "Universidad Mexiquense del Bicentenario, Tultepec, Estado de México",
    "UMB Villa": "Universidad Mexiquense del Bicentenario, Villa Nicolás Romero, Estado de México",
    "UMB Almoloya de Alquisiras": "Universidad Mexiquense del Bicentenario, Almoloya de Alquisiras, Estado de México",
    "UMB Coatepec Harinas": "Universidad Mexiquense del Bicentenario, Coatepec Harinas, Estado de México",
    "UMB Sultepec": "Universidad Mexiquense del Bicentenario, Sultepec, Estado de México",
    "UMB Tejupilco": "Universidad Mexiquense del Bicentenario, Tejupilco de Hidalgo, Estado de México",
    "UMB Tlatlaya": "Universidad Mexiquense del Bicentenario, Tlatlaya, Estado de México"
}

# ============================================
# MODELOS
# ============================================

class CalcularRutaRequest(BaseModel):
    origen: Optional[str] = None

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def obtener_ruta_mapquest(origen: str, destino: str):
    """Consulta MapQuest API para obtener ruta"""
    API_KEY = os.getenv("MAPQUEST_API_KEY")
    
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key de MapQuest no configurada")
    
    url = f"http://www.mapquestapi.com/directions/v2/route?key={API_KEY}"
    
    payload = {
        "locations": [origen, destino],
        "options": {
            "unit": "k",
            "routeType": "fastest",
            "doReverseGeocode": False
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "route" not in data:
            raise Exception("No se pudo calcular la ruta")
        
        route = data["route"]
        
        return {
            "distancia_km": route.get("distance", 0),
            "tiempo_min": route.get("time", 0) / 60,
            "ruta_completa": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error con MapQuest: {str(e)}")

# ============================================
# ENDPOINTS
# ============================================

@router.get("/pendientes")
def listar_asignaciones_pendientes(db: Session = Depends(get_db)):
    """
    Lista asignaciones activas que AÚN NO tienen ruta calculada
    """
    try:
        query = text("""
            SELECT 
                a.id as asignacion_id,
                a.numero_paquetes,
                a.ruta_municipio as destino,
                a.fecha_asignacion,
                u.id as repartidor_id,
                u.nombre_completo as repartidor_nombre,
                v.id as vehiculo_id,
                v.modelo as vehiculo_modelo,
                v.tipo as vehiculo_tipo
            FROM asignaciones a
            INNER JOIN usuarios u ON a.id_repartidor = u.id
            INNER JOIN vehiculos v ON a.id_vehiculo = v.id
            LEFT JOIN rutas_asignadas r ON a.id = r.id_asignacion AND r.activa = TRUE
            WHERE a.estado = 'activa'
                AND r.id IS NULL
            ORDER BY a.fecha_asignacion DESC
        """)
        
        result = db.execute(query)
        asignaciones = result.fetchall()
        
        return {
            "total": len(asignaciones),
            "asignaciones": [
                {
                    "asignacion_id": a.asignacion_id,
                    "repartidor": {
                        "id": a.repartidor_id,
                        "nombre": a.repartidor_nombre
                    },
                    "vehiculo": {
                        "id": a.vehiculo_id,
                        "modelo": a.vehiculo_modelo,
                        "tipo": a.vehiculo_tipo
                    },
                    "numero_paquetes": a.numero_paquetes,
                    "destino": a.destino,
                    "fecha_asignacion": a.fecha_asignacion.isoformat()
                } for a in asignaciones
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/calcular/{asignacion_id}")
def calcular_ruta(
    asignacion_id: int,
    request: CalcularRutaRequest = CalcularRutaRequest(),
    db: Session = Depends(get_db)
):
    """
    Calcula ruta para una asignación específica y la guarda en rutas_asignadas
    """
    try:
        # 1. Verificar que la asignación existe y no tiene ruta
        check_query = text("""
            SELECT 
                a.id, a.ruta_municipio, a.numero_paquetes,
                v.tipo as vehiculo_tipo,
                u.nombre_completo as repartidor_nombre,
                r.id as ruta_existente
            FROM asignaciones a
            INNER JOIN vehiculos v ON a.id_vehiculo = v.id
            INNER JOIN usuarios u ON a.id_repartidor = u.id
            LEFT JOIN rutas_asignadas r ON a.id = r.id_asignacion AND r.activa = TRUE
            WHERE a.id = :asignacion_id AND a.estado = 'activa'
        """)
        
        asignacion = db.execute(check_query, {"asignacion_id": asignacion_id}).fetchone()
        
        if not asignacion:
            raise HTTPException(status_code=404, detail="Asignación no encontrada")
        
        if asignacion.ruta_existente:
            raise HTTPException(status_code=400, detail="Esta asignación ya tiene una ruta calculada")
        
        # 2. Obtener dirección completa del destino
        destino_completo = UNIVERSIDADES.get(asignacion.ruta_municipio)
        
        if not destino_completo:
            destino_completo = f"{asignacion.ruta_municipio}, Estado de México"
        
        # 3. Calcular ruta con MapQuest
        origen = request.origen or ORIGEN_BASE
        
        ruta_data = obtener_ruta_mapquest(origen, destino_completo)
        
        # 4. Insertar en rutas_asignadas
        insert_query = text("""
            INSERT INTO rutas_asignadas (
                id_asignacion,
                origen_direccion,
                destino_direccion,
                distancia_km,
                tiempo_min,
                ruta_mapquest,
                vehiculo_tipo,
                activa
            ) VALUES (
                :asignacion_id,
                :origen,
                :destino,
                :distancia,
                :tiempo,
                CAST(:ruta_json AS jsonb),
                :vehiculo_tipo,
                TRUE
            ) RETURNING id
        """)
        
        result = db.execute(insert_query, {
            "asignacion_id": asignacion_id,
            "origen": origen,
            "destino": destino_completo,
            "distancia": ruta_data["distancia_km"],
            "tiempo": ruta_data["tiempo_min"],
            "ruta_json": json.dumps(ruta_data["ruta_completa"]),  # ✅ CORREGIDO
            "vehiculo_tipo": asignacion.vehiculo_tipo
        })
        
        ruta_id = result.fetchone()[0]
        db.commit()
        
        return {
            "mensaje": "Ruta calculada exitosamente",
            "ruta_id": ruta_id,
            "asignacion_id": asignacion_id,
            "repartidor": asignacion.repartidor_nombre,
            "origen": origen,
            "destino": destino_completo,
            "distancia_km": round(ruta_data["distancia_km"], 2),
            "tiempo_min": round(ruta_data["tiempo_min"], 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al calcular ruta: {str(e)}")

@router.get("/calculadas")
def listar_rutas_calculadas(db: Session = Depends(get_db)):
    """
    Lista todas las rutas calculadas y activas
    """
    try:
        query = text("""
            SELECT 
                r.id as ruta_id,
                r.origen_direccion,
                r.destino_direccion,
                r.distancia_km,
                r.tiempo_min,
                r.costo_total,
                r.emisiones_co2_kg,
                r.fecha_calculo,
                a.id as asignacion_id,
                a.numero_paquetes,
                u.id as repartidor_id,
                u.nombre_completo as repartidor_nombre,
                v.modelo as vehiculo_modelo,
                v.tipo as vehiculo_tipo
            FROM rutas_asignadas r
            INNER JOIN asignaciones a ON r.id_asignacion = a.id
            INNER JOIN usuarios u ON a.id_repartidor = u.id
            INNER JOIN vehiculos v ON a.id_vehiculo = v.id
            WHERE r.activa = TRUE
            ORDER BY r.fecha_calculo DESC
        """)
        
        result = db.execute(query)
        rutas = result.fetchall()
        
        return {
            "total": len(rutas),
            "rutas": [
                {
                    "ruta_id": r.ruta_id,
                    "asignacion_id": r.asignacion_id,
                    "repartidor": {
                        "id": r.repartidor_id,
                        "nombre": r.repartidor_nombre
                    },
                    "vehiculo": {
                        "modelo": r.vehiculo_modelo,
                        "tipo": r.vehiculo_tipo
                    },
                    "numero_paquetes": r.numero_paquetes,
                    "origen": r.origen_direccion,
                    "destino": r.destino_direccion,
                    "distancia_km": float(r.distancia_km),
                    "tiempo_min": float(r.tiempo_min),
                    "costo_total": float(r.costo_total) if r.costo_total else 0,
                    "emisiones_co2_kg": float(r.emisiones_co2_kg) if r.emisiones_co2_kg else 0,
                    "fecha_calculo": r.fecha_calculo.isoformat()
                } for r in rutas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.delete("/{ruta_id}")
def eliminar_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """
    Marca una ruta como inactiva (soft delete)
    """
    try:
        query = text("""
            UPDATE rutas_asignadas
            SET activa = FALSE
            WHERE id = :ruta_id
            RETURNING id
        """)
        
        result = db.execute(query, {"ruta_id": ruta_id})
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Ruta no encontrada")
        
        db.commit()
        
        return {"mensaje": "Ruta eliminada exitosamente", "ruta_id": ruta_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/recalcular/{ruta_id}")
def recalcular_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """
    Recalcula una ruta existente (actualiza distancia, tiempo, etc.)
    """
    try:
        # Obtener datos actuales
        query = text("""
            SELECT origen_direccion, destino_direccion, vehiculo_tipo
            FROM rutas_asignadas
            WHERE id = :ruta_id AND activa = TRUE
        """)
        
        ruta = db.execute(query, {"ruta_id": ruta_id}).fetchone()
        
        if not ruta:
            raise HTTPException(status_code=404, detail="Ruta no encontrada")
        
        # Recalcular con MapQuest
        ruta_data = obtener_ruta_mapquest(ruta.origen_direccion, ruta.destino_direccion)
        
        # Actualizar en BD
        update_query = text("""
            UPDATE rutas_asignadas
            SET 
                distancia_km = :distancia,
                tiempo_min = :tiempo,
                ruta_mapquest = CAST(:ruta_json AS jsonb),
                fecha_calculo = CURRENT_TIMESTAMP
            WHERE id = :ruta_id
        """)
        
        db.execute(update_query, {
            "ruta_id": ruta_id,
            "distancia": ruta_data["distancia_km"],
            "tiempo": ruta_data["tiempo_min"],
            "ruta_json": json.dumps(ruta_data["ruta_completa"])  # ✅ CORREGIDO
        })
        
        db.commit()
        
        return {
            "mensaje": "Ruta recalculada exitosamente",
            "ruta_id": ruta_id,
            "distancia_km": round(ruta_data["distancia_km"], 2),
            "tiempo_min": round(ruta_data["tiempo_min"], 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")