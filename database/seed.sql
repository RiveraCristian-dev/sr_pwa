-- ======================================================
-- DATOS DE PRUEBA - SIMULADOR DE RUTAS SUSTENTABLES
-- ======================================================
-- Usuarios de prueba
INSERT INTO usuarios (nombre, email, password_hash, rol)
VALUES (
        'Admin Principal',
        'admin@simulador.com',
        'hashed_password_123',
        'admin'
    ),
    (
        'Repartidor Juan',
        'juan@simulador.com',
        'hashed_password_456',
        'repartidor'
    ),
    (
        'Repartidor Maria',
        'maria@simulador.com',
        'hashed_password_789',
        'repartidor'
    );
-- Vehículos de prueba (DATOS REALISTAS)
INSERT INTO vehiculos (
        tipo,
        nombre_modelo,
        consumo_gasolina,
        consumo_electrico,
        precio_gasolina,
        precio_kwh,
        capacidad_carga_kg,
        capacidad_carga_m3,
        autonomia_km,
        factor_emisiones_gasolina,
        factor_emisiones_electrico,
        rendimiento_gasolina,
        rendimiento_electrico,
        costo_mantenimiento_km,
        valor_aproximado,
        velocidad_promedio_kmh
    )
VALUES -- Gasolina
    (
        'gasolina',
        'Ford Transit 2023',
        12.5,
        NULL,
        22.50,
        NULL,
        1200,
        12.5,
        450,
        2.31,
        NULL,
        8.0,
        NULL,
        0.15,
        450000,
        30.0
    ),
    -- Híbrido
    (
        'hibrido',
        'Toyota Prius 2023',
        4.5,
        15.0,
        22.50,
        2.50,
        400,
        4.2,
        850,
        2.31,
        0.45,
        22.2,
        6.7,
        0.12,
        550000,
        28.0
    ),
    -- Eléctrico
    (
        'electrico',
        'Tesla Model 3',
        NULL,
        15.5,
        NULL,
        2.50,
        400,
        3.5,
        450,
        NULL,
        0.45,
        NULL,
        6.45,
        0.08,
        800000,
        32.0
    );
-- Nodos del mapa (CDMX ejemplo)
INSERT INTO nodos_del_mapa (latitud, longitud, nombre, tipo, direccion)
VALUES -- Almacén central
    (
        19.432608,
        -99.133209,
        'Almacén Central',
        'almacen',
        'Centro Histórico CDMX'
    ),
    -- Clientes
    (
        19.435422,
        -99.144325,
        'Cliente Condesa',
        'cliente',
        'Av. Michoacán 123, Condesa'
    ),
    (
        19.401235,
        -99.171447,
        'Cliente Coyoacán',
        'cliente',
        'Centro Coyoacán 45'
    ),
    (
        19.357798,
        -99.279100,
        'Cliente Santa Fe',
        'cliente',
        'Av. Vasco de Quiroga 1500'
    ),
    (
        19.490345,
        -99.124567,
        'Cliente Lindavista',
        'cliente',
        'Av. Instituto Técnico 800'
    ),
    -- Intersecciones importantes
    (
        19.426445,
        -99.152863,
        'Glorieta Insurgentes',
        'interseccion',
        'Insurgentes Sur esq. Michoacán'
    ),
    (
        19.389165,
        -99.177536,
        'Periférico Universidad',
        'interseccion',
        'Periférico esq. Universidad'
    ),
    (
        19.438423,
        -99.205367,
        'Tacuba Metro',
        'interseccion',
        'Metro Tacuba'
    );
-- Conexiones entre nodos (grafo de la ciudad)
INSERT INTO conexiones_mapa (
        id_nodo_origen,
        id_nodo_destino,
        distancia_km,
        tiempo_min,
        tipo_via,
        trafico_promedio
    )
VALUES -- Desde almacén central
    (1, 2, 3.2, 12.5, 'avenida', 0.3),
    (1, 5, 2.8, 10.2, 'calle', 0.2),
    (1, 6, 4.1, 15.8, 'avenida', 0.4),
    -- Conexiones en red
    (2, 3, 8.7, 25.3, 'avenida', 0.6),
    (2, 6, 2.1, 8.5, 'calle', 0.3),
    (3, 4, 12.3, 35.2, 'autopista', 0.7),
    (3, 7, 5.8, 18.9, 'avenida', 0.5),
    (4, 7, 6.9, 22.1, 'autopista', 0.6),
    (5, 6, 3.4, 13.2, 'calle', 0.4),
    (6, 7, 7.2, 24.5, 'avenida', 0.5),
    -- Conexiones bidireccionales (vuelta)
    (2, 1, 3.2, 12.5, 'avenida', 0.3),
    (5, 1, 2.8, 10.2, 'calle', 0.2),
    (6, 1, 4.1, 15.8, 'avenida', 0.4),
    (3, 2, 8.7, 25.3, 'avenida', 0.6),
    (6, 2, 2.1, 8.5, 'calle', 0.3),
    (4, 3, 12.3, 35.2, 'autopista', 0.7),
    (7, 3, 5.8, 18.9, 'avenida', 0.5),
    (7, 4, 6.9, 22.1, 'autopista', 0.6),
    (6, 5, 3.4, 13.2, 'calle', 0.4),
    (7, 6, 7.2, 24.5, 'avenida', 0.5);
-- Pedidos de ejemplo
INSERT INTO pedidos (
        id_usuario_admin,
        id_vehiculo,
        destino_lat,
        destino_lng,
        peso_kg,
        volumen_m3,
        descripcion,
        estado
    )
VALUES (
        1,
        1,
        19.435422,
        -99.144325,
        5.5,
        0.12,
        'Paquete documentos Condesa',
        'pendiente'
    ),
    (
        1,
        2,
        19.401235,
        -99.171447,
        15.2,
        0.45,
        'Mercancía Coyoacán',
        'asignado'
    ),
    (
        1,
        3,
        19.357798,
        -99.279100,
        8.7,
        0.23,
        'Electrónicos Santa Fe',
        'pendiente'
    );