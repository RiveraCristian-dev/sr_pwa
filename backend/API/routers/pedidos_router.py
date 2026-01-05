from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, and_

from ..database import get_db

router = APIRouter()

# =========================
# MODELOS PYDANTIC
# =========================

class PedidoCreate(BaseModel):
    numero_pedido: str
    id_repartidor: int
    id_vehiculo: int
    destino_entrega: str
    capacidad_paquetes: int
    estado: str = "pendiente"

class PedidoResponse(BaseModel):
    id: int
    numero_pedido: str
    id_repartidor: int
    nombre_repartidor: str
    id_vehiculo: int
    modelo_vehiculo: str
    tipo_vehiculo: str
    destino_entrega: str
    capacidad_paquetes: int
    estado: str
    fecha_creacion: datetime
    fecha_asignacion: Optional[datetime] = None
    fecha_entrega_estimada: Optional[datetime] = None

class EstadisticasResponse(BaseModel):
    total_pedidos: int
    pedidos_pendientes: int
    pedidos_en_ruta: int
    pedidos_entregados: int
    capacidad_total: int
    repartidores_activos: int

# =========================
# ENDPOINTS
# =========================

@router.post("/crear", response_model=PedidoResponse)
def crear_pedido_completo(pedido: PedidoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo pedido con validación de asignación repartidor-vehículo
    """
    try:
        print(f"📦 Creando pedido: {pedido.numero_pedido} - Repartidor: {pedido.id_repartidor} - Vehículo: {pedido.id_vehiculo}")
        
        # 1. Verificar que el número de pedido no exista
        check_query = text("SELECT id FROM pedidos WHERE numero_pedido = :numero")
        pedido_existente = db.execute(check_query, {"numero": pedido.numero_pedido}).fetchone()
        
        if pedido_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un pedido con ese número"
            )
        
        # 2. Verificar que el repartidor existe y es repartidor
        repartidor_query = text("""
            SELECT id, nombre_completo 
            FROM usuarios 
            WHERE id = :id AND rol = 'repartidor' AND activo = TRUE
        """)
        repartidor = db.execute(repartidor_query, {"id": pedido.id_repartidor}).fetchone()
        
        if not repartidor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El repartidor no existe, no es repartidor o no está activo"
            )
        
        # 3. Verificar que el vehículo existe
        vehiculo_query = text("""
            SELECT id, modelo, tipo 
            FROM vehiculos 
            WHERE id = :id AND activo = TRUE
        """)
        vehiculo = db.execute(vehiculo_query, {"id": pedido.id_vehiculo}).fetchone()
        
        if not vehiculo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El vehículo no existe o no está activo"
            )
        
        # 4. Verificar que existe asignación repartidor-vehículo (o crearla)
        asignacion_query = text("""
            SELECT id 
            FROM asignaciones 
            WHERE id_repartidor = :repartidor AND id_vehiculo = :vehiculo AND estado = 'activa'
        """)
        asignacion = db.execute(asignacion_query, {
            "repartidor": pedido.id_repartidor,
            "vehiculo": pedido.id_vehiculo
        }).fetchone()
        
        if not asignacion:
            print(f"⚠️ No hay asignación activa. Creando nueva asignación...")
            # Crear nueva asignación automáticamente
            crear_asignacion_query = text("""
                INSERT INTO asignaciones (id_repartidor, id_vehiculo, numero_paquetes, estado)
                VALUES (:repartidor, :vehiculo, :paquetes, 'activa')
                RETURNING id
            """)
            
            result = db.execute(crear_asignacion_query, {
                "repartidor": pedido.id_repartidor,
                "vehiculo": pedido.id_vehiculo,
                "paquetes": pedido.capacidad_paquetes
            })
            nueva_asignacion = result.fetchone()
            db.commit()
            print(f"✅ Asignación creada: ID {nueva_asignacion.id}")
        
        # 5. Validar estado
        estados_validos = ["pendiente", "procesando", "en_ruta", "entregado", "cancelado"]
        if pedido.estado not in estados_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado no válido. Use: {', '.join(estados_validos)}"
            )
        
        # 6. Validar capacidad del vehículo
        capacidad_vehiculo_query = text("SELECT capacidad_maxima_paquetes FROM vehiculos WHERE id = :id")
        capacidad_max = db.execute(capacidad_vehiculo_query, {"id": pedido.id_vehiculo}).fetchone()
        
        if capacidad_max and pedido.capacidad_paquetes > capacidad_max[0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Capacidad excedida. Máximo permitido: {capacidad_max[0]} paquetes"
            )
        
        # 7. Insertar el pedido
        insert_query = text("""
            INSERT INTO pedidos 
            (numero_pedido, id_vehiculo, capacidad_paquetes, destino_entrega, estado)
            VALUES (:numero, :vehiculo, :capacidad, :destino, :estado)
            RETURNING id, numero_pedido, id_vehiculo, capacidad_paquetes, 
                     destino_entrega, estado, fecha_creacion, fecha_asignacion,
                     fecha_entrega_estimada
        """)
        
        result = db.execute(insert_query, {
            "numero": pedido.numero_pedido,
            "vehiculo": pedido.id_vehiculo,
            "capacidad": pedido.capacidad_paquetes,
            "destino": pedido.destino_entrega,
            "estado": pedido.estado
        })
        
        nuevo_pedido = result.fetchone()
        db.commit()
        
        print(f"✅ Pedido creado exitosamente: ID {nuevo_pedido.id}")
        
        # 8. Retornar respuesta completa
        return {
            "id": nuevo_pedido.id,
            "numero_pedido": nuevo_pedido.numero_pedido,
            "id_repartidor": pedido.id_repartidor,
            "nombre_repartidor": repartidor.nombre_completo,
            "id_vehiculo": nuevo_pedido.id_vehiculo,
            "modelo_vehiculo": vehiculo.modelo,
            "tipo_vehiculo": vehiculo.tipo,
            "destino_entrega": nuevo_pedido.destino_entrega,
            "capacidad_paquetes": nuevo_pedido.capacidad_paquetes,
            "estado": nuevo_pedido.estado,
            "fecha_creacion": nuevo_pedido.fecha_creacion,
            "fecha_asignacion": nuevo_pedido.fecha_asignacion,
            "fecha_entrega_estimada": nuevo_pedido.fecha_entrega_estimada
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear pedido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear pedido: {str(e)}"
        )

@router.get("/", response_model=List[PedidoResponse])
def listar_pedidos(
    estado: Optional[str] = None,
    repartidor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos los pedidos con opciones de filtro
    - estado: filtrar por estado
    - repartidor_id: filtrar por repartidor
    """
    try:
        # Construir query base con JOINs
        query_base = """
            SELECT 
                p.id,
                p.numero_pedido,
                p.id_vehiculo,
                p.capacidad_paquetes,
                p.destino_entrega,
                p.estado,
                p.fecha_creacion,
                p.fecha_asignacion,
                p.fecha_entrega_estimada,
                u.id as repartidor_id,
                u.nombre_completo as repartidor_nombre,
                v.modelo as vehiculo_modelo,
                v.tipo as vehiculo_tipo
            FROM pedidos p
            JOIN vehiculos v ON p.id_vehiculo = v.id
            JOIN asignaciones a ON v.id = a.id_vehiculo
            JOIN usuarios u ON a.id_repartidor = u.id
            WHERE 1=1
        """
        
        params = {}
        
        # Aplicar filtros
        if estado:
            query_base += " AND p.estado = :estado"
            params["estado"] = estado
            
        if repartidor_id:
            query_base += " AND u.id = :repartidor_id"
            params["repartidor_id"] = repartidor_id
        
        query_base += " ORDER BY p.fecha_creacion DESC"
        
        query = text(query_base)
        result = db.execute(query, params)
        pedidos = result.fetchall()
        
        # Transformar resultados
        return [
            {
                "id": p.id,
                "numero_pedido": p.numero_pedido,
                "id_repartidor": p.repartidor_id,
                "nombre_repartidor": p.repartidor_nombre,
                "id_vehiculo": p.id_vehiculo,
                "modelo_vehiculo": p.vehiculo_modelo,
                "tipo_vehiculo": p.vehiculo_tipo,
                "destino_entrega": p.destino_entrega,
                "capacidad_paquetes": p.capacidad_paquetes,
                "estado": p.estado,
                "fecha_creacion": p.fecha_creacion,
                "fecha_asignacion": p.fecha_asignacion,
                "fecha_entrega_estimada": p.fecha_entrega_estimada
            }
            for p in pedidos
        ]
        
    except Exception as e:
        print(f"❌ Error al listar pedidos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener pedidos: {str(e)}"
        )

@router.get("/estadisticas", response_model=EstadisticasResponse)
def obtener_estadisticas(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de pedidos
    """
    try:
        # Estadísticas de pedidos
        pedidos_query = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN estado = 'pendiente' THEN 1 END) as pendientes,
                COUNT(CASE WHEN estado = 'en_ruta' THEN 1 END) as en_ruta,
                COUNT(CASE WHEN estado = 'entregado' THEN 1 END) as entregados,
                COALESCE(SUM(capacidad_paquetes), 0) as capacidad_total
            FROM pedidos
        """)
        
        pedidos_stats = db.execute(pedidos_query).fetchone()
        
        # Repartidores activos
        repartidores_query = text("""
            SELECT COUNT(DISTINCT id_repartidor) 
            FROM asignaciones 
            WHERE estado = 'activa'
        """)
        
        repartidores_activos = db.execute(repartidores_query).fetchone()[0] or 0
        
        return {
            "total_pedidos": pedidos_stats.total or 0,
            "pedidos_pendientes": pedidos_stats.pendientes or 0,
            "pedidos_en_ruta": pedidos_stats.en_ruta or 0,
            "pedidos_entregados": pedidos_stats.entregados or 0,
            "capacidad_total": pedidos_stats.capacidad_total or 0,
            "repartidores_activos": repartidores_activos
        }
        
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )

@router.get("/repartidores")
def obtener_repartidores_activos(db: Session = Depends(get_db)):
    """
    Obtiene lista de repartidores activos con sus asignaciones
    (Para poblar dropdown en frontend)
    """
    try:
        query = text("""
            SELECT 
                u.id,
                u.nombre_completo,
                u.email,
                u.telefono,
                v.id as vehiculo_id,
                v.modelo as vehiculo_modelo,
                v.tipo as vehiculo_tipo,
                a.id as asignacion_id,
                a.estado as asignacion_estado
            FROM usuarios u
            LEFT JOIN asignaciones a ON u.id = a.id_repartidor AND a.estado = 'activa'
            LEFT JOIN vehiculos v ON a.id_vehiculo = v.id
            WHERE u.rol = 'repartidor' AND u.activo = TRUE
            ORDER BY u.nombre_completo
        """)
        
        result = db.execute(query)
        repartidores = result.fetchall()
        
        return {
            "total": len(repartidores),
            "repartidores": [
                {
                    "id": r.id,
                    "nombre_completo": r.nombre_completo,
                    "email": r.email,
                    "telefono": r.telefono,
                    "vehiculo_asignado": {
                        "id": r.vehiculo_id,
                        "modelo": r.vehiculo_modelo,
                        "tipo": r.vehiculo_tipo
                    } if r.vehiculo_id else None,
                    "asignacion_activa": r.asignacion_estado == "activa"
                }
                for r in repartidores
            ]
        }
        
    except Exception as e:
        print(f"❌ Error al obtener repartidores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener repartidores: {str(e)}"
        )

@router.get("/vehiculos")
def obtener_vehiculos_disponibles(db: Session = Depends(get_db)):
    """
    Obtiene lista de vehículos disponibles
    (Para poblar dropdown en frontend)
    """
    try:
        query = text("""
            SELECT 
                id,
                modelo,
                tipo,
                capacidad_maxima_paquetes,
                velocidad_promedio_kmh,
                rendimiento_gasolina,
                rendimiento_electrico,
                activo
            FROM vehiculos 
            WHERE activo = TRUE
            ORDER BY modelo
        """)
        
        result = db.execute(query)
        vehiculos = result.fetchall()
        
        return {
            "total": len(vehiculos),
            "vehiculos": [
                {
                    "id": v.id,
                    "modelo": v.modelo,
                    "tipo": v.tipo,
                    "capacidad_maxima": v.capacidad_maxima_paquetes,
                    "velocidad_promedio": v.velocidad_promedio_kmh,
                    "disponible": True  # Podrías añadir lógica para verificar asignaciones
                }
                for v in vehiculos
            ]
        }
        
    except Exception as e:
        print(f"❌ Error al obtener vehículos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener vehículos: {str(e)}"
        )

@router.put("/{pedido_id}/estado")
def actualizar_estado_pedido(
    pedido_id: int,
    nuevo_estado: str,
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de un pedido
    """
    try:
        # Verificar que el pedido existe
        check_query = text("SELECT id FROM pedidos WHERE id = :id")
        pedido = db.execute(check_query, {"id": pedido_id}).fetchone()
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado"
            )
        
        # Validar estado
        estados_validos = ["pendiente", "procesando", "en_ruta", "entregado", "cancelado"]
        if nuevo_estado not in estados_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado no válido. Use: {', '.join(estados_validos)}"
            )
        
        # Actualizar estado
        update_query = text("""
            UPDATE pedidos 
            SET estado = :estado,
                fecha_asignacion = CASE 
                    WHEN :estado = 'en_ruta' AND fecha_asignacion IS NULL 
                    THEN CURRENT_TIMESTAMP 
                    ELSE fecha_asignacion 
                END,
                fecha_entrega_estimada = CASE 
                    WHEN :estado = 'en_ruta' AND fecha_entrega_estimada IS NULL 
                    THEN CURRENT_TIMESTAMP + INTERVAL '2 hours'
                    ELSE fecha_entrega_estimada 
                END,
                fecha_entrega_real = CASE 
                    WHEN :estado = 'entregado' 
                    THEN CURRENT_TIMESTAMP 
                    ELSE fecha_entrega_real 
                END
            WHERE id = :id
            RETURNING id, numero_pedido, estado
        """)
        
        result = db.execute(update_query, {"id": pedido_id, "estado": nuevo_estado})
        updated = result.fetchone()
        db.commit()
        
        print(f"✅ Estado actualizado: Pedido {updated.numero_pedido} -> {updated.estado}")
        
        return {
            "mensaje": f"Estado actualizado a '{nuevo_estado}'",
            "pedido_id": updated.id,
            "numero_pedido": updated.numero_pedido,
            "estado": updated.estado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error al actualizar estado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar estado: {str(e)}"
        )

@router.delete("/{pedido_id}")
def eliminar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """
    Elimina un pedido (solo si está pendiente)
    """
    try:
        # Verificar que el pedido existe y está pendiente
        check_query = text("""
            SELECT id, numero_pedido, estado 
            FROM pedidos 
            WHERE id = :id
        """)
        pedido = db.execute(check_query, {"id": pedido_id}).fetchone()
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado"
            )
        
        if pedido.estado != "pendiente":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden eliminar pedidos en estado 'pendiente'"
            )
        
        # Eliminar pedido
        delete_query = text("DELETE FROM pedidos WHERE id = :id")
        db.execute(delete_query, {"id": pedido_id})
        db.commit()
        
        print(f"✅ Pedido eliminado: {pedido.numero_pedido}")
        
        return {
            "mensaje": "Pedido eliminado exitosamente",
            "pedido_id": pedido_id,
            "numero_pedido": pedido.numero_pedido
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error al eliminar pedido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar pedido: {str(e)}"
        )