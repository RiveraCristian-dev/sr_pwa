import os
from sqlalchemy import text
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

# Importar conexión PostgreSQL
from backend.API.database import engine

# ==========================================================
# FUNCIONES DE CÁLCULO PARA POSTGRESQL NEON
# ==========================================================

def calcular_pedido(id_pedido, distancia_km):
    """
    Calcula métricas para un pedido específico
    Usa el esquema PostgreSQL Neon actualizado
    
    Args:
        id_pedido: ID del pedido en tabla 'pedidos'
        distancia_km: Distancia total en kilómetros
    
    Returns:
        Dict con todas las métricas calculadas
    """
    
    # Validación básica
    if not distancia_km or distancia_km <= 0:
        return {"error": "Distancia no válida"}
    
    if engine is None:
        return calcular_pedido_default(id_pedido, distancia_km)
    
    try:
        with engine.connect() as conn:
            # --------------------------------------------------
            # 1. OBTENER DATOS DEL PEDIDO
            # --------------------------------------------------
            query_pedido = text("""
                SELECT 
                    p.id,
                    p.numero_pedido,
                    p.id_vehiculo,
                    p.capacidad_paquetes,
                    p.destino_entrega,
                    p.estado,
                    v.modelo,
                    v.tipo,
                    v.capacidad_maxima_paquetes,
                    v.velocidad_promedio_kmh,
                    v.rendimiento_gasolina,
                    v.rendimiento_electrico,
                    v.precio_gasolina,
                    v.precio_kwh,
                    v.factor_emisiones_gasolina,
                    v.factor_emisiones_electrico
                FROM pedidos p
                JOIN vehiculos v ON p.id_vehiculo = v.id
                WHERE p.id = :id_pedido
            """)
            
            resultado = conn.execute(query_pedido, {"id_pedido": id_pedido})
            datos = resultado.fetchone()
            
            if not datos:
                return {"error": f"Pedido {id_pedido} no encontrado"}
            
            # --------------------------------------------------
            # 2. EXTRACCIÓN DE DATOS
            # --------------------------------------------------
            tipo_vehiculo = datos.tipo.lower()
            velocidad = float(datos.velocidad_promedio_kmh)
            
            # --------------------------------------------------
            # 3. CÁLCULOS ESPECÍFICOS POR TIPO DE VEHÍCULO
            # --------------------------------------------------
            if tipo_vehiculo == "gasolina":
                resultado = calcular_gasolina(datos, distancia_km)
                
            elif tipo_vehiculo == "electrico":
                resultado = calcular_electrico(datos, distancia_km)
                
            elif tipo_vehiculo == "hibrido":
                resultado = calcular_hibrido(datos, distancia_km)
                
            else:
                return {"error": f"Tipo de vehículo '{tipo_vehiculo}' no soportado"}
            
            # --------------------------------------------------
            # 4. CÁLCULO DE TIEMPO
            # --------------------------------------------------
            tiempo_horas = distancia_km / velocidad
            tiempo_minutos = tiempo_horas * 60
            
            # --------------------------------------------------
            # 5. PREPARAR RESPUESTA FINAL
            # --------------------------------------------------
            return {
                "pedido": {
                    "id": datos.id,
                    "numero_pedido": datos.numero_pedido,
                    "estado": datos.estado,
                    "destino": datos.destino_entrega,
                    "capacidad_paquetes": datos.capacidad_paquetes
                },
                "vehiculo": {
                    "modelo": datos.modelo,
                    "tipo": tipo_vehiculo,
                    "capacidad_maxima": datos.capacidad_maxima_paquetes,
                    "velocidad_promedio_kmh": velocidad
                },
                "distancia": {
                    "km": round(distancia_km, 2),
                    "millas": round(distancia_km * 0.621371, 2)
                },
                "tiempo": {
                    "minutos": round(tiempo_minutos, 1),
                    "horas": round(tiempo_horas, 2),
                    "formateado": f"{int(tiempo_minutos//60)}h {int(tiempo_minutos%60)}min"
                },
                "consumo": resultado["consumo"],
                "costo": {
                    "total": round(resultado["costo"], 2),
                    "moneda": "MXN",
                    "por_km": round(resultado["costo"] / distancia_km, 2) if distancia_km > 0 else 0
                },
                "emisiones": {
                    "co2_kg": round(resultado["emisiones"], 2),
                    "equivalente_arboles": round(resultado["emisiones"] / 21.77, 1),  # 1 árbol absorbe ~21.77kg CO2/año
                    "por_km": round(resultado["emisiones"] / distancia_km, 3) if distancia_km > 0 else 0
                },
                "sustentabilidad": {
                    "impacto": calcular_impacto_sustentabilidad(resultado["emisiones"], distancia_km),
                    "puntuacion": calcular_puntuacion_sustentable(tipo_vehiculo, resultado["emisiones"], distancia_km),
                    "recomendacion": generar_recomendacion(tipo_vehiculo, distancia_km)
                }
            }
            
    except Exception as e:
        print(f"❌ Error en cálculo PostgreSQL: {e}")
        return calcular_pedido_default(id_pedido, distancia_km)

# --------------------------------------------------
# FUNCIONES ESPECÍFICAS DE CÁLCULO
# --------------------------------------------------

def calcular_gasolina(datos, distancia_km):
    """Cálculos para vehículos a gasolina"""
    rendimiento = float(datos.rendimiento_gasolina)
    precio_litro = float(datos.precio_gasolina)
    factor_emisiones = float(datos.factor_emisiones_gasolina)
    
    litros = distancia_km / rendimiento
    costo = litros * precio_litro
    emisiones = litros * factor_emisiones
    
    return {
        "consumo": {"litros": round(litros, 2)},
        "costo": costo,
        "emisiones": emisiones
    }

def calcular_electrico(datos, distancia_km):
    """Cálculos para vehículos eléctricos"""
    rendimiento = float(datos.rendimiento_electrico)
    precio_kwh = float(datos.precio_kwh)
    factor_emisiones = float(datos.factor_emisiones_electrico)
    
    kwh = distancia_km / rendimiento
    costo = kwh * precio_kwh
    emisiones = kwh * factor_emisiones
    
    return {
        "consumo": {"kwh": round(kwh, 2)},
        "costo": costo,
        "emisiones": emisiones
    }

def calcular_hibrido(datos, distancia_km):
    """Cálculos para vehículos híbridos (60% gasolina, 40% eléctrico)"""
    rend_gas = float(datos.rendimiento_gasolina)
    rend_elec = float(datos.rendimiento_electrico)
    precio_gas = float(datos.precio_gasolina)
    precio_kwh = float(datos.precio_kwh)
    factor_gas = float(datos.factor_emisiones_gasolina)
    factor_elec = float(datos.factor_emisiones_electrico)
    
    # Distribución 60/40
    distancia_gas = distancia_km * 0.6
    distancia_elec = distancia_km * 0.4
    
    litros = distancia_gas / rend_gas
    kwh = distancia_elec / rend_elec
    
    costo = (litros * precio_gas) + (kwh * precio_kwh)
    emisiones = (litros * factor_gas) + (kwh * factor_elec)
    
    return {
        "consumo": {
            "litros": round(litros, 2),
            "kwh": round(kwh, 2),
            "distribucion": "60% gasolina, 40% eléctrico"
        },
        "costo": costo,
        "emisiones": emisiones
    }

def calcular_impacto_sustentabilidad(emisiones_kg, distancia_km):
    """Calcula impacto ambiental en términos comprensibles"""
    # 1 litro de gasolina produce ~2.31kg CO2
    # 1 árbol absorbe ~21.77kg CO2 al año
    
    equivalente_litros = emisiones_kg / 2.31
    arboles_necesarios = emisiones_kg / 21.77
    
    if emisiones_kg < 5:
        nivel = "Muy Bajo"
    elif emisiones_kg < 15:
        nivel = "Bajo"
    elif emisiones_kg < 30:
        nivel = "Moderado"
    elif emisiones_kg < 50:
        nivel = "Alto"
    else:
        nivel = "Muy Alto"
    
    return {
        "nivel": nivel,
        "equivalente_litros_gasolina": round(equivalente_litros, 1),
        "arboles_necesarios_anual": round(arboles_necesarios, 1),
        "eficiencia": f"{round(distancia_km / emisiones_kg, 1) if emisiones_kg > 0 else 0} km/kg CO2"
    }

def calcular_puntuacion_sustentable(tipo_vehiculo, emisiones_kg, distancia_km):
    """Calcula puntuación de sustentabilidad (0-100)"""
    # Factores base por tipo de vehículo
    factores = {
        "electrico": 0.8,
        "hibrido": 0.5,
        "gasolina": 0.2
    }
    
    factor_tipo = factores.get(tipo_vehiculo, 0.2)
    
    # Eficiencia (menos emisiones por km = mejor)
    if distancia_km > 0:
        eficiencia = emisiones_kg / distancia_km
    else:
        eficiencia = 1
    
    # Puntuación base
    puntuacion = 100 * factor_tipo
    
    # Ajustar por eficiencia
    if eficiencia < 0.1:  # Menos de 0.1kg CO2 por km
        puntuacion += 20
    elif eficiencia < 0.3:
        puntuacion += 10
    elif eficiencia > 0.8:  # Más de 0.8kg CO2 por km
        puntuacion -= 20
    elif eficiencia > 0.5:
        puntuacion -= 10
    
    return min(100, max(0, round(puntuacion)))

def generar_recomendacion(tipo_vehiculo, distancia_km):
    """Genera recomendaciones de optimización"""
    recomendaciones = []
    
    if tipo_vehiculo == "gasolina":
        recomendaciones.append("Considerar vehículo híbrido para distancias medias")
        if distancia_km > 50:
            recomendaciones.append("Optimizar ruta para reducir distancia")
    elif tipo_vehiculo == "hibrido":
        recomendaciones.append("Mantener batería cargada para maximizar modo eléctrico")
    elif tipo_vehiculo == "electrico":
        recomendaciones.append("Verificar estaciones de carga en la ruta")
    
    if distancia_km < 10:
        recomendaciones.append("Ideal para entregas urbanas")
    elif distancia_km > 100:
        recomendaciones.append("Considerar puntos de recarga/reabastecimiento intermedios")
    
    return recomendaciones

def calcular_pedido_default(id_pedido, distancia_km):
    """Cálculos por defecto (fallback)"""
    return {
        "pedido": {"id": id_pedido, "numero_pedido": "N/A", "estado": "desconocido"},
        "vehiculo": {"modelo": "Default", "tipo": "gasolina", "velocidad_promedio_kmh": 40},
        "distancia": {"km": distancia_km},
        "tiempo": {"minutos": round((distancia_km / 40) * 60, 1)},
        "consumo": {"litros": round(distancia_km / 12, 2)},
        "costo": {"total": round(distancia_km / 12 * 22.5, 2), "moneda": "MXN"},
        "emisiones": {"co2_kg": round(distancia_km / 12 * 2.31, 2)},
        "sustentabilidad": {"impacto": "Estimado", "puntuacion": 50},
        "mensaje": "Usando valores por defecto"
    }

# ==========================================================
# FUNCIONES ADICIONALES PARA FORMULARIOS
# ==========================================================

def calcular_ruta_sustentable(id_asignacion, distancia_km):
    """
    Calcula métricas para una asignación completa
    (Para mostrar en panel de repartidor)
    """
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    a.id,
                    a.numero_paquetes,
                    a.ruta_municipio,
                    u.nombre_completo as repartidor,
                    v.modelo,
                    v.tipo,
                    v.capacidad_maxima_paquetes,
                    v.velocidad_promedio_kmh,
                    v.rendimiento_gasolina,
                    v.rendimiento_electrico,
                    v.precio_gasolina,
                    v.precio_kwh
                FROM asignaciones a
                JOIN usuarios u ON a.id_repartidor = u.id
                JOIN vehiculos v ON a.id_vehiculo = v.id
                WHERE a.id = :id_asignacion
            """)
            
            datos = conn.execute(query, {"id_asignacion": id_asignacion}).fetchone()
            
            if not datos:
                return {"error": "Asignación no encontrada"}
            
            # Calcular métricas básicas
            resultado = calcular_pedido(0, distancia_km)  # Usar cálculo genérico
            
            # Añadir información específica de asignación
            resultado["asignacion"] = {
                "id": datos.id,
                "repartidor": datos.repartidor,
                "paquetes": datos.numero_paquetes,
                "municipio": datos.ruta_municipio,
                "ocupacion": f"{(datos.numero_paquetes / datos.capacidad_maxima_paquetes) * 100:.1f}%"
            }
            
            return resultado
            
    except Exception as e:
        return {"error": f"Error en cálculo: {str(e)}"}

def verificar_capacidad_vehiculo(id_vehiculo, numero_paquetes):
    """
    Verifica si un vehículo tiene capacidad para cierta cantidad de paquetes
    (Para formulario de asignación)
    """
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT capacidad_maxima_paquetes, modelo
                FROM vehiculos 
                WHERE id = :id_vehiculo AND activo = TRUE
            """)
            
            vehiculo = conn.execute(query, {"id_vehiculo": id_vehiculo}).fetchone()
            
            if not vehiculo:
                return {"error": "Vehículo no encontrado o inactivo"}
            
            capacidad = vehiculo.capacidad_maxima_paquetes
            disponible = capacidad - numero_paquetes
            
            return {
                "vehiculo": vehiculo.modelo,
                "capacidad_maxima": capacidad,
                "paquetes_solicitados": numero_paquetes,
                "disponible": max(0, disponible),
                "sobrecarga": max(0, -disponible),
                "valido": numero_paquetes <= capacidad,
                "porcentaje_uso": f"{(numero_paquetes / capacidad) * 100:.1f}%" if capacidad > 0 else "0%"
            }
            
    except Exception as e:
        return {"error": f"Error en verificación: {str(e)}"}