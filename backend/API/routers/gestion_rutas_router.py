from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import json
from dotenv import load_dotenv
import requests

from backend.API.database import get_db
from backend.core.dijkstra import obtener_ruta_multiparada
from backend.core.simulacion import generar_mapa_visual

router = APIRouter()
load_dotenv()

# ============================================
# CONFIGURACIÓN
# ============================================

ORIGEN_BASE = "Universidad Mexiquense del Bicentenario, Manzana 005, Loma Bonita, 54879 Cuautitlán, Estado de México"

# Mapeo UMB → Dirección completa (NECESARIO PARA GEOMETRÍA EXACTA)
UNIVERSIDADES = {
    # REGIÓN NORTE
    "UMB Acambay": "50300 Villa de Acambay de Ruíz Castañeda, Méx.",
    "UMB El oro": "Angel Castillo López S/N, A Santiago Oxtempan, 50600 El Oro de Hidalgo, Méx.",
    "UMB Temascalciongo": "Ignacio Zaragoza, 50400 Temascalcingo de José María Velasco, Méx.",
    "UMB Jilotepec": "Km. 7, Carretera Jilotepec-Chapa de Mota, Ejido de Jilotepec, 54240 Jilotepec de Molina Enríquez, Méx.",
    "UMB Morelos": "Camino Real S/N, Barrio Primero, 50550 San Bartolo Morelos, Méx.",
    "UMB Ixtlahuaca": "Domicilio Conocido S/N, Ixtlahuaca, 50740 Barrio de San Pedro la Cabecera, Méx.",
    "UMB San Jose del Rincon": "AVENIDA UNIVERSIDAD SN, 50660 Colonia Las Tinajas, Méx.",
    "UMB Jiquipilco": "Km.1, Carretera San Felipe Santiago, 50800 Méx.",
    "UMB Villa Vivtoria": "Km. 47 Carretera Federal Toluca-Zitácuaro, 50960 San Agustín Berros, Méx.",

    # REGIÓN ORIENTE
    "UMB Atenco": "Independencia 1, Sta Isabel Ixtapan, 56300 Santa Isabel Ixtapan, Méx.",
    "UMB Chalco": "Carr Federal México-Cuautla Km 14 s/n, La Candelaria tlapala, 56641 Chalco de Díaz Covarrubias, Méx.",
    "UMB Ixtapaluca": "Avenida Hacienda La Escondida 589, Geovillas Santa Barbara, 56630 Ixtapaluca, Méx.",
    "UMB La Paz": "S. Agustín S/N, El Pino, 56400 San Isidro, Méx.",

    # REGIÓN VALLE DE TOLUCA
    "UMB Huixquilucan": "De las Flores S/N, La Magdalena Chichicaspa, 52773 Huixquilucan de Degollado, Méx.",
    "UMB Lerma": "Cto de la Industria Pte S/N, Isidro Fabela, 52004 Lerma de Villada, Méx.",
    "UMB Temoaya": "Domicilio Conocido S/N, San Diego Alcalá, 50850 Temoaya, Méx.",
    "UMB Tenango del Valle": "Los Hidalgos 233, 52316 Tenango de Arista, Méx.",
    "UMB Xalatlaco": "Calle Colorines S/N, Deportiva de Xalatlaco, 52680 Xalatlaco, Méx.",

    # REGIÓN VALLE DE MÉXICO
    "UMB Ecatepec": "Av Insurgentes, Fraccionamiento Las Americas, Las Américas, 55070 Ecatepec de Morelos, Méx.",
    "UMB Tecámac": "Calle Blvrd Jardines Mz 66, Los Heroes Tecamac, 55764 Ojo de Agua, Méx.",
    "UMB Tepotzotlán": "Calle Av. del Convento S/N, El Trebol, 54614 Tepotzotlán, Méx.",
    "UMB Tultitlán": "San Antonio s/n, Villa Esmeralda, 54910 Tultitlán de Mariano Escobedo, Méx.",
    "UMB Tultepec": "Calle al Quemado S/N, Fracción I del Ex Ejido, 54980 San Pablo de las Salinas, Méx.",
    "UMB Villa": "Carretera Villa del Carbon, KM 34.5, 54300 Villa del Carbón, Méx.",

    # REGIÓN SUR
    "UMB Almoloya de Alquisiras": "Domicilio Conocido, Paraje la Chimenea, 51860 Almoloya de Alquisiras, Méx.",
    "UMB Coatepec Harinas": "Domicilio conocido, San Luis, 51700 Coatepec Harinas, Méx.",
    "UMB Sultepec": "Carretera Toluca–Sultepec, Libramiento Sultepec–La Goleta S/N, Barrio Camino Nacional, 51600 Sultepec, Méx.",
    "UMB Tejupilco": "Domicilio Conocido, El Rodeo, Tejupilco de Hidalgo, 51400 Méx.",
    "UMB Tlatlaya": "Carretera Los Cuervos-Arcelia km 35, San Pedro, Limón, 51585 Tlatlaya, Méx"
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
    Calcula ruta REAL con geometría para una asignación y la guarda en la DB
    """
    try:
        # 1. Buscar los datos de la asignación
        check_query = text("""
            SELECT a.id, a.ruta_municipio, v.tipo as vehiculo_tipo
            FROM asignaciones a
            INNER JOIN vehiculos v ON a.id_vehiculo = v.id
            WHERE a.id = :asignacion_id AND a.estado = 'activa'
        """)
        asig = db.execute(check_query, {"asignacion_id": asignacion_id}).fetchone()

        if not asig:
            raise HTTPException(status_code=404, detail="Asignación no encontrada")
        
        # 2. Definir origen y destino
        destino_completo = UNIVERSIDADES.get(asig.ruta_municipio, f"{asig.ruta_municipio}, Estado de México")
        origen = request.origen or ORIGEN_BASE
        
        # 3. LLAMAR A DIJKSTRA
        api_key = os.getenv("MAPQUEST_API_KEY")
        maniobras, geometria, bbox, orden = obtener_ruta_multiparada(api_key, [origen, destino_completo])

        if not geometria:
            raise HTTPException(status_code=400, detail="No se obtuvo geometría de MapQuest")
        
        # 4. ACTUALIZAR MAPA PARA EL ADMINISTRADOR (simulacion.py)
        generar_mapa_visual(None, geometria, [], [{"pos": [0,0], "dir": origen}, {"pos": [0,0], "dir": destino_completo}])

        # 5. GUARDAR EN BASE DE DATOS PARA EL REPARTIDOR
        distancia_km = sum(m.get('distance', 0) for m in maniobras)
        tiempo_min = sum(m.get('time', 0) for m in maniobras) / 60

        datos_ruta = {
            "puntos": geometria,
            "maniobras": maniobras,
            "bbox": bbox
        }

        insert_query = text("""
            INSERT INTO rutas_asignadas (
                id_asignacion, origen_direccion, destino_direccion,
                distancia_km, tiempo_min, ruta_mapquest,
                vehiculo_tipo, activa
            ) VALUES (
                :asig_id, :origen, :destino,
                :dist, :tiempo, CAST(:ruta_json AS jsonb),
                :v_tipo, TRUE
            )
        """)

        db.execute(insert_query, {
            "asig_id": asignacion_id,
            "origen": origen,
            "destino": destino_completo,
            "dist": distancia_km,
            "tiempo": tiempo_min,
            "ruta_json": json.dumps(datos_ruta),
            "v_tipo": asig.vehiculo_tipo
        })

        db.commit()

        # ✅ CORREGIDO: Devolvemos los datos numéricos para evitar el error 'toFixed' en el frontend
        return {
            "status": "success", 
            "mensaje": "Ruta guardada y mapa actualizado",
            "distancia_km": distancia_km,
            "tiempo_min": tiempo_min,
            "costo_total": 0,       # Valor por defecto para frontend
            "emisiones_co2_kg": 0   # Valor por defecto para frontend
        }
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error en el router: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
            "ruta_json": json.dumps(ruta_data["ruta_completa"])
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