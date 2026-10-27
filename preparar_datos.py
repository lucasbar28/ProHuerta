# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "datos" / "datasetoriginales"
OUT_DIR = BASE_DIR / "datos" / "preparados"
INFO_DIR = BASE_DIR / "informe"

VALOR_SOBRE = 500
ESPECIES_POR_KIT = 10
CANASTA_VERSION = "OI_2025_2026_v1"

SOURCES = [
    {
        "anio": 2022,
        "temporada": "OI",
        "archivo": "2022 registro de huerta otoño-invierno 2022.xlsx",
        "hoja": "general",
        "esquema": "kit_generico",
    },
    {
        "anio": 2023,
        "temporada": "OI",
        "archivo": "2023 Relevamiento otoño invierno para filtrar.xlsx",
        "hoja": "DATOS",
        "esquema": "kit_generico",
    },
    {
        "anio": 2024,
        "temporada": "PV",
        "archivo": "2024 retiro de semillas prim-ver. 2024. + seguiminento + devolución.xlsx",
        "hoja": "familiares",
        "esquema": "especifico",
    },
    {
        "anio": 2025,
        "temporada": "OI",
        "archivo": "2025 RETIRO de semillas 2025 por primera vez OI 2025 (respuestas).xlsx",
        "hoja": "Respuestas de formulario 1",
        "esquema": "especifico",
    },
    {
        "anio": 2025,
        "temporada": "PV",
        "archivo": "2025 retiro de semillas por primera vez PV 2025 (respuestas).xlsx",
        "hoja": "Respuestas de formulario 1",
        "esquema": "especifico",
    },
    {
        "anio": 2026,
        "temporada": "OI",
        "archivo": "2026 Retiro de semillas por primera vez O-I 2026 (respuestas).xlsx",
        "hoja": "Respuestas de formulario 1",
        "esquema": "especifico",
    },
    {
        "anio": 2026,
        "temporada": "PV",
        "archivo": "2026 Retiro de semillas P-V 2026 (respuestas).xlsx",
        "hoja": "Respuestas de formulario 1",
        "esquema": "especifico",
    },
]

OFERTA_CATALOGO = {
    (2022, "OI"): 10,
    (2023, "OI"): 10,
    (2024, "PV"): 9,
    (2025, "OI"): 9,
    (2025, "PV"): 12,
    (2026, "OI"): 17,
    (2026, "PV"): 18,
}

INVALID_SPECIES = {
    "otra",
    "otras",
    "ninguna",
    "no",
    "no retira",
    "0",
    "4 paquetes",
    "paquetes",
    "nan",
    "none",
    "sin dato",
    "no especificado",
}

SPECIES_DISPLAY = {
    "acelga": "Acelga",
    "albahaca": "Albahaca",
    "apio": "Apio",
    "aromaticas": "Aromáticas",
    "arveja": "Arveja",
    "berenjena": "Berenjena",
    "brocoli": "Brócoli",
    "calendula": "Caléndula",
    "cebolla": "Cebolla",
    "choclo": "Choclo",
    "coliflor": "Coliflor",
    "espinaca": "Espinaca",
    "flor": "Flor",
    "habas": "Habas",
    "lechuga": "Lechuga",
    "morron": "Morrón",
    "oregano": "Orégano",
    "perejil": "Perejil",
    "puerro": "Puerro",
    "rabanito": "Rabanito",
    "remolacha": "Remolacha",
    "repollo": "Repollo",
    "rucula": "Rúcula",
    "tomate": "Tomate",
    "zanahoria": "Zanahoria",
    "zapallito": "Zapallito",
    "zapallo": "Zapallo",
    "zapallo de tronco": "Zapallo de tronco",
}

BARRIO_DISPLAY = {
    "sin_dato": "Sin dato",
    "chascomus": "Chascomús",
    "centro": "Centro",
    "hueco": "El Hueco",
    "noria chica": "Noria Chica",
    "ipora": "Ipora",
    "san cayetano": "San Cayetano",
    "fatima": "Fátima",
    "acceso norte": "Acceso Norte",
    "f moreno": "F. Moreno",
    "escribano": "Escribano",
    "jardin": "Barrio Jardín",
    "30 de mayo": "30 de Mayo",
    "lomas altas": "Lomas Altas",
    "san luis": "San Luis",
    "adela": "Adela",
    "giribone": "Giribone",
    "algarrobo": "El Algarrobo",
    "obispado": "El Obispado",
    "comi pini": "Comi Pini",
    "liberata": "La Liberata",
    "porteno": "Porteño",
    "villa lujan": "Villa Luján",
    "esmeralda": "La Esmeralda",
    "san jose obrero": "San José Obrero",
    "gallo blanco": "Gallo Blanco",
    "san jose": "San José",
    "esteban echeverria": "Esteban Echeverría",
    "anahi": "Anahí",
    "parque chascomus": "Parque Chascomús",
}

BARRIO_ALIASES = {
    "chasc" : "chascomus",
    "chascomus": "chascomus",
    "chasocmus": "chascomus",
    "chascomuis": "chascomus",
    "chascpomus": "chascomus",
    "chacomus": "chascomus",
    "chachomus": "chascomus",
    "vhascomus": "chascomus",
    "treinta de mayo": "30 de mayo",
    "la noria chica": "noria chica",
    "noria chica": "noria chica",
    "el hueco": "hueco",
    "hueco": "hueco",
    "el obispado": "obispado",
    "obispado": "obispado",
    "barrio jardin": "jardin",
    "jardin": "jardin",
    "f. moreno": "f moreno",
    "f moreno": "f moreno",
    "francisco moreno": "f moreno",
    "la liberata": "liberata",
    "liberata": "liberata",
    "la esmeralda": "esmeralda",
    "esmeralda": "esmeralda",
    "el algarrobo": "algarrobo",
    "algarrobo": "algarrobo",
    "comipini": "comi pini",
    "comi pini": "comi pini",
    "villa lujan": "villa lujan",
    "porteno": "porteno",
    "agarrobo": "algarrobo",
    "30de mayo": "30 de mayo",
    "30 de mauo": "30 de mayo",
    "ecribano": "escribano",
    "san cayentano": "san cayetano",
    "san juan fautista": "san juan bautista",
    "fernandez moreno": "f moreno",
    "pampitas": "pampita",
    "eucalipto": "eucaliptos",
    "coperativa": "cooperativa",
    "139 vivienda": "139 viviendas",
    "sauce": "sauces",
    "girado": "parque girado",
}


def fix_mojibake(value: object) -> str:
    if not isinstance(value, str):
        return value
    if any(x in value for x in ("Ã", "Â", "â€")):
        try:
            return value.encode("latin-1").decode("utf-8")
        except Exception:
            return value
    return value


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = fix_mojibake(str(value))
    text = re.sub(r"\s+", " ", text).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def norm_key(value: object) -> str:
    text = fix_mojibake(str(value))
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9/ ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def find_col(df: pd.DataFrame, *patterns: str, exclude: tuple[str, ...] = ()) -> str | None:
    wanted = [norm_key(p) for p in patterns]
    excluded = [norm_key(e) for e in exclude]
    for column in df.columns:
        key = norm_key(column)
        if all(p in key for p in wanted) and not any(e in key for e in excluded):
            return column
    return None


def parse_coords(value: object) -> tuple[float, float]:
    text = clean_text(value)
    if not text:
        return np.nan, np.nan
    parts = [p.strip() for p in re.split(r"[;]", text) if p.strip()]
    if len(parts) < 2:
        parts = [p.strip() for p in text.split(",")]
    if len(parts) < 2:
        return np.nan, np.nan
    try:
        lat = float(parts[0].replace(",", "."))
        lng = float(parts[1].replace(",", "."))
    except Exception:
        return np.nan, np.nan
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return np.nan, np.nan
    return lat, lng


def normalize_barrio(value: object) -> str:
    key = norm_key(value)
    if not key or key in {"nan", "none", "sin dato", "no especificado", "no", "."}:
        return "sin_dato"
    key = re.sub(r"\b(barrio|b|b°)\b", " ", key)
    key = re.sub(r"\bparaje\b", " ", key)
    key = re.sub(r"\b(la|el|los|las)\b", " ", key)
    key = re.sub(r"\s+", " ", key).strip()
    key = BARRIO_ALIASES.get(key, key)
    return key or "sin_dato"


def normalize_localidad(value: object) -> str:
    key = norm_key(value)
    if not key or key in {"nan", "none", "sin dato", "no especificado"}:
        return "sin_dato"
    if "chascom" in key or "chasc" in key or "chacom" in key or "chachom" in key or "vhascom" in key:
        return "chascomus"
    return key


def barrio_nombre(key: str) -> str:
    if key in BARRIO_DISPLAY:
        return BARRIO_DISPLAY[key]
    return " ".join(part.capitalize() for part in key.split())


def map_tipo_localizacion(value: object) -> str:
    key = norm_key(value)
    if "periurbana" in key:
        return "periurbana"
    if "urbana" in key:
        return "urbana"
    if "rural" in key:
        return "rural"
    return "no especificado"


def map_tipo_huerta(familiar_value: object, institucional_value: object) -> str:
    familiar = norm_key(familiar_value)
    institucional = norm_key(institucional_value)
    if familiar == "si":
        return "familiar"
    if familiar == "no":
        return "institucional"
    if institucional and institucional not in {"no", "no.", "no sabe", "familiar", ".", "..", "-"}:
        if "familiar" in institucional and len(institucional) < 25:
            return "familiar"
        return "institucional"
    if institucional == "familiar":
        return "familiar"
    return "no especificado"


def map_experiencia(value: object, anio: int, primera_vez: object = None) -> str:
    if anio <= 2023:
        primera = norm_key(primera_vez)
        if primera in {"si", "s"}:
            return "primera vez"
        return "no especificado"
    key = norm_key(value)
    if "primera" in key:
        return "primera vez"
    if "1 y 3" in key or "1 a 3" in key:
        return "1 a 3 años"
    if "mas de 3" in key:
        return "más de 3 años"
    return "no especificado"


def map_superficie(value: object) -> str:
    key = norm_key(value)
    if not key or key in {"nan", "none", "j"}:
        return "no especificado"
    if "hasta 5" in key:
        return "hasta 5 m2"
    if "6 y 20" in key or "6 a 20" in key:
        return "entre 6 y 20 m2"
    if "mas de 20" in key:
        return "más de 20 m2"
    if any(x in key for x in ("21 y 40", "41 y 60", "61 y 80", "81 y 100", "101 y 200", "mas de 200")):
        return "más de 20 m2"
    numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", key)]
    if numbers:
        if "por" in key and len(numbers) >= 2:
            area = numbers[0] * numbers[1]
        else:
            area = max(numbers)
        if area <= 5:
            return "hasta 5 m2"
        if area <= 20:
            return "entre 6 y 20 m2"
        return "más de 20 m2"
    return "no especificado"


def map_destino(value: object) -> str:
    key = norm_key(value)
    if not key:
        return "no especificado"
    if "venta" in key or "vende" in key:
        return "venta / excedentes"
    if "intercambio" in key or "intercambia" in key or "trueque" in key:
        return "autoconsumo e intercambio"
    if "autoconsumo" in key or "autocosumo" in key or "consumo" in key:
        return "autoconsumo"
    return "no especificado"


def map_ocupacion(value: object) -> str:
    key = norm_key(value)
    if not key or key in {".", "..", "-", "no", "0", "no especificado"}:
        return "no especificado"
    if "jubilad" in key or "pensionad" in key:
        return "jubilado/a"
    if "desocupad" in key or "desemplead" in key:
        return "desempleado/a"
    if "ama de casa" in key or ("amo" in key and "casa" in key) or "tareas del hogar" in key:
        return "ama de casa / tareas del hogar"
    if "estudiante" in key:
        return "estudiante"
    if "usuario" in key:
        return "otro"
    if any(x in key for x in ("autonom", "cuentaprop", "independiente", "autoempleo", "agricultor", "albanil", "costurera")):
        return "cuentapropista / autónomo/a"
    if any(x in key for x in ("emplead", "docente", "auxiliar", "bibliotecar", "plantinera", "enfermera", "kinesiolog")):
        return "empleado/a"
    return "otro"


def canonical_species(raw_value: object) -> str | None:
    key = norm_key(raw_value)
    key = re.sub(r"^[0-9\s.\-/]+", "", key).strip()
    if not key or key in INVALID_SPECIES:
        return None
    if "lechuga" in key:
        return "lechuga"
    if "tomate" in key:
        return "tomate"
    if "morron" in key or "pimiento" in key or "pimenton" in key:
        return "morron"
    if "zapallito" in key:
        return "zapallito"
    if "zapallo" in key:
        return "zapallo de tronco" if "tronco" in key else "zapallo"
    if "cebolla" in key:
        return "cebolla"
    if "arveja" in key:
        return "arveja"
    if "haba" in key:
        return "habas"
    if "flor" in key:
        return "flor"
    if "coclo" in key or "choclo" in key:
        return "choclo"
    if "acelga" in key:
        return "acelga"
    if "perejil" in key:
        return "perejil"
    if "espinaca" in key:
        return "espinaca"
    if "remolacha" in key:
        return "remolacha"
    if "rabanito" in key:
        return "rabanito"
    if "zanahoria" in key:
        return "zanahoria"
    if "rucula" in key:
        return "rucula"
    if "puerro" in key:
        return "puerro"
    if "brocoli" in key:
        return "brocoli"
    if "coliflor" in key:
        return "coliflor"
    if "repollo" in key:
        return "repollo"
    if "achicoria" in key:
        return "achicoria"
    if "calendula" in key:
        return "calendula"
    if "albahaca" in key:
        return "albahaca"
    if "berenjena" in key:
        return "berenjena"
    if "apio" in key:
        return "apio"
    if "oregano" in key:
        return "oregano"
    if "aromatic" in key:
        return "aromaticas"
    return key


def parse_species(value: object) -> tuple[list[tuple[str, str]], list[str], bool]:
    raw = clean_text(value)
    if not raw:
        return [], [], False
    found: list[tuple[str, str]] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for token in re.split(r"[;,\n]+", raw):
        token = clean_text(token)
        if not token:
            continue
        canonical = canonical_species(token)
        if canonical is None:
            invalid.append(token)
            continue
        if canonical not in seen:
            seen.add(canonical)
            found.append((canonical, token))
    return found, invalid, True


def species_nombre(canonical: str) -> str:
    return SPECIES_DISPLAY.get(canonical, " ".join(p.capitalize() for p in canonical.split()))


def sum_kits(row: pd.Series, kit_columns: list[str]) -> float:
    values = [pd.to_numeric(row[c], errors="coerce") for c in kit_columns]
    valid = [v for v in values if not pd.isna(v)]
    if not valid:
        return np.nan
    return float(sum(valid))


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INFO_DIR.mkdir(parents=True, exist_ok=True)

    solicitudes: list[dict] = []
    especies_observadas: list[dict] = []
    source_stats: list[dict] = []

    for source in SOURCES:
        archivo = source["archivo"]
        anio = source["anio"]
        temporada = source["temporada"]
        esquema = source["esquema"]
        df = pd.read_excel(RAW_DIR / archivo, sheet_name=source["hoja"])

        barrio_col = find_col(df, "barrio", exclude=("retirar",))
        localidad_col = find_col(df, "localidad")
        coords_col = find_col(df, "coord")
        tipo_loc_col = find_col(df, "tipo", "localizacion")
        fam_col = find_col(df, "tipo", "huerta", "familiar")
        inst_col = find_col(df, "tipo", "huerta", "institucional")
        primera_col = find_col(df, "primera", "vez")
        desde_col = find_col(df, "desde", "cuando")
        vinculado_col = find_col(df, "vinculado")
        superficie_col = find_col(df, "superficie")
        destino_col = find_col(df, "destino", "produccion", exclude=("11",))
        destino_alt_col = None
        for column in df.columns:
            key = norm_key(column)
            if key.startswith("11") and "destino" in key:
                destino_alt_col = column
                break
        ocupacion_col = find_col(df, "ocupacion", "huerter")
        variedades_col = find_col(df, "variedades", "retira", exclude=("devolucion",))
        referencia_col = find_col(df, "referencia")
        kit_columns = [c for c in df.columns if "kit" in norm_key(c)]

        stats = {
            "anio": anio,
            "temporada": temporada,
            "archivo": archivo,
            "hoja": source["hoja"],
            "filas": len(df),
            "kits_nulos": 0,
            "kits_cero": 0,
            "especies_nulas": 0,
            "especies_cero": 0,
        }

        for idx, row in df.iterrows():
            fila_origen = int(idx) + 2
            barrio_raw = clean_text(row[barrio_col]) if barrio_col else ""
            if not barrio_raw and anio == 2026:
                detalle_col = find_col(df, "retirar", "barrio")
                if detalle_col:
                    barrio_raw = clean_text(row[detalle_col])
            localidad_raw = clean_text(row[localidad_col]) if localidad_col else ""
            if anio in {2024, 2025} and temporada == "OI":
                barrio_raw = ""
            barrio_norm = normalize_barrio(barrio_raw)
            localidad_norm = normalize_localidad(localidad_raw)
            lat, lng = parse_coords(row[coords_col]) if coords_col else (np.nan, np.nan)

            tipo_localizacion = map_tipo_localizacion(row[tipo_loc_col]) if tipo_loc_col else "no especificado"
            familiar_value = row[fam_col] if fam_col else None
            institucional_value = row[inst_col] if inst_col else None
            tipo_huerta = map_tipo_huerta(familiar_value, institucional_value)
            experiencia = map_experiencia(
                row[desde_col] if desde_col else None,
                anio,
                row[primera_col] if primera_col else None,
            )
            superficie = map_superficie(row[superficie_col]) if superficie_col else "no especificado"
            destino_raw = row[destino_col] if destino_col else None
            if (not clean_text(destino_raw)) and destino_alt_col:
                destino_raw = row[destino_alt_col]
            destino = map_destino(destino_raw)
            ocupacion = map_ocupacion(row[ocupacion_col]) if ocupacion_col else "no especificado"

            anio_vinculacion = np.nan
            if anio <= 2023 and vinculado_col:
                match = re.search(r"(19|20)\d{2}", clean_text(row[vinculado_col]))
                if match:
                    anio_vinculacion = int(match.group(0))
            antiguedad_programa = anio - anio_vinculacion if not pd.isna(anio_vinculacion) else np.nan

            kits = np.nan
            cantidad_variedades = np.nan
            especies_equivalentes = np.nan
            cobertura = np.nan
            cobertura_generica = np.nan
            alerta = pd.NA
            invalid_species: list[str] = []
            has_species_raw = False

            if esquema == "kit_generico":
                kits = sum_kits(row, kit_columns)
                if pd.isna(kits):
                    stats["kits_nulos"] += 1
                    especies_equivalentes = np.nan
                else:
                    if kits == 0:
                        stats["kits_cero"] += 1
                    especies_equivalentes = kits * ESPECIES_POR_KIT
                    cobertura_generica = 100.0 if kits > 0 else 0.0
            else:
                variedades_raw = row[variedades_col] if variedades_col else None
                species, invalid_species, has_species_raw = parse_species(variedades_raw)
                if not has_species_raw:
                    stats["especies_nulas"] += 1
                    cantidad_variedades = np.nan
                else:
                    cantidad_variedades = len(species)
                    if cantidad_variedades == 0:
                        stats["especies_cero"] += 1
                    for canonical, raw_token in species:
                        especies_observadas.append(
                            {
                                "id_solicitud": f"{anio}-{temporada}-{fila_origen:05d}",
                                "anio": anio,
                                "temporada": temporada,
                                "barrio_norm": barrio_norm,
                                "barrio_nombre": barrio_nombre(barrio_norm),
                                "tipo_huerta": tipo_huerta,
                                "tipo_localizacion": tipo_localizacion,
                                "experiencia": experiencia,
                                "superficie": superficie,
                                "destino": destino,
                                "ocupacion": ocupacion,
                                "especie": canonical,
                                "especie_nombre": species_nombre(canonical),
                                "especie_raw": raw_token,
                                "cantidad_sobres": 1.0,
                                "origen": "observada",
                                "metodo": "observada",
                                "fuente_archivo": archivo,
                            }
                        )
                especies_equivalentes = cantidad_variedades
                oferta = OFERTA_CATALOGO.get((anio, temporada), np.nan)
                if not pd.isna(especies_equivalentes) and not pd.isna(oferta) and oferta > 0:
                    cobertura = min(100.0, especies_equivalentes / oferta * 100.0)
                    alerta = 1 if cobertura >= 75.0 else 0

            oferta = OFERTA_CATALOGO.get((anio, temporada), np.nan)
            presupuesto = especies_equivalentes * VALOR_SOBRE if not pd.isna(especies_equivalentes) else np.nan

            flags: list[str] = []
            if esquema == "kit_generico":
                if pd.isna(kits):
                    flags.append("sin_dato_kits")
                if not pd.isna(kits) and kits == 0:
                    flags.append("cero_kits")
                if not pd.isna(kits) and kits > 0:
                    flags.append("demanda_especies_imputada")
            else:
                if not has_species_raw:
                    flags.append("sin_especies")
                elif cantidad_variedades == 0:
                    flags.append("cero_especies")
                if invalid_species:
                    flags.append("tokens_invalidos:" + "|".join(sorted(set(invalid_species))))
            if barrio_norm == "sin_dato":
                flags.append("barrio_sin_dato")
            if tipo_huerta == "no especificado":
                flags.append("tipo_huerta_no_especificado")
            if experiencia == "no especificado":
                flags.append("experiencia_no_especificada")
            if superficie == "no especificado":
                flags.append("superficie_no_especificada")
            if destino == "no especificado":
                flags.append("destino_no_especificado")
            if ocupacion == "no especificado":
                flags.append("ocupacion_no_especificada")
            if localidad_norm not in {"chascomus", "sin_dato"}:
                flags.append("localidad_fuera_chascomus")
            if pd.isna(lat) or pd.isna(lng):
                flags.append("sin_coordenadas")

            referencia = clean_text(row[referencia_col]) if referencia_col else ""

            solicitudes.append(
                {
                    "id_solicitud": f"{anio}-{temporada}-{fila_origen:05d}",
                    "archivo_origen": archivo,
                    "hoja_origen": source["hoja"],
                    "fila_origen": fila_origen,
                    "referencia": referencia,
                    "anio": anio,
                    "temporada": temporada,
                    "esquema_entrega": esquema,
                    "contenido_kit": "generico_10" if esquema == "kit_generico" else "especifico",
                    "target_modelo": "volumen" if esquema == "kit_generico" else "cobertura",
                    "target_cobertura_valido": esquema == "especifico",
                    "barrio_raw": barrio_raw,
                    "barrio_norm": barrio_norm,
                    "barrio_nombre": barrio_nombre(barrio_norm),
                    "localidad_raw": localidad_raw,
                    "localidad_norm": localidad_norm,
                    "lat": lat,
                    "lng": lng,
                    "tipo_localizacion": tipo_localizacion,
                    "tipo_huerta": tipo_huerta,
                    "experiencia": experiencia,
                    "superficie": superficie,
                    "destino": destino,
                    "ocupacion": ocupacion,
                    "anio_vinculacion": anio_vinculacion,
                    "antiguedad_programa": antiguedad_programa,
                    "kits": kits,
                    "cantidad_variedades": cantidad_variedades,
                    "especies_equivalentes": especies_equivalentes,
                    "oferta_catalogo": oferta,
                    "cobertura_catalogo": cobertura,
                    "cobertura_equivalente_generica": cobertura_generica,
                    "alerta_alta_demanda": alerta,
                    "presupuesto_estimado": presupuesto,
                    "flags_calidad": ";".join(flags),
                }
            )

        source_stats.append(stats)

    df_solicitudes = pd.DataFrame(solicitudes)
    df_especies_obs = pd.DataFrame(especies_observadas)

    obs_oi = df_especies_obs[
        df_especies_obs["anio"].isin([2025, 2026])
        & (df_especies_obs["temporada"] == "OI")
    ]
    n_oi = obs_oi["id_solicitud"].nunique()
    canasta = (
        obs_oi.groupby(["especie", "especie_nombre"])
        .size()
        .reset_index(name="n_solicitudes")
        .sort_values(["n_solicitudes", "especie"], ascending=[False, True])
        .reset_index(drop=True)
    )
    canasta["rank"] = canasta.index + 1
    canasta["pct_solicitudes"] = canasta["n_solicitudes"] / n_oi if n_oi else 0.0
    canasta["incluida_en_canasta"] = canasta["rank"] <= 10
    canasta["canasta_version"] = CANASTA_VERSION

    top10 = canasta[canasta["incluida_en_canasta"]].copy()
    filas_imputadas: list[dict] = []
    for _, row in df_solicitudes[
        (df_solicitudes["esquema_entrega"] == "kit_generico")
        & (df_solicitudes["kits"].notna())
        & (df_solicitudes["kits"] > 0)
    ].iterrows():
        for _, species in top10.iterrows():
            filas_imputadas.append(
                {
                    "id_solicitud": row["id_solicitud"],
                    "anio": row["anio"],
                    "temporada": row["temporada"],
                    "barrio_norm": row["barrio_norm"],
                    "barrio_nombre": row["barrio_nombre"],
                    "tipo_huerta": row["tipo_huerta"],
                    "tipo_localizacion": row["tipo_localizacion"],
                    "experiencia": row["experiencia"],
                    "superficie": row["superficie"],
                    "destino": row["destino"],
                    "ocupacion": row["ocupacion"],
                    "especie": species["especie"],
                    "especie_nombre": species["especie_nombre"],
                    "especie_raw": "imputada",
                    "cantidad_sobres": float(row["kits"]),
                    "origen": "imputada",
                    "metodo": "top10_OI_2025_2026",
                    "confianza": "baja",
                    "canasta_version": CANASTA_VERSION,
                    "fuente_archivo": row["archivo_origen"],
                }
            )
    df_especies_imp = pd.DataFrame(filas_imputadas)
    if df_especies_imp.empty:
        df_especies_imp = pd.DataFrame(
            columns=[
                "id_solicitud",
                "anio",
                "temporada",
                "barrio_norm",
                "barrio_nombre",
                "tipo_huerta",
                "tipo_localizacion",
                "experiencia",
                "superficie",
                "destino",
                "ocupacion",
                "especie",
                "especie_nombre",
                "especie_raw",
                "cantidad_sobres",
                "origen",
                "metodo",
                "confianza",
                "canasta_version",
                "fuente_archivo",
            ]
        )
    else:
        df_especies_imp["confianza"] = "baja"
    df_especies_completa = pd.concat(
        [df_especies_obs, df_especies_imp], ignore_index=True, sort=False
    )

    catalogo = pd.DataFrame(
        [
            {
                "anio": source["anio"],
                "temporada": source["temporada"],
                "esquema_entrega": source["esquema"],
                "oferta_catalogo": OFERTA_CATALOGO[(source["anio"], source["temporada"])],
                "especies_por_kit": ESPECIES_POR_KIT if source["esquema"] == "kit_generico" else pd.NA,
                "valor_sobre": VALOR_SOBRE,
                "fuente": source["archivo"],
            }
            for source in SOURCES
        ]
    ).drop_duplicates(subset=["anio", "temporada"]).reset_index(drop=True)

    dim_barrios = (
        df_solicitudes.groupby("barrio_norm")
        .agg(
            barrio_nombre=("barrio_nombre", "first"),
            n_solicitudes=("id_solicitud", "size"),
            n_con_coordenadas=("lat", lambda s: int(s.notna().sum())),
            lat_centroide=("lat", "median"),
            lng_centroide=("lng", "median"),
            anios=("anio", lambda s: ", ".join(str(int(x)) for x in sorted(set(s.dropna())))),
        )
        .reset_index()
        .sort_values(["n_solicitudes", "barrio_nombre"], ascending=[False, True])
        .reset_index(drop=True)
    )

    df_solicitudes["alerta_alta_demanda"] = df_solicitudes["alerta_alta_demanda"].astype("Int64")
    df_solicitudes["kits"] = pd.to_numeric(df_solicitudes["kits"], errors="coerce")
    df_solicitudes["cantidad_variedades"] = pd.to_numeric(df_solicitudes["cantidad_variedades"], errors="coerce")

    df_solicitudes.to_csv(OUT_DIR / "solicitudes_v2.csv", index=False, encoding="utf-8-sig")
    df_especies_obs.to_csv(OUT_DIR / "solicitud_especies.csv", index=False, encoding="utf-8-sig")
    df_especies_imp.to_csv(OUT_DIR / "solicitud_especies_imputada.csv", index=False, encoding="utf-8-sig")
    df_especies_completa.to_csv(OUT_DIR / "solicitud_especies_completa.csv", index=False, encoding="utf-8-sig")
    canasta.to_csv(OUT_DIR / "canasta_oi_referencia.csv", index=False, encoding="utf-8-sig")
    catalogo.to_csv(OUT_DIR / "catalogo_temporada.csv", index=False, encoding="utf-8-sig")
    dim_barrios.to_csv(OUT_DIR / "dim_barrios.csv", index=False, encoding="utf-8-sig")

    write_audit(df_solicitudes, df_especies_obs, df_especies_imp, canasta, dim_barrios, source_stats)
    write_dictionary()
    return df_solicitudes, df_especies_obs, df_especies_imp, canasta, catalogo, dim_barrios


def write_audit(
    df: pd.DataFrame,
    especies_obs: pd.DataFrame,
    especies_imp: pd.DataFrame,
    canasta: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    source_stats: list[dict],
) -> None:
    total = len(df)
    generico = df[df["esquema_entrega"] == "kit_generico"]
    especifico = df[df["esquema_entrega"] == "especifico"]
    n_kits_nulos = int(generico["kits"].isna().sum())
    n_kits_cero = int((generico["kits"] == 0).sum())
    n_especies_nulas = int(especifico["cantidad_variedades"].isna().sum())
    n_especies_cero = int((especifico["cantidad_variedades"] == 0).sum())
    n_barrio_sin_dato = int((df["barrio_norm"] == "sin_dato").sum())
    n_coords = int(df["lat"].notna().sum())
    imputadas_solicitudes = df[
        (df["esquema_entrega"] == "kit_generico")
        & (df["kits"].notna())
        & (df["kits"] > 0)
    ]
    total_sobres_imputados = float((imputadas_solicitudes["kits"] * ESPECIES_POR_KIT).sum())

    lines: list[str] = []
    lines.append("# Auditoría de datos ProHuerta")
    lines.append("")
    lines.append(f"Generado por `preparar_datos.py` el {pd.Timestamp.today().date().isoformat()}.")
    lines.append("")
    lines.append("## 1. Fuentes y filas")
    lines.append("")
    lines.append("| Año | Temporada | Archivo | Hoja | Filas |")
    lines.append("|---:|---|---|---|---:|")
    for s in source_stats:
        lines.append(
            f"| {s['anio']} | {s['temporada']} | {s['archivo']} | {s['hoja']} | {s['filas']} |"
        )
    lines.append("")
    lines.append(f"Total de solicitudes: **{total}**.")
    lines.append(f"Kits genéricos (2022–2023): **{len(generico)}**.")
    lines.append(f"Entregas específicas (2024–2026): **{len(especifico)}**.")
    lines.append("")
    lines.append("## 2. Reconciliación y calidad")
    lines.append("")
    lines.append("| Control | Valor |")
    lines.append("|---|---:|")
    lines.append(f"| Solicitudes totales | {total} |")
    lines.append(f"| Filas de 2022–2023 sin dato de kits | {n_kits_nulos} |")
    lines.append(f"| Filas de 2022–2023 con 0 kits reales | {n_kits_cero} |")
    lines.append(f"| Filas de 2024–2026 sin texto de especies | {n_especies_nulas} |")
    lines.append(f"| Filas de 2024–2026 con 0 especies | {n_especies_cero} |")
    lines.append(f"| Solicitudes con barrio sin dato | {n_barrio_sin_dato} |")
    lines.append(f"| Solicitudes con coordenadas | {n_coords} |")
    lines.append(f"| Solicitudes genéricas con demanda imputada | {len(imputadas_solicitudes)} |")
    lines.append(f"| Sobres equivalentes imputados (kits × 10) | {total_sobres_imputados:.0f} |")
    lines.append("")
    lines.append("El CSV anterior calculaba `Cantidad_Variedades = max(kits, 1) × 7` para 2022–2023. "
                 "Esta versión conserva `kits` como dato original, deja nulos los faltantes y usa "
                 "`especies_equivalentes = kits × 10`, que es la regla acordada para el kit genérico.")
    lines.append("")
    lines.append("## 3. Distribución por esquema")
    lines.append("")
    lines.append("| Esquema | Filas | Cobertura media | Alerta media | Especies equivalentes medias | Presupuesto total |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for esquema, group in df.groupby("esquema_entrega"):
        cob = group["cobertura_catalogo"].mean()
        alerta = group["alerta_alta_demanda"].dropna().mean()
        esp = group["especies_equivalentes"].mean()
        pres = group["presupuesto_estimado"].sum()
        lines.append(
            f"| {esquema} | {len(group)} | {cob:.2f} | {alerta:.3f} | {esp:.2f} | {pres:,.0f} |"
        )
    lines.append("")
    lines.append("## 4. Distribución por año y temporada")
    lines.append("")
    lines.append("| Año | Temporada | Filas | Cobertura media | Alerta media | Especies equivalentes medias |")
    lines.append("|---:|---|---:|---:|---:|---:|")
    for (anio, temporada), group in df.groupby(["anio", "temporada"]):
        cob = group["cobertura_catalogo"].mean()
        alerta = group["alerta_alta_demanda"].dropna().mean()
        esp = group["especies_equivalentes"].mean()
        lines.append(
            f"| {anio} | {temporada} | {len(group)} | {cob:.2f} | {alerta:.3f} | {esp:.2f} |"
        )
    lines.append("")
    lines.append("## 5. Canasta OI de referencia")
    lines.append("")
    lines.append(
        f"Construida con las solicitudes observadas de 2025 OI y 2026 OI "
        f"({int(canasta['n_solicitudes'].max()) if not canasta.empty else 0} solicitudes como máximo por especie)."
    )
    lines.append("")
    lines.append("| Rank | Especie | Solicitudes | % de solicitudes | En canasta top 10 |")
    lines.append("|---:|---|---:|---:|---|")
    for _, row in canasta.head(15).iterrows():
        lines.append(
            f"| {int(row['rank'])} | {row['especie_nombre']} | {int(row['n_solicitudes'])} | "
            f"{row['pct_solicitudes']:.1%} | {'Sí' if row['incluida_en_canasta'] else 'No'} |"
        )
    lines.append("")
    lines.append("## 6. Top de especies observadas")
    lines.append("")
    for temporada, group in especies_obs.groupby("temporada"):
        top = (
            group.groupby("especie_nombre")
            .size()
            .sort_values(ascending=False)
            .head(10)
        )
        lines.append(f"### {temporada}")
        lines.append("")
        lines.append("| Especie | Solicitudes |")
        lines.append("|---|---:|")
        for nombre, cantidad in top.items():
            lines.append(f"| {nombre} | {int(cantidad)} |")
        lines.append("")
    lines.append("## 7. Top de barrios")
    lines.append("")
    lines.append("| Barrio | Solicitudes | Con coordenadas | Años |")
    lines.append("|---|---:|---:|---|")
    for _, row in dim_barrios.head(15).iterrows():
        lines.append(
            f"| {row['barrio_nombre']} | {int(row['n_solicitudes'])} | "
            f"{int(row['n_con_coordenadas'])} | {row['anios']} |"
        )
    lines.append("")
    lines.append("## 8. Flags de calidad")
    lines.append("")
    flag_counts: dict[str, int] = {}
    for value in df["flags_calidad"].fillna(""):
        for flag in str(value).split(";"):
            if flag:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
    lines.append("| Flag | Filas |")
    lines.append("|---|---:|")
    for flag, count in sorted(flag_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {flag} | {count} |")
    lines.append("")
    lines.append("## 9. Supuestos y limitaciones")
    lines.append("")
    lines.append("- `valor_sobre = 500` es constante para todas las temporadas.")
    lines.append("- Cada kit genérico de 2022–2023 contiene 10 especies surtidas.")
    lines.append("- La canasta de 10 especies para 2022–2023 es una **imputación** basada en 2025 OI + 2026 OI; no es un dato observado.")
    lines.append("- 2024 no tiene barrio en el formulario original; 2025 OI tampoco. Esas filas quedan con `barrio_sin_dato`.")
    lines.append("- 2024 no tiene tipo de huerta en el formulario original; queda `no especificado`.")
    lines.append("- Las filas 2022–2023 no tienen experiencia hortícola detallada; solo se marca `primera vez` cuando el formulario lo indica.")
    lines.append("- No se eliminó ninguna fila.")
    lines.append("")
    lines.append("## 10. Archivos generados")
    lines.append("")
    lines.append("| Archivo | Contenido |")
    lines.append("|---|---|")
    lines.append("| `datos/preparados/solicitudes_v2.csv` | Una fila por solicitud, con targets y flags. |")
    lines.append("| `datos/preparados/solicitud_especies.csv` | Especies observadas 2024–2026. |")
    lines.append("| `datos/preparados/solicitud_especies_imputada.csv` | Canasta imputada 2022–2023. |")
    lines.append("| `datos/preparados/solicitud_especies_completa.csv` | Unión de observadas e imputadas. |")
    lines.append("| `datos/preparados/canasta_oi_referencia.csv` | Ranking de especies OI. |")
    lines.append("| `datos/preparados/catalogo_temporada.csv` | Oferta y precio por temporada. |")
    lines.append("| `datos/preparados/dim_barrios.csv` | Barrios, conteos y centroides. |")
    lines.append("| `informe/diccionario_datos.md` | Diccionario y fórmulas. |")
    lines.append("")
    lines.append("## 11. Reproducibilidad")
    lines.append("")
    lines.append("```powershell")
    lines.append("python preparar_datos.py")
    lines.append("```")
    lines.append("")

    (INFO_DIR / "auditoria_datos.md").write_text("\n".join(lines), encoding="utf-8")


def write_dictionary() -> None:
    lines = [
        "# Diccionario de datos",
        "",
        "## `solicitudes_v2.csv`",
        "",
        "| Variable | Tipo | Descripción |",
        "|---|---|---|",
        "| `id_solicitud` | texto | Identificador único: año-temporada-fila. |",
        "| `archivo_origen` | texto | Archivo Excel de origen. |",
        "| `hoja_origen` | texto | Hoja del Excel. |",
        "| `fila_origen` | entero | Fila de datos en el Excel (incluye encabezado). |",
        "| `referencia` | texto | Referencia original cuando existe. |",
        "| `anio` | entero | Año de la campaña. |",
        "| `temporada` | texto | `OI` u `PV`. |",
        "| `esquema_entrega` | texto | `kit_generico` (2022–2023) o `especifico` (2024–2026). |",
        "| `contenido_kit` | texto | `generico_10` o `especifico`. |",
        "| `target_modelo` | texto | `volumen` para kits genéricos; `cobertura` para específicos. |",
        "| `target_cobertura_valido` | booleano | `True` solo en la era específica. |",
        "| `barrio_raw` | texto | Barrio tal como aparece en el formulario. |",
        "| `barrio_norm` | texto | Barrio normalizado para joins y mapa. |",
        "| `barrio_nombre` | texto | Nombre para mostrar. |",
        "| `localidad_raw` | texto | Localidad original. |",
        "| `localidad_norm` | texto | Localidad normalizada. |",
        "| `lat` | decimal | Latitud (solo 2022–2023). |",
        "| `lng` | decimal | Longitud (solo 2022–2023). |",
        "| `tipo_localizacion` | texto | `urbana`, `periurbana`, `rural`, `no especificado`. |",
        "| `tipo_huerta` | texto | `familiar`, `institucional`, `no especificado`. |",
        "| `experiencia` | texto | `primera vez`, `1 a 3 años`, `más de 3 años`, `no especificado`. |",
        "| `superficie` | texto | `hasta 5 m2`, `entre 6 y 20 m2`, `más de 20 m2`, `no especificado`. |",
        "| `destino` | texto | `autoconsumo`, `autoconsumo e intercambio`, `venta / excedentes`, `no especificado`. |",
        "| `ocupacion` | texto | Ocupación agrupada. |",
        "| `anio_vinculacion` | entero | Año de vinculación al programa (2022–2023). |",
        "| `antiguedad_programa` | entero | Años vinculado al programa. |",
        "| `kits` | decimal | Kits entregados en 2022–2023; nulo si no hay dato. |",
        "| `cantidad_variedades` | decimal | Especies distintas solicitadas en 2024–2026. |",
        "| `especies_equivalentes` | decimal | `kits × 10` o `cantidad_variedades`. |",
        "| `oferta_catalogo` | entero | Especies ofrecidas en la temporada. |",
        "| `cobertura_catalogo` | decimal | `min(100, especies_equivalentes / oferta × 100)`, solo era específica. |",
        "| `cobertura_equivalente_generica` | decimal | 100 si el kit genérico tiene al menos 1 kit; 0 si tiene 0. |",
        "| `alerta_alta_demanda` | entero | 1 si cobertura ≥ 75; nulo en era genérica. |",
        "| `presupuesto_estimado` | decimal | `especies_equivalentes × 500`. |",
        "| `flags_calidad` | texto | Alertas de calidad separadas por `;`. |",
        "",
        "## `solicitud_especies.csv`",
        "",
        "Una fila por solicitud y especie observada (2024–2026).",
        "",
        "| Variable | Descripción |",
        "|---|---|",
        "| `id_solicitud` | Solicitud de origen. |",
        "| `anio`, `temporada` | Campaña. |",
        "| `barrio_norm`, `barrio_nombre` | Barrio normalizado y visible. |",
        "| `tipo_huerta`, `tipo_localizacion`, `experiencia`, `superficie`, `destino`, `ocupacion` | Perfil del solicitante. |",
        "| `especie` | Especie canónica. |",
        "| `especie_nombre` | Nombre para mostrar. |",
        "| `especie_raw` | Texto original del formulario. |",
        "| `cantidad_sobres` | Sobres solicitados (1 por especie observada). |",
        "| `origen` | `observada`. |",
        "| `metodo` | `observada`. |",
        "| `fuente_archivo` | Archivo de origen. |",
        "",
        "## `solicitud_especies_imputada.csv`",
        "",
        "Una fila por solicitud genérica y especie de la canasta OI.",
        "",
        "| Variable | Descripción |",
        "|---|---|",
        "| `id_solicitud` | Solicitud genérica de origen. |",
        "| `especie`, `especie_nombre` | Especie de la canasta. |",
        "| `cantidad_sobres` | `kits` de la solicitud. |",
        "| `origen` | `imputada`. |",
        "| `metodo` | `top10_OI_2025_2026`. |",
        "| `confianza` | `baja`. |",
        "| `canasta_version` | Versión de la canasta. |",
        "",
        "## `catalogo_temporada.csv`",
        "",
        "| Variable | Descripción |",
        "|---|---|",
        "| `anio`, `temporada` | Campaña. |",
        "| `esquema_entrega` | `kit_generico` o `especifico`. |",
        "| `oferta_catalogo` | Especies ofrecidas. |",
        "| `especies_por_kit` | 10 para kits genéricos. |",
        "| `valor_sobre` | 500 pesos por sobre. |",
        "| `fuente` | Archivo de origen. |",
        "",
        "## Fórmulas",
        "",
        "- `especies_equivalentes = kits × 10` en 2022–2023.",
        "- `especies_equivalentes = cantidad_variedades` en 2024–2026.",
        "- `presupuesto_estimado = especies_equivalentes × 500`.",
        "- `cobertura_catalogo = min(100, especies_equivalentes / oferta_catalogo × 100)`.",
        "- `alerta_alta_demanda = 1` si `cobertura_catalogo >= 75`, si no `0`.",
        "",
    ]
    (INFO_DIR / "diccionario_datos.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df, especies_obs, especies_imp, canasta, catalogo, dim_barrios = build()
    print("Archivos generados en", OUT_DIR)
    print("Solicitudes:", len(df))
    print("Especies observadas:", len(especies_obs))
    print("Especies imputadas:", len(especies_imp))
    print("Barrios:", len(dim_barrios))
    print("Canasta OI:", len(canasta))
    print("Catálogo:", len(catalogo))
    print(df.groupby(["esquema_entrega", "anio", "temporada"]).size().to_string())


if __name__ == "__main__":
    main()
