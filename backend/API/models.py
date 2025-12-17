from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Numeric, TIMESTAMP, Boolean, Text, ForeignKey, JSON, CheckConstraint, Time
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(150), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    telefono = Column(String(20))
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)  # 'admin' o 'repartidor'
    activo = Column(Boolean, default=True)
    fecha_registro = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ultimo_login = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("rol IN ('admin', 'repartidor')", name='rol_check'),
    )

class Vehiculo(Base):
    __tablename__ = 'vehiculos'
    
    id = Column(Integer, primary_key=True, index=True)
    modelo = Column(String(100), nullable=False)
    tipo = Column(String(20), nullable=False)  # 'gasolina', 'hibrido', 'electrico'
    capacidad_maxima_paquetes = Column(Integer, nullable=False)
    velocidad_promedio_kmh = Column(Numeric(5, 2), nullable=False)
    hora_envio = Column(Time)
    rendimiento_gasolina = Column(Numeric(8, 2))
    rendimiento_electrico = Column(Numeric(8, 2))
    precio_gasolina = Column(Numeric(8, 2))
    precio_kwh = Column(Numeric(8, 2))
    factor_emisiones_gasolina = Column(Numeric(8, 2), default=2.31)
    factor_emisiones_electrico = Column(Numeric(8, 2), default=0.45)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("tipo IN ('gasolina', 'hibrido', 'electrico')", name='tipo_vehiculo_check'),
        CheckConstraint("capacidad_maxima_paquetes > 0", name='capacidad_check'),
    )

class Asignacion(Base):
    __tablename__ = 'asignaciones'
    
    id = Column(Integer, primary_key=True, index=True)
    id_repartidor = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id', ondelete='CASCADE'), nullable=False)
    numero_paquetes = Column(Integer, default=0)
    ruta_municipio = Column(Text)
    estado = Column(String(20), default='activa')
    fecha_asignacion = Column(TIMESTAMP(timezone=True), server_default=func.now())
    fecha_inicio = Column(TIMESTAMP(timezone=True))
    fecha_fin = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activa', 'completada', 'cancelada')", name='estado_asignacion_check'),
        CheckConstraint("numero_paquetes >= 0", name='paquetes_check'),
    )
    
    # Relaciones
    repartidor = relationship("Usuario", foreign_keys=[id_repartidor])
    vehiculo = relationship("Vehiculo", foreign_keys=[id_vehiculo])

class Pedido(Base):
    __tablename__ = 'pedidos'
    
    id = Column(Integer, primary_key=True, index=True)
    numero_pedido = Column(String(50), unique=True, nullable=False)
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id', ondelete='CASCADE'), nullable=False)
    capacidad_paquetes = Column(Integer)
    destino_entrega = Column(Text, nullable=False)
    estado = Column(String(20), default='pendiente')
    fecha_creacion = Column(TIMESTAMP(timezone=True), server_default=func.now())
    fecha_asignacion = Column(TIMESTAMP(timezone=True))
    fecha_entrega_estimada = Column(TIMESTAMP(timezone=True))
    fecha_entrega_real = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'procesando', 'en_ruta', 'entregado', 'cancelado')", name='estado_pedido_check'),
    )
    
    vehiculo = relationship("Vehiculo", foreign_keys=[id_vehiculo])

class RutaAsignada(Base):
    __tablename__ = 'rutas_asignadas'
    
    id = Column(Integer, primary_key=True, index=True)
    id_asignacion = Column(Integer, ForeignKey('asignaciones.id', ondelete='CASCADE'), nullable=False)
    id_pedido = Column(Integer, ForeignKey('pedidos.id', ondelete='SET NULL'))
    origen_direccion = Column(Text, nullable=False)
    destino_direccion = Column(Text, nullable=False)
    distancia_km = Column(Numeric(8, 2), nullable=False)
    tiempo_min = Column(Numeric(8, 2), nullable=False)
    ruta_mapquest = Column(JSONB, nullable=False)
    vehiculo_tipo = Column(String(20), nullable=False)
    consumo_data = Column(JSONB)
    costo_total = Column(Numeric(10, 2))
    emisiones_co2_kg = Column(Numeric(8, 2))
    fecha_calculo = Column(TIMESTAMP(timezone=True), server_default=func.now())
    activa = Column(Boolean, default=True)
    
    __table_args__ = (
        CheckConstraint("vehiculo_tipo IN ('gasolina', 'hibrido', 'electrico')", name='tipo_ruta_check'),
    )
    
    asignacion = relationship("Asignacion", foreign_keys=[id_asignacion])
    pedido = relationship("Pedido", foreign_keys=[id_pedido])