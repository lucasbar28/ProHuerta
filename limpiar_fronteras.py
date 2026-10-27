# -*- coding: utf-8 -*-
import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
GEO_DIR = BASE_DIR / "datos" / "geospatial"
EXTENT_PATH = GEO_DIR / "barrios_extent.json"
RADIOS_PATH = GEO_DIR / "chascomus_radios_censales.geojson"
BARRIOS_PATH = GEO_DIR / "chascomus_barrios.geojson"

def calcular_distancia(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def main():
    print("Iniciando limpieza de fronteras superpuestas...")
    
    # 1. Cargar datos
    with open(EXTENT_PATH, "r", encoding="utf-8") as f:
        barrios_extent = json.load(f)
        
    with open(RADIOS_PATH, "r", encoding="utf-8") as f:
        radios_geojson = json.load(f)
        
    with open(BARRIOS_PATH, "r", encoding="utf-8") as f:
        barrios_geojson = json.load(f)

    # 2. Extraer centroides reales de los radios del INDEC
    radios_centroides = {}
    for feature in radios_geojson.get("features", []):
        props = feature["properties"]
        link = str(props.get("LINK"))
        lat = props.get("centroide_lat")
        lon = props.get("centroide_lon")
        if link and lat and lon:
            radios_centroides[link] = {"lat": lat, "lng": lon}

    # 3. Extraer centroides de los barrios
    barrios_centroides = {}
    for feature in barrios_geojson.get("features", []):
        props = feature["properties"]
        norm = props.get("barrio_norm")
        lat = props.get("lat_centroide")
        lon = props.get("lng_centroide")
        if norm and lat and lon:
            barrios_centroides[norm] = {"lat": lat, "lng": lon}

    # 4. Mapear qué barrios reclaman cada radio
    radio_to_barrios = {}
    for barrio, data in barrios_extent.items():
        for radio in data.get("radios_link", []):
            if radio not in radio_to_barrios:
                radio_to_barrios[radio] = []
            radio_to_barrios[radio].append(barrio)

    # 5. Resolver conflictos (asignar al barrio más cercano)
    limpio_barrios = {barrio: [] for barrio in barrios_extent}
    
    for radio, barrios in radio_to_barrios.items():
        if len(barrios) == 1:
            limpio_barrios[barrios[0]].append(radio)
        else:
            # Hay conflicto de superposición
            if radio in radios_centroides:
                r_lat = radios_centroides[radio]["lat"]
                r_lng = radios_centroides[radio]["lng"]
                
                mejor_barrio = barrios[0]
                distancia_minima = float('inf')
                
                for b in barrios:
                    if b in barrios_centroides:
                        d = calcular_distancia(
                            r_lat, r_lng, 
                            barrios_centroides[b]["lat"], 
                            barrios_centroides[b]["lng"]
                        )
                        if d < distancia_minima:
                            distancia_minima = d
                            mejor_barrio = b
                            
                limpio_barrios[mejor_barrio].append(radio)
            else:
                limpio_barrios[barrios[0]].append(radio)

    # 6. Actualizar y guardar el JSON de extensión
    for barrio in barrios_extent:
        barrios_extent[barrio]["radios_link"] = limpio_barrios[barrio]
        barrios_extent[barrio]["radios_count"] = len(limpio_barrios[barrio])
        
    with open(EXTENT_PATH, "w", encoding="utf-8") as f:
        json.dump(barrios_extent, f, indent=2, ensure_ascii=False)
        
    print("¡Limpieza completada! Archivo barrios_extent.json actualizado.")
    print("Por favor, vuelve a ejecutar 'python generar_barrios_reales.py' ahora.")

if __name__ == "__main__":
    main()