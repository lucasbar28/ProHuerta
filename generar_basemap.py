# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import io
import json
import logging
import math
from pathlib import Path

import requests
from PIL import Image, ImageEnhance
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_IMAGE = STATIC_DIR / "chascomus_basemap.jpg"
OUTPUT_META = STATIC_DIR / "chascomus_basemap.json"

WEST, SOUTH, EAST, NORTH = -58.105, -35.635, -57.915, -35.485
ZOOM = 14
TILE_SIZE = 256
BASE_TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
LABEL_TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
ATTRIBUTION = "Esri, Maxar, Earthstar Geographics, © OpenStreetMap contributors"


def lon_to_tile_x(lon: float, zoom: int) -> float:
    return (lon + 180.0) / 360.0 * (2**zoom)

def lat_to_tile_y(lat: float, zoom: int) -> float:
    lat_rad = math.radians(lat)
    return (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * (2**zoom)

def tile_x_to_lon(x: float, zoom: int) -> float:
    return x / (2**zoom) * 360.0 - 180.0

def tile_y_to_lat(y: float, zoom: int) -> float:
    return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / (2**zoom)))))

def fetch_tile(session: requests.Session, url_template: str, x: int, y: int) -> Image.Image:
    """Descarga una tesela utilizando una sesión configurada con reintentos automáticos."""
    url = url_template.format(z=ZOOM, x=x, y=y)
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except requests.exceptions.RequestException as e:
        logging.error(f"Fallo al descargar la tesela de {url}: {e}")
        raise RuntimeError("No se pudo descargar el tile") from e

def main() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    x_min = math.floor(lon_to_tile_x(WEST, ZOOM))
    x_max = math.floor(lon_to_tile_x(EAST, ZOOM))
    y_min = math.floor(lat_to_tile_y(NORTH, ZOOM))
    y_max = math.floor(lat_to_tile_y(SOUTH, ZOOM))
    
    columns = x_max - x_min + 1
    rows = y_max - y_min + 1
    canvas = Image.new("RGB", (columns * TILE_SIZE, rows * TILE_SIZE), (8, 15, 28))

    # Configurar sesión HTTP con estrategia robusta de reintentos
    session = requests.Session()
    retry_strategy = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "ProHuerta-Chascomus/1.0"})

    logging.info(f"Descargando matriz de {columns}x{rows} tiles...")
    
    for row, tile_y in enumerate(range(y_min, y_max + 1)):
        for column, tile_x in enumerate(range(x_min, x_max + 1)):
            base = fetch_tile(session, BASE_TILE_URL, tile_x, tile_y)
            labels = fetch_tile(session, LABEL_TILE_URL, tile_x, tile_y)
            tile = Image.alpha_composite(base, labels).convert("RGB")
            canvas.paste(tile, (column * TILE_SIZE, row * TILE_SIZE))

    logging.info("Aplicando mejoras de imagen y guardando...")
    canvas = ImageEnhance.Brightness(canvas).enhance(1.05)
    canvas = ImageEnhance.Contrast(canvas).enhance(1.03)
    canvas.save(OUTPUT_IMAGE, quality=88, optimize=True)

    bounds = [
        tile_x_to_lon(x_min, ZOOM),
        tile_y_to_lat(y_max + 1, ZOOM),
        tile_x_to_lon(x_max + 1, ZOOM),
        tile_y_to_lat(y_min, ZOOM),
    ]
    
    version = hashlib.md5(OUTPUT_IMAGE.read_bytes()).hexdigest()[:10]
    metadata = {
        "image": f"/static/chascomus_basemap.jpg?v={version}",
        "bounds": bounds,
        "zoom": ZOOM,
        "attribution": ATTRIBUTION,
        "width": canvas.width,
        "height": canvas.height,
    }
    
    OUTPUT_META.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    
    logging.info("Metadatos generados:")
    logging.info(json.dumps(metadata, ensure_ascii=False, indent=2))
    logging.info(f"Imagen lista: {OUTPUT_IMAGE} ({OUTPUT_IMAGE.stat().st_size} bytes)")

if __name__ == "__main__":
    main()