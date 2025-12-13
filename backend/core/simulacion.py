import folium
import dijkstra

def generar_mapa_visual(G, ruta_geometria, incidentes, paradas_ordenadas, nombre_archivo="simulacion_logistica.html"):
    if not G:
        print("Error: No se generó el Grafo (G).")
        return
    if not ruta_geometria:
        print("Error: No llegaron datos de geometría (ruta_geometria).")
        return

    # 1. Centrar Mapa
    primer_nodo = list(G.nodes())[0]
    centro_mapa = G.nodes[primer_nodo]['pos']
    mapa = folium.Map(location=centro_mapa, zoom_start=13, tiles='OpenStreetMap')

    # 2. Ruta Azul
    folium.PolyLine(ruta_geometria, color="#0055FF", weight=5, opacity=0.7).add_to(mapa)

    # 3. Tráfico (Igual que antes)
    for inc in incidentes:
        if inc['type'] == 4:
             folium.Circle(location=(inc['lat'], inc['lng']), radius=300, color='red', fill=True, popup=inc['fullDesc']).add_to(mapa)
        else:
             folium.Marker(location=(inc['lat'], inc['lng']), icon=folium.Icon(color='orange', icon='warning', prefix='fa'), popup=inc['fullDesc']).add_to(mapa)

    # 4. MARCADORES DE PARADAS (LOS DESTINOS REALES)
    # paradas_ordenadas viene de la API con el orden óptimo
    for i, parada in enumerate(paradas_ordenadas):
        coord = parada['pos']
        texto = parada['dir']
        
        if i == 0:
            # INICIO / ALMACÉN
            folium.Marker(
                location=coord,
                popup=f"<b>ALMACÉN (SALIDA)</b><br>{texto}",
                icon=folium.Icon(color='green', icon='home', prefix='fa')
            ).add_to(mapa)
        elif i == len(paradas_ordenadas) - 1:
            # FIN (REGRESO AL ALMACÉN)
            # Solo ponemos un icono diferente si es diferente coordenada, 
            # pero como es retorno, suele caer encima del verde. 
            # Lo ponemos un poco desplazado o con otro icono.
            pass # No dibujamos nada para no tapar el icono de salida
        else:
            # PARADAS DE ENTREGA (1, 2, 3...)
            folium.Marker(
                location=coord,
                popup=f"<b>ENTREGA #{i}</b><br>{texto}",
                icon=folium.Icon(color='blue', icon='truck', prefix='fa')
            ).add_to(mapa)
            
            # Ponemos un número grande sobre el mapa
            folium.Marker(
                location=coord,
                icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; background: blue; border-radius: 50%; width: 20px; height: 20px; text-align: center; font-weight: bold; border: 2px solid white;">{i}</div>""")
            ).add_to(mapa)

    # 5. Puntos de navegación (instrucciones giro a giro)
    for node_id in G.nodes():
        datos = G.nodes[node_id]
        # Solo dibujamos puntos pequeños, no marcadores grandes
        folium.CircleMarker(location=datos['pos'], radius=2, color='gray', popup=datos['desc']).add_to(mapa)

    mapa.save(nombre_archivo)
    print(f"\nMapa Logístico generado: {nombre_archivo}")

# --- BLOQUE PRINCIPAL INTERACTIVO ---
if __name__ == "__main__":
    API_KEY = "0wSs0qcTStL21HNT4VhipGi7CDsjXnkw"
    
    print("--- SISTEMA DE GESTIÓN DE RUTAS Y ENTREGAS ---")
    print("Nota: El sistema optimizará el orden de las entregas automáticamente.")
    
    lugares = []
    
    # 1. Pedir Inicio
    inicio = input("1. Ingrese dirección de SALIDA (Almacén): ")
    if not inicio: inicio = "Zocalo, Mexico City" # Default por si das enter vacio
    lugares.append(inicio)
    
    # 2. Pedir Destinos
    contador = 1
    while True:
        destino = input(f"2. Ingrese Destino de entrega #{contador} (o escriba 'fin'): ")
        if destino.lower() == 'fin':
            break
        lugares.append(destino)
        contador += 1
        
    # 3. Añadir Retorno (Vuelta al inicio)
    print("-> Añadiendo ruta de regreso al almacén...")
    lugares.append(inicio)
    
    if len(lugares) < 3:
        print("Error: Necesitas al menos Salida y 1 Destino.")
    else:
        print(f"\nCalculando ruta óptima para {len(lugares)-1} paradas...")
        
        # Llamamos a la nueva función multiparada
        maniobras, geometria, bbox, orden = dijkstra.obtener_ruta_multiparada(API_KEY, lugares, optimizar=True)
        
        if maniobras:
            # Imprimimos el orden sugerido
            print("\n--- ORDEN DE RUTA OPTIMIZADO ---")
            for i, parada in enumerate(orden):
                tipo = "ALMACÉN" if i==0 or i==len(orden)-1 else f"ENTREGA {i}"
                print(f"{i}. {tipo}: {parada['dir']}")
            
            print("\nDescargando tráfico...")
            incidentes = dijkstra.obtener_incidencias_trafico(API_KEY, bbox)
            
            print("Construyendo visualización...")
            grafo = dijkstra.construir_grafo_logico(maniobras)
            generar_mapa_visual(grafo, geometria, incidentes, orden)
        else:
            print("No se pudo calcular la ruta.")