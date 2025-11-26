-- ============================================
-- SIMULADOR DE RUTAS 
-- ============================================
-- ============================================
-- TABLA: usuarios 
-- ============================================
CREATE TABLE usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'repartidor') NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- ============================================
--TABLA: Vehiculos
-- ============================================
CREATE TABLE vehiculos (
    id_vehiculo INT PRIMARY KEY AUTO_INCREMENT,
    tipo ENUM('gasolina', 'hibrido', 'electrico') NOT NULL,
    nombre_modelo VARCHAR(100) NOT NULL --Datos para calculos 
    consumo_gasolina FLOAT,
    consumo_electrico FLOAT,
    precio_gasolina FLOAT,
    precio_kwh FLOAT,
    capacidad_carga_kg FLOAT,
    capacidad_carga_m3 FLOAT,
    autonomia_km FLOAT,
    --Calculos mejorados
    factor_emisiones_gasolina FLOAT DEFAULT 2.31,
    factor_emisiones_electrico FLOAT DEFAULT.45,
    rendimiento_gasolina FLOAT,
    rendimiento_electrico FLOAT,
    costo_mantenimiento_km FLOAT,
    valor_aproximado FLOAT,
    velocidad_promedio_kmh FLOAT DEFAULT 25.0
);
-- ============================================
--TABLA: nodos_del_mapa
-- ============================================
CREATE TABLE nodos_del_mapa (
    id_nodo INT PRIMARY KEY AUTO_INCREMENT,
    latitud DECIMAL(10, 8) NOT NULL,
    longitud DECIMAL(11, 8) NOT NULL,
    nombre VARCHAR(100),
    tipo ENUM(
        'alamcen',
        'cliente',
        'interseccion',
        'punto_interes'
    ) NOT NULL,
    direccion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_coordenadas (latitud, longitud),
    INDEX idx_tipo (tipo)
);
-- ============================================
--TABLA: conexiones_mapa
-- ============================================
CREATE TABLE conexiones_mapa (
    id_conexion INT PRIMARY KEY AUTO_INCREMENT,
    id_nodo_origen INT NOT NULL,
    id_nodo_destino INT NOT NULL,
    distancia_km DECIMAL(8, 3) NOT NULL,
    tiempo_min DECIMAL(8, 2) NOT NULL,
    tipo_via ENUM ('autopista', 'avenida', 'calle', 'atajo') DEFAULT 'calle',
    trafico_promedio DECIMAL(3, 2) DEFAULT 0.0 FOREIGN KEY (id_nodo_origen) REFERENCES nodos_del_mapa(id_nodo) ON DELETE CASCADE,
    FOREIGN KEY (id_nodo_destino) REFERENCES nodos_del_mapa(id_nodo) ON DELETE CASCADE,
    UNIQUE KEY unique_conexion (id_nodo_origen, id_nodo_destino),
    INDEX idx_origen (id_nodo_origen),
    INDEX idx_destino (id_nodo_destino)
);
-- ============================================
-- TABLA: pedidos 
-- ============================================
CREATE TABLE pedidos (
    id_pedido INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario_admin INT NOT NULL,
    id_vehiculo INT,
    destino_lat DECIMAL(8, 2) NOT NULL,
    destino_lng DECIMAL(8, 4) NOT NULL,
    descripcion TEXT,
    estado ENUM(
        'pendiendte',
        'asignado',
        'en_ruta',
        'entregado',
        'cancelado'
    ) DEFAULT 'pendiente',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pedido_admin FOREIGN KEY (id_usuario_admin) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_pedido_vehiculo -- NUEVA RELACIÓN
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo) ON DELETE
    SET NULL,
        INDEX idx_destino (destino_lat, destino_lng),
        INDEX idx_estado (estado)
);
-- ============================================
-- TABLA: entregas
-- ============================================
CREATE TABLE entregas (
    id_entrega INT PRIMARY KEY AUTO_INCREMENT,
    id_pedido INT NOT NULL,
    id_usuario_repartidor INT NOT NULL,
    estado ENUM('asiagnado', 'en_ruta', 'entregado') DEFAULT 'asignado',
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP NULL,
    CONSTRAINT fk_entrega_pedido FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_entrega_repartidor FOREIGN KEY (id_usuario_repartidor) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    INDEX idx_estado_entrega (estado),
    INDEX idx_repartidor (id_usuario_repartidor)
);
-- ============================================
-- TABLA: rutas_optimizadas
-- ============================================
CREATE TABLE rutas_optimizadas (
    id_ruta INT PRIMARY KEY AUTO_INCREMENT,
    id_pedido INT NOT NULL,
    id_ususario INT NOT NULL,
    id_vehiculo INT NOT NULL,
    --almacenar de ruta
    origen_lat DECIMAL(10, 8) NOT NULL,
    origen_lng DECIMAL(11, 8) NOT NULL,
    ruta_calculada JSON,
    --metricas de la ruta 
    distancia_km DECIMAL(8, 3) NOT NULL,
    tiempo_estimado_min DECIMAL(8, 2) NOT NULL,
    energia_usada_kwh DECIMAL(8, 2),
    energia_usada_litros DECIMAL(8, 2),
    costo_estimado DECIMAL(8, 2) NOT NULL,
    emisiones_co2_kg DECIMAL(8, 2),
    modo ENUM('simulacion', 'real') NOT NULL,
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ruta_pedido FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_ruta_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_ruta_vehiculo FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo) ON DELETE RESTRICT,
    INDEX idx_modo (modo),
    INDEX idx_fecha_calculo (fecha_calculo)
);