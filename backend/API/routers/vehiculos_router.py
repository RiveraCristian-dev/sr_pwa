from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from ..database import get_db

router = APIRouter()

# =========================
# MODELOS PYDANTIC
# =========================

class VehiculoCreate(BaseModel):
    modelo: str
    tipo: str  # gasolina, hibrido, electrico
    capacidad_maxima_paquetes: int
    velocidad_promedio_kmh: float
    hora_envio: Optional[str] = None
    rendimiento_gasolina: Optional[float] = None
    rendimiento_electrico: Optional[float] = None
    precio_gasolina: Optional[float] = None
    precio_kwh: Optional[float] = None

class VehiculoResponse(BaseModel):
    id: int
    modelo: str
    tipo: str
    capacidad_maxima_paquetes: int
    velocidad_promedio_kmh: float
    activo: bool
    estado: str  # disponible/asignado
    asignado_a: Optional[str] = None
    fecha_creacion: datetime

class AsignacionCreate(BaseModel):
    id_repartidor: int
    id_vehiculo: int
    numero_paquetes: int
    ruta_municipio: Optional[str] = None

class AsignacionResponse(BaseModel):
    id: int
    id_repartidor: int
    id_vehiculo: int
    numero_paquetes: int
    ruta_municipio: Optional[str]
    estado: str
    repartidor_nombre: str
    vehiculo_modelo: str
    fecha_asignacion: datetime

# =========================
# ENDPOINTS - VEHÍCULOS
# =========================

@router.post("/vehiculos", response_model=VehiculoResponse)
def crear_vehiculo(vehiculo: VehiculoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo vehículo en el sistema
    """
    try:
        # Validar tipo de vehículo
        if vehiculo.tipo not in ["gasolina", "hibrido", "electrico"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de vehículo no válido. Use: gasolina, hibrido o electrico"
            )
        
        # Validaciones específicas por tipo
        if vehiculo.tipo in ["gasolina", "hibrido"] and not vehiculo.rendimiento_gasolina:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe especificar rendimiento_gasolina para vehículos de gasolina/híbridos"
            )
        
        if vehiculo.tipo in ["electrico", "hibrido"] and not vehiculo.rendimiento_electrico:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe especificar rendimiento_electrico para vehículos eléctricos/híbridos"
            )
        
        # Insertar vehículo
        insert_query = text("""
            INSERT INTO vehiculos 
            (modelo, tipo, capacidad_maxima_paquetes, velocidad_promedio_kmh,
             hora_envio, rendimiento_gasolina, rendimiento_electrico,
             precio_gasolina, precio_kwh)
            VALUES (:modelo, :tipo, :capacidad, :velocidad, :hora_envio,
                    :rend_gas, :rend_elec, :precio_gas, :precio_kwh)
            RETURNING id, modelo, tipo, capacidad_maxima_paquetes, 
                     velocidad_promedio_kmh, activo, fecha_creacion
        """)
        
        result = db.execute(insert_query, {
            "modelo": vehiculo.modelo,
            "tipo": vehiculo.tipo,
            "capacidad": vehiculo.capacidad_maxima_paquetes,
            "velocidad": vehiculo.velocidad_promedio_kmh,
            "hora_envio": vehiculo.hora_envio,
            "rend_gas": vehiculo.rendimiento_gasolina,
            "rend_elec": vehiculo.rendimiento_electrico,
            "precio_gas": vehiculo.precio_gasolina or 22.50,  # Default México
            "precio_kwh": vehiculo.precio_kwh or 2.50  # Default México
        })
        
        nuevo_vehiculo = result.fetchone()
        db.commit()
        
        print(f"✅ Vehículo creado: {nuevo_vehiculo.modelo} (ID: {nuevo_vehiculo.id})")
        
        return VehiculoResponse(
            id=nuevo_vehiculo.id,
            modelo=nuevo_vehiculo.modelo,
            tipo=nuevo_vehiculo.tipo,
            capacidad_maxima_paquetes=nuevo_vehiculo.capacidad_maxima_paquetes,
            velocidad_promedio_kmh=nuevo_vehiculo.velocidad_promedio_kmh,
            activo=nuevo_vehiculo.activo,
            estado="disponible",
            asignado_a=None,
            fecha_creacion=nuevo_vehiculo.fecha_creacion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear vehículo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear vehículo: {str(e)}"
        )

@router.get("/vehiculos", response_model=List[VehiculoResponse])
def listar_vehiculos(
    disponibles_solo: bool = False,
    db: Session = Depends(get_db)
):
    """
    Lista todos los vehículos o solo los disponibles
    """
    try:
        query = text("""
            SELECT 
                v.id, v.modelo, v.tipo, v.capacidad_maxima_paquetes,
                v.velocidad_promedio_kmh, v.activo, v.fecha_creacion,
                CASE 
                    WHEN a.id IS NOT NULL THEN 'asignado'
                    ELSE 'disponible'
                END as estado,
                u.nombre_completo as asignado_a
            FROM vehiculos v
            LEFT JOIN asignaciones a ON v.id = a.id_vehiculo AND a.estado = 'activa'
            LEFT JOIN usuarios u ON a.id_repartidor = u.id
            WHERE v.activo = TRUE
            ORDER BY v.fecha_creacion DESC
        """)
        
        result = db.execute(query)
        vehiculos = result.fetchall()
        
        # Filtrar solo disponibles si se solicita
        if disponibles_solo:
            vehiculos = [v for v in vehiculos if v.estado == 'disponible']
        
        return [
            VehiculoResponse(
                id=v.id,
                modelo=v.modelo,
                tipo=v.tipo,
                capacidad_maxima_paquetes=v.capacidad_maxima_paquetes,
                velocidad_promedio_kmh=v.velocidad_promedio_kmh,
                activo=v.activo,
                estado=v.estado,
                asignado_a=v.asignado_a,
                fecha_creacion=v.fecha_creacion
            ) for v in vehiculos
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar vehículos: {str(e)}"
        )

@router.get("/vehiculos/{vehiculo_id}", response_model=VehiculoResponse)
def obtener_vehiculo(vehiculo_id: int, db: Session = Depends(get_db)):
    """
    Obtiene detalles de un vehículo específico
    """
    try:
        query = text("""
            SELECT 
                v.id, v.modelo, v.tipo, v.capacidad_maxima_paquetes,
                v.velocidad_promedio_kmh, v.activo, v.fecha_creacion,
                CASE 
                    WHEN a.id IS NOT NULL THEN 'asignado'
                    ELSE 'disponible'
                END as estado,
                u.nombre_completo as asignado_a
            FROM vehiculos v
            LEFT JOIN asignaciones a ON v.id = a.id_vehiculo AND a.estado = 'activa'
            LEFT JOIN usuarios u ON a.id_repartidor = u.id
            WHERE v.id = :vehiculo_id AND v.activo = TRUE
        """)
        
        result = db.execute(query, {"vehiculo_id": vehiculo_id})
        vehiculo = result.fetchone()
        
        if not vehiculo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )
        
        return VehiculoResponse(
            id=vehiculo.id,
            modelo=vehiculo.modelo,
            tipo=vehiculo.tipo,
            capacidad_maxima_paquetes=vehiculo.capacidad_maxima_paquetes,
            velocidad_promedio_kmh=vehiculo.velocidad_promedio_kmh,
            activo=vehiculo.activo,
            estado=vehiculo.estado,
            asignado_a=vehiculo.asignado_a,
            fecha_creacion=vehiculo.fecha_creacion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener vehículo: {str(e)}"
        )

# =========================
# ENDPOINTS - ASIGNACIONES
# =========================

@router.post("/asignaciones", response_model=AsignacionResponse)
def crear_asignacion(asignacion: AsignacionCreate, db: Session = Depends(get_db)):
    """
    Asigna un vehículo a un repartidor
    """
    try:
        # Verificar que el repartidor existe
        check_rep = text("SELECT id, nombre_completo FROM usuarios WHERE id = :id AND rol = 'repartidor' AND activo = TRUE")
        repartidor = db.execute(check_rep, {"id": asignacion.id_repartidor}).fetchone()
        
        if not repartidor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repartidor no encontrado o inactivo"
            )
        
        # Verificar que el vehículo existe y está disponible
        check_veh = text("""
            SELECT v.id, v.modelo, v.capacidad_maxima_paquetes
            FROM vehiculos v
            LEFT JOIN asignaciones a ON v.id = a.id_vehiculo AND a.estado = 'activa'
            WHERE v.id = :id AND v.activo = TRUE AND a.id IS NULL
        """)
        vehiculo = db.execute(check_veh, {"id": asignacion.id_vehiculo}).fetchone()
        
        if not vehiculo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehículo no disponible o ya está asignado"
            )
        
        # Verificar capacidad
        if asignacion.numero_paquetes > vehiculo.capacidad_maxima_paquetes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Número de paquetes excede la capacidad del vehículo ({vehiculo.capacidad_maxima_paquetes})"
            )
        
        # Crear asignación
        insert_query = text("""
            INSERT INTO asignaciones 
            (id_repartidor, id_vehiculo, numero_paquetes, ruta_municipio, estado)
            VALUES (:id_rep, :id_veh, :num_paq, :ruta, 'activa')
            RETURNING id, id_repartidor, id_vehiculo, numero_paquetes, 
                     ruta_municipio, estado, fecha_asignacion
        """)
        
        result = db.execute(insert_query, {
            "id_rep": asignacion.id_repartidor,
            "id_veh": asignacion.id_vehiculo,
            "num_paq": asignacion.numero_paquetes,
            "ruta": asignacion.ruta_municipio
        })
        
        nueva_asignacion = result.fetchone()
        db.commit()
        
        print(f"✅ Asignación creada: Vehículo {vehiculo.modelo} → Repartidor {repartidor.nombre_completo}")
        
        return AsignacionResponse(
            id=nueva_asignacion.id,
            id_repartidor=nueva_asignacion.id_repartidor,
            id_vehiculo=nueva_asignacion.id_vehiculo,
            numero_paquetes=nueva_asignacion.numero_paquetes,
            ruta_municipio=nueva_asignacion.ruta_municipio,
            estado=nueva_asignacion.estado,
            repartidor_nombre=repartidor.nombre_completo,
            vehiculo_modelo=vehiculo.modelo,
            fecha_asignacion=nueva_asignacion.fecha_asignacion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear asignación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear asignación: {str(e)}"
        )

@router.get("/asignaciones", response_model=List[AsignacionResponse])
def listar_asignaciones(
    activas_solo: bool = True,
    db: Session = Depends(get_db)
):
    """
    Lista todas las asignaciones o solo las activas
    """
    try:
        where_clause = "WHERE a.estado = 'activa'" if activas_solo else ""
        
        query = text(f"""
            SELECT 
                a.id, a.id_repartidor, a.id_vehiculo, a.numero_paquetes,
                a.ruta_municipio, a.estado, a.fecha_asignacion,
                u.nombre_completo as repartidor_nombre,
                v.modelo as vehiculo_modelo
            FROM asignaciones a
            JOIN usuarios u ON a.id_repartidor = u.id
            JOIN vehiculos v ON a.id_vehiculo = v.id
            {where_clause}
            ORDER BY a.fecha_asignacion DESC
        """)
        
        result = db.execute(query)
        asignaciones = result.fetchall()
        
        return [
            AsignacionResponse(
                id=a.id,
                id_repartidor=a.id_repartidor,
                id_vehiculo=a.id_vehiculo,
                numero_paquetes=a.numero_paquetes,
                ruta_municipio=a.ruta_municipio,
                estado=a.estado,
                repartidor_nombre=a.repartidor_nombre,
                vehiculo_modelo=a.vehiculo_modelo,
                fecha_asignacion=a.fecha_asignacion
            ) for a in asignaciones
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar asignaciones: {str(e)}"
        )

@router.delete("/asignaciones/{asignacion_id}")
def liberar_asignacion(asignacion_id: int, db: Session = Depends(get_db)):
    """
    Libera una asignación (marca como completada)
    """
    try:
        # Verificar que existe
        check_query = text("""
            SELECT a.id, u.nombre_completo, v.modelo
            FROM asignaciones a
            JOIN usuarios u ON a.id_repartidor = u.id
            JOIN vehiculos v ON a.id_vehiculo = v.id
            WHERE a.id = :id AND a.estado = 'activa'
        """)
        
        asignacion = db.execute(check_query, {"id": asignacion_id}).fetchone()
        
        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada o ya fue liberada"
            )
        
        # Actualizar estado
        update_query = text("""
            UPDATE asignaciones 
            SET estado = 'completada', fecha_fin = CURRENT_TIMESTAMP
            WHERE id = :id
        """)
        
        db.execute(update_query, {"id": asignacion_id})
        db.commit()
        
        print(f"✅ Asignación liberada: {asignacion.modelo} de {asignacion.nombre_completo}")
        
        return {
            "message": "Asignación liberada exitosamente",
            "asignacion_id": asignacion_id,
            "repartidor": asignacion.nombre_completo,
            "vehiculo": asignacion.modelo
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al liberar asignación: {str(e)}"
        )

# =========================
# ENDPOINTS - ESTADÍSTICAS
# =========================

@router.get("/estadisticas")
def obtener_estadisticas(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales de la flota
    """
    try:
        stats_query = text("""
            SELECT 
                (SELECT COUNT(*) FROM vehiculos WHERE activo = TRUE) as total_vehiculos,
                (SELECT COUNT(*) FROM vehiculos v 
                 LEFT JOIN asignaciones a ON v.id = a.id_vehiculo AND a.estado = 'activa'
                 WHERE v.activo = TRUE AND a.id IS NULL) as vehiculos_disponibles,
                (SELECT COUNT(*) FROM asignaciones WHERE estado = 'activa') as asignaciones_activas,
                (SELECT COUNT(*) FROM usuarios WHERE rol = 'repartidor' AND activo = TRUE) as total_repartidores
        """)
        
        result = db.execute(stats_query)
        stats = result.fetchone()
        
        return {
            "total_vehiculos": stats.total_vehiculos,
            "vehiculos_disponibles": stats.vehiculos_disponibles,
            "vehiculos_asignados": stats.total_vehiculos - stats.vehiculos_disponibles,
            "asignaciones_activas": stats.asignaciones_activas,
            "total_repartidores": stats.total_repartidores,
            "tasa_utilizacion": round((stats.asignaciones_activas / stats.total_vehiculos * 100), 2) if stats.total_vehiculos > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )