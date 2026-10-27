# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

from logica_demanda import (
    MUESTRA_MINIMA_ANIOS,
    MUESTRA_MINIMA_SOLICITUDES,
    calcular_variacion,
    clasificar_muestra,
    evaluar_alerta,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datos" / "preparados"
GEO_PATH_REAL = BASE_DIR / "datos" / "geospatial" / "chascomus_barrios_reales.geojson"
GEO_PATH = BASE_DIR / "datos" / "geospatial" / "chascomus_barrios.geojson"
MODEL_DIR = BASE_DIR / "modelos"
BASEMAP_PATH = BASE_DIR / "static" / "chascomus_basemap.json"

MODEL_REG = joblib.load(MODEL_DIR / "modelo_regresion_dash.joblib")
METADATA = json.loads(
    (MODEL_DIR / "metadata_modelos.json").read_text(encoding="utf-8")
)

FEATURES = METADATA["features"]
COLUMNAS_NUMERICAS = {"anio_idx", "Año", "anio", "oferta_catalogo", "Oferta_Catalogo"}
NUM_FEATURES = [col for col in FEATURES if col in COLUMNAS_NUMERICAS]
CAT_FEATURES = [col for col in FEATURES if col not in COLUMNAS_NUMERICAS]

BASE_ANIO = int(METADATA.get("base_anio", 2024))
PRECIO_SOBRE = float(METADATA.get("precio_fijo_sobre", 500))
MAX_PAQUETES_PRED = float(METADATA.get("limites", {}).get("paquetes_max", 60.0))
MARGEN_SOBREDEMANDA = float(METADATA["alerta"]["margen"])
DIFERENCIA_MINIMA_SOBRES = float(
    METADATA["alerta"].get("diferencia_minima_sobres", 0.0)
)
CRECIMIENTO_POR_TEMPORADA = METADATA["baseline"]["crecimiento_por_temporada"]
CALIBRACION_POR_TEMPORADA = METADATA["regresion"]["calibracion_por_temporada"]
SHRINKAGE_K = 10.0

SOLICITUDES = pd.read_csv(DATA_DIR / "solicitudes_v2.csv")
ESPECIES = pd.read_csv(DATA_DIR / "solicitud_especies.csv")
CATALOGO = pd.read_csv(DATA_DIR / "catalogo_temporada.csv")

ESPECIFICAS = SOLICITUDES[
    (SOLICITUDES["esquema_entrega"] == "especifico")
    & (SOLICITUDES["target_cobertura_valido"].fillna(False).astype(bool))
    & (SOLICITUDES["especies_equivalentes"].notna())
].copy()
ESPECIFICAS["anio_idx"] = ESPECIFICAS["anio"] - BASE_ANIO
ESPECIFICAS_TRAIN = ESPECIFICAS.copy()

TARGET = "especies_equivalentes"
MAX_ANIO_OBSERVADO = int(ESPECIFICAS["anio"].max())
ANIOS_PROYECCION = tuple(range(MAX_ANIO_OBSERVADO + 1, MAX_ANIO_OBSERVADO + 3))


def agregar_escenarios_base(catalogo: pd.DataFrame) -> pd.DataFrame:
    """Extiende el catalogo a 2027-2028 repitiendo la ultima oferta observada."""
    especifico = catalogo[catalogo["esquema_entrega"] == "especifico"]
    ultimos = especifico.sort_values("anio").groupby("temporada").tail(1)
    filas = []
    for _, ultimo in ultimos.iterrows():
        for anio in ANIOS_PROYECCION:
            if anio <= MAX_ANIO_OBSERVADO:
                continue
            existe = catalogo[
                (catalogo["anio"] == anio)
                & (catalogo["temporada"] == ultimo["temporada"])
            ]
            if not existe.empty:
                continue
            filas.append(
                {
                    "anio": anio,
                    "temporada": ultimo["temporada"],
                    "esquema_entrega": "especifico",
                    "oferta_catalogo": int(ultimo["oferta_catalogo"]),
                    "especies_por_kit": pd.NA,
                    "valor_sobre": PRECIO_SOBRE,
                    "fuente": (
                        "Escenario base: ultima oferta observada "
                        f"{int(ultimo['anio'])} {ultimo['temporada']}"
                    ),
                }
            )
    if not filas:
        return catalogo
    return pd.concat([catalogo, pd.DataFrame(filas)], ignore_index=True)


CATALOGO = agregar_escenarios_base(CATALOGO)
GEOJSON_PATH = GEO_PATH_REAL if GEO_PATH_REAL.exists() else GEO_PATH
GEOJSON = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
BASEMAP = (
    json.loads(BASEMAP_PATH.read_text(encoding="utf-8"))
    if BASEMAP_PATH.exists()
    else None
)
BARRIOS_EXTENT_PATH = BASE_DIR / "datos" / "geospatial" / "barrios_extent.json"
BARRIOS_EXTENT = (
    json.loads(BARRIOS_EXTENT_PATH.read_text(encoding="utf-8"))
    if BARRIOS_EXTENT_PATH.exists()
    else {}
)

app = Flask(__name__)


def available_periods() -> list[dict[str, object]]:
    rows = CATALOGO[CATALOGO["esquema_entrega"] == "especifico"]
    return [
        {
            "anio": int(row["anio"]),
            "temporada": row["temporada"],
            "oferta_catalogo": int(row["oferta_catalogo"]),
        }
        for _, row in rows.sort_values(["anio", "temporada"]).iterrows()
    ]


def map_barrios() -> list[dict[str, object]]:
    return [
        {
            "barrio_norm": feature["properties"]["barrio_norm"],
            "barrio_nombre": feature["properties"]["barrio_nombre"],
        }
        for feature in GEOJSON["features"]
    ]


def barrio_feature(barrio_norm: str) -> dict[str, object] | None:
    for feature in GEOJSON["features"]:
        if feature["properties"]["barrio_norm"] == barrio_norm:
            return feature
    return None


def _metric_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(number) else number


def _geo_norms() -> set[str]:
    return {
        str(feature["properties"]["barrio_norm"])
        for feature in GEOJSON["features"]
    }


def _build_app_lookups():
    base = ESPECIFICAS_TRAIN
    global_temp = base.groupby("temporada")[TARGET].mean().to_dict()
    barrio_agg = (
        base.groupby(["barrio_norm", "temporada"])[TARGET]
        .agg(["mean", "count"])
        .reset_index()
    )
    barrio_anios = (
        base.groupby(["barrio_norm", "temporada"])["anio"]
        .nunique()
        .reset_index(name="anios")
    )
    barrio_agg = barrio_agg.merge(barrio_anios, on=["barrio_norm", "temporada"], how="left")
    barrio_lookup = {}
    for _, row in barrio_agg.iterrows():
        barrio_lookup[(row["barrio_norm"], row["temporada"])] = {
            "mean": float(row["mean"]),
            "count": float(row["count"]),
            "anios": float(row["anios"]) if pd.notna(row["anios"]) else 0.0,
        }
    perfil_lookup = {}
    for _, row in base.groupby(
        [
            "barrio_norm",
            "temporada",
            "tipo_huerta",
            "experiencia",
            "superficie",
        ]
    )[TARGET].mean().reset_index(name="perfil_mean").iterrows():
        perfil_lookup[
            (
                row["barrio_norm"],
                row["temporada"],
                row["tipo_huerta"],
                row["experiencia"],
                row["superficie"],
            )
        ] = float(row["perfil_mean"])
    return {"global_temp": global_temp, "barrio_lookup": barrio_lookup, "perfil_lookup": perfil_lookup}


APP_LOOKUPS = _build_app_lookups()


def predict_packets(
    rows: pd.DataFrame, anio: int, temporada: str
) -> np.ndarray:
    """Predice sobres equivalentes mapeando dinámicamente el input a las columnas de scikit-learn."""
    if rows.empty:
        return np.array([], dtype=float)

    oferta_default = 10.0
    match_cat = CATALOGO[(CATALOGO["anio"] == anio) & (CATALOGO["temporada"] == temporada)]
    if not match_cat.empty:
        oferta_default = float(match_cat.iloc[0]["oferta_catalogo"])

    df_predict = pd.DataFrame(index=rows.index)
    
    for col in FEATURES:
        if col in rows.columns:
            df_predict[col] = rows[col]
        elif col in {"Año", "anio"}:
            df_predict[col] = anio
        elif col in {"anio_idx"}:
            df_predict[col] = anio - BASE_ANIO
        elif col in {"Temporada", "temporada"}:
            df_predict[col] = temporada
        elif col in {"Oferta_Catalogo", "oferta_catalogo"}:
            df_predict[col] = rows.get("oferta_catalogo", oferta_default)
        else:
            if "mean" in col or "ratio" in col:
                df_predict[col] = 1.0
            elif "count" in col or "anios" in col:
                df_predict[col] = 1.0
            else:
                df_predict[col] = "no especificado"

    for col in df_predict.columns:
        if df_predict[col].dtype == object or pd.api.types.is_string_dtype(df_predict[col]):
            df_predict[col] = df_predict[col].fillna("no especificado")
        else:
            df_predict[col] = df_predict[col].fillna(0.0)

    raw = np.clip(MODEL_REG.predict(df_predict), 0.0, MAX_PAQUETES_PRED)
    factor = float(CALIBRACION_POR_TEMPORADA.get(temporada, 1.0))
    
    return np.clip(raw * factor, 0.0, MAX_PAQUETES_PRED)


def top_species(ids: set[str], limit: int = 3) -> list[dict[str, object]]:
    if not ids:
        return []
    subset = ESPECIES[ESPECIES["id_solicitud"].isin(ids)]
    if subset.empty:
        return []
    counts = (
        subset.groupby(["especie", "especie_nombre"])
        .size()
        .reset_index(name="solicitudes")
        .sort_values(["solicitudes", "especie_nombre"], ascending=[False, True])
        .head(limit)
    )
    return [
        {
            "especie": row["especie"],
            "nombre": row["especie_nombre"],
            "solicitudes": int(row["solicitudes"]),
        }
        for _, row in counts.iterrows()
    ]


def annual_series(barrio_norm: str, temporada: str) -> pd.DataFrame:
    subset = ESPECIFICAS[
        (ESPECIFICAS["barrio_norm"] == barrio_norm)
        & (ESPECIFICAS["temporada"] == temporada)
    ]
    if subset.empty:
        return pd.DataFrame(
            columns=["solicitudes", "paquetes", "variedades", "presupuesto"]
        )
    return (
        subset.groupby("anio")
        .agg(
            solicitudes=("id_solicitud", "size"),
            paquetes=("especies_equivalentes", "sum"),
            variedades=("cantidad_variedades", "sum"),
            presupuesto=("presupuesto_estimado", "sum"),
        )
        .sort_index()
    )


def history_series(barrio_norm: str, temporada: str) -> list[dict[str, object]]:
    grouped = annual_series(barrio_norm, temporada)
    return [
        {
            "anio": int(anio),
            "solicitudes": int(row["solicitudes"]),
            "paquetes": _metric_or_none(row["paquetes"]),
            "variedades": _metric_or_none(row["variedades"]),
            "presupuesto": _metric_or_none(row["presupuesto"]),
        }
        for anio, row in grouped.iterrows()
    ]


def city_history(
    temporada: str, solo_mapeados: bool = False
) -> list[dict[str, object]]:
    subset = ESPECIFICAS[ESPECIFICAS["temporada"] == temporada]
    if solo_mapeados:
        subset = subset[subset["barrio_norm"].isin(_geo_norms())]
    if subset.empty:
        return []
    grouped = (
        subset.groupby("anio")
        .agg(
            solicitudes=("id_solicitud", "size"),
            paquetes=("especies_equivalentes", "sum"),
            variedades=("cantidad_variedades", "sum"),
            presupuesto=("presupuesto_estimado", "sum"),
        )
        .reset_index()
        .sort_values("anio")
    )
    return [
        {
            "anio": int(row["anio"]),
            "solicitudes": int(row["solicitudes"]),
            "paquetes": _metric_or_none(row["paquetes"]),
            "variedades": _metric_or_none(row["variedades"]),
            "presupuesto": _metric_or_none(row["presupuesto"]),
        }
        for _, row in grouped.iterrows()
    ]


@lru_cache(maxsize=512)
def barrio_scenario(barrio_norm: str, temporada: str) -> dict[str, object]:
    grouped = annual_series(barrio_norm, temporada)
    if grouped.empty:
        return {
            "barrio_norm": barrio_norm,
            "temporada": temporada,
            "sin_datos": True,
            "estado_alerta": "sin_datos",
            "motivo_alerta": (
                "Sin solicitudes historicas con barrio para esta temporada."
            ),
            "muestra_limitada": False,
            "motivo_muestra": None,
            "n_solicitudes_historicas": 0,
            "n_anios_historicos": 0,
            "anio_referencia": None,
            "escenarios": {},
            "serie": [],
            "top_especies": [],
        }

    rows = ESPECIFICAS[
        (ESPECIFICAS["barrio_norm"] == barrio_norm)
        & (ESPECIFICAS["temporada"] == temporada)
    ]
    ultimo_anio = int(grouped.index.max())
    ultimas_solicitudes = float(grouped.loc[ultimo_anio, "solicitudes"])
    media_solicitudes = float(grouped["solicitudes"].mean())
    media_paquetes = float(grouped["paquetes"].mean())
    paquetes_ultimo_anio = float(grouped.loc[ultimo_anio, "paquetes"])
    crecimiento = float(CRECIMIENTO_POR_TEMPORADA.get(temporada, 0.0))
    muestra = clasificar_muestra(
        grouped["solicitudes"].sum(), len(grouped)
    )
    if len(grouped) < 2 or muestra["n_solicitudes_historicas"] < 10:
        muestra["muestra_limitada"] = True
        if not muestra["motivo_muestra"]:
            muestra["motivo_muestra"] = (
                "Muestra historica limitada: "
                f"{muestra['n_solicitudes_historicas']} solicitudes en {len(grouped)} anio(s); "
                f"se requieren al menos {10} solicitudes y {2} anios para una lectura mas robusta."
            )

    baseline_por_solicitud = (
        media_paquetes / media_solicitudes if media_solicitudes > 0 else 0.0
    )
    predicciones_historicas: list[float] = []
    for anio in grouped.index:
        predicciones_historicas.extend(
            predict_packets(
                rows[rows["anio"] == anio], int(anio), temporada
            ).tolist()
        )
    modelo_historico_medio = (
        float(np.mean(predicciones_historicas))
        if predicciones_historicas
        else 0.0
    )
    factor_barrio = (
        baseline_por_solicitud / modelo_historico_medio
        if modelo_historico_medio > 0
        else 1.0
    )
    # shrinkage towards global factor
    try:
        grows = annual_series(None, temporada) if False else None
    except Exception:
        grows = None
    # compute global
    gsub = ESPECIFICAS[ESPECIFICAS["temporada"] == temporada]
    if not gsub.empty:
        ggroup = gsub.groupby("anio").agg(sol=("id_solicitud", "size"), paq=("especies_equivalentes", "sum"))
        gmedia_sol = float(ggroup["sol"].mean()) if not ggroup.empty else media_solicitudes
        gmedia_paq = float(ggroup["paq"].mean()) if not ggroup.empty else media_paquetes
        gpred_hist = []
        for anio in ggroup.index:
            gpred_hist.extend(predict_packets(gsub[gsub["anio"] == anio], int(anio), temporada).tolist())
        gmodelo_medio = float(np.mean(gpred_hist)) if gpred_hist else modelo_historico_medio
        factor_global = (gmedia_paq / gmedia_sol / gmodelo_medio) if gmodelo_medio > 0 and gmedia_sol > 0 else 1.0
    else:
        factor_global = 1.0
    n_b = float(muestra["n_solicitudes_historicas"]) or 0.0
    w = n_b / (n_b + SHRINKAGE_K) if (n_b + SHRINKAGE_K) > 0 else 0.0
    factor_barrio = w * factor_barrio + (1.0 - w) * factor_global

    serie = history_series(barrio_norm, temporada)
    escenarios: dict[int, dict[str, object]] = {}
    for anio in ANIOS_PROYECCION:
        factor_crecimiento = (1.0 + crecimiento) ** (anio - ultimo_anio)
        solicitudes_esperadas = ultimas_solicitudes * factor_crecimiento
        esperado = media_paquetes * factor_crecimiento
        predicciones_futuras = predict_packets(rows, anio, temporada)
        modelo_futuro_medio = (
            float(predicciones_futuras.mean())
            if len(predicciones_futuras)
            else 0.0
        )
        predicho = max(
            0.0,
            solicitudes_esperadas * modelo_futuro_medio * factor_barrio,
        )
        evaluacion = evaluar_alerta(
            predicho,
            esperado,
            MARGEN_SOBREDEMANDA,
            DIFERENCIA_MINIMA_SOBRES,
            bool(muestra["muestra_limitada"]),
        )
        escenarios[anio] = {
            "anio": anio,
            "solicitudes": solicitudes_esperadas,
            "solicitudes_esperadas": solicitudes_esperadas,
            "esperado_paquetes": esperado,
            "predicho_paquetes": predicho,
            "esperado_presupuesto": esperado * PRECIO_SOBRE,
            "predicho_presupuesto": predicho * PRECIO_SOBRE,
            "diferencia_paquetes": evaluacion["diferencia_absoluta"],
            "ratio_predicho_esperado": (
                predicho / esperado if esperado > 0 else None
            ),
            "variacion_pct": evaluacion["variacion_pct"],
            "alerta_sobredemanda": (
                1 if evaluacion["alerta"] else 0
            ),
            "estado_alerta": evaluacion["estado"],
            "motivo_alerta": evaluacion["motivo"],
            "muestra_limitada": evaluacion["muestra_limitada"],
            "motivo_muestra": muestra["motivo_muestra"],
        }

    return {
        "barrio_norm": barrio_norm,
        "barrio_nombre": str(rows.iloc[0]["barrio_nombre"]),
        "temporada": temporada,
        "sin_datos": False,
        "anio_referencia": ultimo_anio,
        "ultimo_anio": ultimo_anio,
        "estado_alerta": None,
        "motivo_alerta": None,
        "muestra_limitada": muestra["muestra_limitada"],
        "motivo_muestra": muestra["motivo_muestra"],
        "n_solicitudes_historicas": muestra["n_solicitudes_historicas"],
        "n_anios_historicos": muestra["n_anios_historicos"],
        "anios_historicos": [int(anio) for anio in grouped.index],
        "solicitudes_historicas": ultimas_solicitudes,
        "media_solicitudes": media_solicitudes,
        "media_historica_paquetes": media_paquetes,
        "paquetes_ultimo_anio": paquetes_ultimo_anio,
        "crecimiento_anual": crecimiento,
        "factor_barrio": factor_barrio,
        "escenarios": escenarios,
        "serie": serie,
        "top_especies": top_species(set(rows["id_solicitud"])),
    }


def _empty_summary(
    barrio_norm: str, anio: int, temporada: str, mensaje: str
) -> dict[str, object]:
    return {
        "barrio_norm": barrio_norm,
        "barrio_nombre": barrio_norm.replace("_", " ").title(),
        "anio": anio,
        "temporada": temporada,
        "es_proyeccion": anio > MAX_ANIO_OBSERVADO,
        "sin_datos": True,
        "mensaje": mensaje,
        "anio_referencia": None,
        "ultimo_anio": None,
        "estado_alerta": "sin_datos",
        "motivo_alerta": mensaje,
        "muestra_limitada": False,
        "motivo_muestra": None,
        "n_solicitudes_historicas": 0,
        "n_anios_historicos": 0,
        "solicitudes": None,
        "solicitudes_historicas": None,
        "solicitudes_esperadas": None,
        "esperado_paquetes": None,
        "predicho_paquetes": None,
        "diferencia_paquetes": None,
        "esperado_presupuesto": None,
        "predicho_presupuesto": None,
        "presupuesto": None,
        "ratio_predicho_esperado": None,
        "variacion_pct": None,
        "alerta_sobredemanda": None,
        "alertas_estimadas": None,
        "alertas": None,
        "solicitudes_en_riesgo": None,
        "tasa_alerta": None,
        "alerta_barrio": None,
        "probabilidad_alerta_media": None,
        "cobertura_estimada": None,
        "crecimiento_anual": None,
        "historico_paquetes": None,
        "proyectado_paquetes": None,
        "historico_presupuesto": None,
        "proyectado_presupuesto": None,
        "top_especies": [],
        "serie": [],
        "escenarios": {},
    }


@lru_cache(maxsize=4096)
def barrio_summary(
    barrio_norm: str, anio: int, temporada: str
) -> dict[str, object]:
    extent = BARRIOS_EXTENT.get(barrio_norm, {}) or {}
    scenario = barrio_scenario(barrio_norm, temporada)
    if scenario["sin_datos"]:
        res = _empty_summary(
            barrio_norm,
            anio,
            temporada,
            "Sin solicitudes historicas con barrio para esta temporada.",
        )
        res["superficie_ha"] = extent.get("area_ha")
        res["superficie_km2"] = extent.get("area_km2")
        res["superficie_m2"] = extent.get("area_m2")
        res["radios_censales"] = extent.get("radios_count")
        return res

    if anio in scenario["escenarios"]:
        item = scenario["escenarios"][anio]
        esperado = _metric_or_none(item["esperado_paquetes"])
        predicho = _metric_or_none(item["predicho_paquetes"])
        presupuesto = _metric_or_none(item["predicho_presupuesto"])
        alerta = int(item.get("alerta_sobredemanda") or 0)
        return {
            "barrio_norm": scenario["barrio_norm"],
            "barrio_nombre": scenario["barrio_nombre"],
            "anio": anio,
            "temporada": temporada,
            "es_proyeccion": True,
            "sin_datos": False,
            "anio_referencia": scenario["anio_referencia"],
            "ultimo_anio": scenario["ultimo_anio"],
            "anios_historicos": scenario["anios_historicos"],
            "estado_alerta": item.get("estado_alerta"),
            "motivo_alerta": item.get("motivo_alerta"),
            "muestra_limitada": bool(item.get("muestra_limitada")),
            "motivo_muestra": item.get("motivo_muestra"),
            "n_solicitudes_historicas": scenario[
                "n_solicitudes_historicas"
            ],
            "n_anios_historicos": scenario["n_anios_historicos"],
            "solicitudes": item["solicitudes_esperadas"],
            "solicitudes_historicas": scenario["solicitudes_historicas"],
            "solicitudes_esperadas": item["solicitudes_esperadas"],
            "esperado_paquetes": esperado,
            "predicho_paquetes": predicho,
            "esperado_presupuesto": _metric_or_none(
                item["esperado_presupuesto"]
            ),
            "predicho_presupuesto": presupuesto,
            "presupuesto": presupuesto,
            "diferencia_paquetes": _metric_or_none(
                item["diferencia_paquetes"]
            ),
            "ratio_predicho_esperado": item["ratio_predicho_esperado"],
            "variacion_pct": item["variacion_pct"],
            "alerta_sobredemanda": alerta,
            "alertas_estimadas": alerta,
            "alertas": alerta,
            "solicitudes_en_riesgo": alerta,
            "tasa_alerta": float(alerta),
            "alerta_barrio": alerta,
            "probabilidad_alerta_media": 0.0,
            "cobertura_estimada": 0.0,
            "crecimiento_anual": scenario["crecimiento_anual"],
            "media_historica_paquetes": scenario["media_historica_paquetes"],
            "paquetes_ultimo_anio": scenario["paquetes_ultimo_anio"],
            "media_solicitudes": scenario["media_solicitudes"],
            "top_especies": scenario["top_especies"],
            "serie": scenario["serie"],
            "escenarios": scenario["escenarios"],
            "historico_paquetes": esperado,
            "proyectado_paquetes": predicho,
            "historico_presupuesto": item["esperado_presupuesto"],
            "proyectado_presupuesto": presupuesto,
            "superficie_ha": extent.get("area_ha"),
            "superficie_km2": extent.get("area_km2"),
            "superficie_m2": extent.get("area_m2"),
            "radios_censales": extent.get("radios_count"),
        }

    record = next(
        (item for item in scenario["serie"] if item["anio"] == anio), None
    )
    if record is None:
        res = _empty_summary(
            barrio_norm,
            anio,
            temporada,
            "No hay solicitudes observadas para el anio seleccionado.",
        )
        res["anio_referencia"] = scenario["anio_referencia"]
        res["ultimo_anio"] = scenario["ultimo_anio"]
        res["anios_historicos"] = scenario["anios_historicos"]
        res["n_solicitudes_historicas"] = scenario[
            "n_solicitudes_historicas"
        ]
        res["n_anios_historicos"] = scenario["n_anios_historicos"]
        res["muestra_limitada"] = scenario["muestra_limitada"]
        res["motivo_muestra"] = scenario["motivo_muestra"]
        res["superficie_ha"] = extent.get("area_ha")
        res["superficie_km2"] = extent.get("area_km2")
        res["superficie_m2"] = extent.get("area_m2")
        res["radios_censales"] = extent.get("radios_count")
        return res

    paquetes = _metric_or_none(record["paquetes"])
    solicitudes = int(record["solicitudes"])
    presupuesto = _metric_or_none(record["presupuesto"])
    return {
        "barrio_norm": scenario["barrio_norm"],
        "barrio_nombre": scenario["barrio_nombre"],
        "anio": anio,
        "temporada": temporada,
        "es_proyeccion": False,
        "sin_datos": False,
        "anio_referencia": anio,
        "ultimo_anio": scenario["ultimo_anio"],
        "anios_historicos": scenario["anios_historicos"],
        "estado_alerta": "observado",
        "motivo_alerta": (
            "Dato observado; no se compara contra una proyeccion."
        ),
        "muestra_limitada": scenario["muestra_limitada"],
        "motivo_muestra": scenario["motivo_muestra"],
        "n_solicitudes_historicas": scenario["n_solicitudes_historicas"],
        "n_anios_historicos": scenario["n_anios_historicos"],
        "solicitudes": solicitudes,
        "solicitudes_historicas": solicitudes,
        "solicitudes_esperadas": None,
        "esperado_paquetes": paquetes,
        "predicho_paquetes": None,
        "esperado_presupuesto": presupuesto,
        "predicho_presupuesto": None,
        "presupuesto": None,
        "diferencia_paquetes": None,
        "ratio_predicho_esperado": None,
        "variacion_pct": None,
        "alerta_sobredemanda": None,
        "alertas_estimadas": None,
        "alertas": None,
        "solicitudes_en_riesgo": None,
        "tasa_alerta": None,
        "alerta_barrio": None,
        "probabilidad_alerta_media": None,
        "cobertura_estimada": None,
        "crecimiento_anual": scenario["crecimiento_anual"],
        "media_historica_paquetes": scenario["media_historica_paquetes"],
        "paquetes_ultimo_anio": scenario["paquetes_ultimo_anio"],
        "media_solicitudes": scenario["media_solicitudes"],
        "top_especies": scenario["top_especies"],
        "serie": scenario["serie"],
        "escenarios": scenario["escenarios"],
        "historico_paquetes": paquetes,
        "proyectado_paquetes": None,
        "historico_presupuesto": presupuesto,
        "proyectado_presupuesto": None,
        "superficie_ha": extent.get("area_ha"),
        "superficie_km2": extent.get("area_km2"),
        "superficie_m2": extent.get("area_m2"),
        "radios_censales": extent.get("radios_count"),
    }


def _sumar(items: list[dict[str, object]], key: str) -> float:
    total = 0.0
    for item in items:
        value = _metric_or_none(item.get(key))
        if value is not None:
            total += value
    return total


def resumen_territorial(
    barrios: list[dict[str, object]], anio: int, temporada: str
) -> dict[str, object]:
    """Totales del ambito que efectivamente puede proyectarse por barrio."""
    con_datos = [item for item in barrios if not item.get("sin_datos")]
    es_proyeccion = anio > MAX_ANIO_OBSERVADO
    referencia = _sumar(con_datos, "esperado_paquetes")
    proyectado = (
        _sumar(con_datos, "predicho_paquetes") if es_proyeccion else None
    )
    diferencia = (
        proyectado - referencia
        if proyectado is not None and referencia > 0
        else None
    )
    variacion = (
        calcular_variacion(proyectado, referencia)
        if proyectado is not None
        else None
    )
    anios_referencia = [
        int(item["anio_referencia"])
        for item in con_datos
        if item.get("anio_referencia") is not None
    ]
    return {
        "ambito": "territorial_mapeado",
        "anio": anio,
        "temporada": temporada,
        "es_proyeccion": es_proyeccion,
        "unidad": "sobres equivalentes",
        "incluye_sin_barrio": False,
        "barrios_geograficos": len(barrios),
        "barrios_con_datos": len(con_datos),
        "barrios_sin_datos": len(barrios) - len(con_datos),
        "barrios_alerta": sum(
            1 for item in con_datos if item.get("alerta_sobredemanda")
        ),
        "barrios_muestra_limitada": sum(
            1 for item in con_datos if item.get("muestra_limitada")
        ),
        "demanda_referencia_paquetes": round(referencia, 3),
        "demanda_proyectada_paquetes": (
            round(proyectado, 3) if proyectado is not None else None
        ),
        "diferencia_paquetes": (
            round(diferencia, 3) if diferencia is not None else None
        ),
        "variacion_pct": (
            round(variacion, 2) if variacion is not None else None
        ),
        "presupuesto_referencia": round(referencia * PRECIO_SOBRE, 2),
        "presupuesto_proyectado": (
            round(proyectado * PRECIO_SOBRE, 2)
            if proyectado is not None
            else None
        ),
        "solicitudes_esperadas": int(
            round(_sumar(con_datos, "solicitudes_esperadas"))
        ),
        "anio_referencia": (
            max(anios_referencia) if anios_referencia else None
        ),
        "nota": (
            "Totales calculados solo con barrios mapeados con datos. "
            "No incluyen registros sin barrio ni barrios fuera de la "
            "dimension geografica."
        ),
    }


def resumen_municipal_observado(temporada: str) -> dict[str, object]:
    """Particiona el total municipal sin eliminar registros no mapeados."""
    subset = ESPECIFICAS[ESPECIFICAS["temporada"] == temporada]
    if subset.empty:
        return {
            "ambito": "municipal_completo_observado",
            "anio": None,
            "temporada": temporada,
            "unidad": "sobres equivalentes",
            "incluye_sin_barrio": True,
            "total": {"paquetes": None, "solicitudes": 0, "barrios": 0},
            "mapeados": {"paquetes": None, "solicitudes": 0, "barrios": 0},
            "sin_barrio": {"paquetes": None, "solicitudes": 0, "barrios": 0},
            "barrio_no_mapeado": {
                "paquetes": None,
                "solicitudes": 0,
                "barrios": 0,
            },
            "cobertura_mapeada_pct": None,
            "nota": "Sin registros para la temporada.",
        }

    anio = int(subset["anio"].max())
    subset = subset[subset["anio"] == anio]
    geo = _geo_norms()
    mapped = subset[subset["barrio_norm"].isin(geo)]
    sin_barrio = subset[subset["barrio_norm"] == "sin_dato"]
    no_mapeado = subset[
        (~subset["barrio_norm"].isin(geo))
        & (subset["barrio_norm"] != "sin_dato")
    ]

    def agregar(frame: pd.DataFrame) -> dict[str, object]:
        if frame.empty:
            return {"paquetes": None, "solicitudes": 0, "barrios": 0}
        return {
            "paquetes": round(
                float(frame["especies_equivalentes"].sum()), 3
            ),
            "solicitudes": int(len(frame)),
            "barrios": int(frame["barrio_norm"].nunique()),
        }

    total = agregar(subset)
    mapeados = agregar(mapped)
    total_paquetes = _metric_or_none(total["paquetes"]) or 0.0
    mapeados_paquetes = _metric_or_none(mapeados["paquetes"]) or 0.0
    cobertura = (
        mapeados_paquetes / total_paquetes * 100.0
        if total_paquetes > 0
        else None
    )
    return {
        "ambito": "municipal_completo_observado",
        "anio": anio,
        "temporada": temporada,
        "unidad": "sobres equivalentes",
        "incluye_sin_barrio": True,
        "total": total,
        "mapeados": mapeados,
        "sin_barrio": agregar(sin_barrio),
        "barrio_no_mapeado": agregar(no_mapeado),
        "cobertura_mapeada_pct": (
            round(cobertura, 2) if cobertura is not None else None
        ),
        "nota": (
            "Total municipal observado, incluidos registros sin barrio y "
            "barrios fuera de la dimension geografica. La proyeccion futura "
            "solo cubre los barrios mapeados."
        ),
    }


@lru_cache(maxsize=8)
def escenarios_ciudad(temporada: str) -> list[dict[str, object]]:
    result = []
    for anio in ANIOS_PROYECCION:
        barrios = [
            barrio_summary(
                str(feature["properties"]["barrio_norm"]),
                anio,
                temporada,
            )
            for feature in GEOJSON["features"]
        ]
        result.append(resumen_territorial(barrios, anio, temporada))
    return result


def clean_number(value: object) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    return value


@app.route("/")
def index():
    return render_template(
        "index.html",
        periods=available_periods(),
        barrios=map_barrios(),
        threshold=0.0,
        model_meta=METADATA,
        basemap=BASEMAP,
        max_observed_year=MAX_ANIO_OBSERVADO,
    )


@app.route("/api/filtros")
def api_filtros():
    return jsonify(
        {
            "periodos": available_periods(),
            "barrios": map_barrios(),
            "margen_sobredemanda": MARGEN_SOBREDEMANDA,
            "diferencia_minima_sobres": DIFERENCIA_MINIMA_SOBRES,
            "precio_sobre": PRECIO_SOBRE,
        }
    )


@app.route("/api/mapa_completo")
def api_mapa_completo():
    try:
        anio = int(request.args.get("anio", MAX_ANIO_OBSERVADO))
    except ValueError:
        return jsonify({"error": "Anio invalido"}), 400
    temporada = request.args.get("temporada", "PV").upper()
    if temporada not in {"OI", "PV"}:
        return jsonify({"error": "Temporada invalida"}), 400

    barrios = []
    for feature in GEOJSON["features"]:
        props = feature["properties"]
        summary = barrio_summary(props["barrio_norm"], anio, temporada)
        barrios.append(
            {
                "barrio_norm": props["barrio_norm"],
                "barrio_nombre": props["barrio_nombre"],
                "lat": props["lat_centroide"],
                "lng": props["lng_centroide"],
                "radio_m": props.get("radio_m"),
                "geometry": feature["geometry"],
                "solicitudes": summary.get("solicitudes"),
                "solicitudes_historicas": summary.get(
                    "solicitudes_historicas"
                ),
                "solicitudes_esperadas": summary.get(
                    "solicitudes_esperadas"
                ),
                "esperado_paquetes": summary.get("esperado_paquetes"),
                "predicho_paquetes": summary.get("predicho_paquetes"),
                "esperado_presupuesto": summary.get(
                    "esperado_presupuesto"
                ),
                "predicho_presupuesto": summary.get(
                    "predicho_presupuesto"
                ),
                "diferencia_paquetes": summary.get("diferencia_paquetes"),
                "historico_paquetes": summary.get("historico_paquetes"),
                "proyectado_paquetes": summary.get(
                    "proyectado_paquetes"
                ),
                "presupuesto": summary.get("presupuesto"),
                "variacion_pct": summary.get("variacion_pct"),
                "ratio_predicho_esperado": summary.get(
                    "ratio_predicho_esperado"
                ),
                "alerta_sobredemanda": summary.get(
                    "alerta_sobredemanda"
                ),
                "estado_alerta": summary.get("estado_alerta"),
                "motivo_alerta": summary.get("motivo_alerta"),
                "muestra_limitada": summary.get(
                    "muestra_limitada", False
                ),
                "motivo_muestra": summary.get("motivo_muestra"),
                "n_solicitudes_historicas": summary.get(
                    "n_solicitudes_historicas", 0
                ),
                "n_anios_historicos": summary.get(
                    "n_anios_historicos", 0
                ),
                "alertas": summary.get("alerta_sobredemanda"),
                "alertas_estimadas": summary.get(
                    "alerta_sobredemanda"
                ),
                "solicitudes_en_riesgo": summary.get(
                    "solicitudes_en_riesgo"
                ),
                "tasa_alerta": summary.get("tasa_alerta"),
                "alerta_barrio": summary.get("alerta_barrio"),
                "cobertura_estimada": summary.get(
                    "cobertura_estimada"
                ),
                "crecimiento_anual": summary.get("crecimiento_anual"),
                "media_historica_paquetes": summary.get(
                    "media_historica_paquetes"
                ),
                "anio_referencia": summary.get("anio_referencia"),
                "ultimo_anio": summary.get("ultimo_anio"),
                "anios_historicos": summary.get("anios_historicos", []),
                "es_proyeccion": summary.get("es_proyeccion", False),
                "top_especies": summary.get("top_especies", []),
                "sin_datos": summary.get("sin_datos", True),
            }
        )

    resumen_territorial_actual = resumen_territorial(
        barrios, anio, temporada
    )
    resumen_municipal = resumen_municipal_observado(temporada)
    resumen_ciudad = {
        **resumen_territorial_actual,
        "esperado_paquetes": resumen_territorial_actual[
            "demanda_referencia_paquetes"
        ],
        "predicho_paquetes": resumen_territorial_actual[
            "demanda_proyectada_paquetes"
        ],
        "esperado_presupuesto": resumen_territorial_actual[
            "presupuesto_referencia"
        ],
        "predicho_presupuesto": resumen_territorial_actual[
            "presupuesto_proyectado"
        ],
        "historico_paquetes": resumen_territorial_actual[
            "demanda_referencia_paquetes"
        ],
        "proyectado_paquetes": resumen_territorial_actual[
            "demanda_proyectada_paquetes"
        ],
        "presupuesto": resumen_territorial_actual[
            "presupuesto_proyectado"
        ],
        "solicitudes": resumen_territorial_actual[
            "solicitudes_esperadas"
        ],
        "alertas_totales": resumen_territorial_actual["barrios_alerta"],
        "barrios_total": resumen_territorial_actual[
            "barrios_con_datos"
        ],
    }
    return jsonify(
        {
            "anio": anio,
            "temporada": temporada,
            "es_proyeccion": anio > MAX_ANIO_OBSERVADO,
            "target": "especies_equivalentes",
            "precio_sobre": PRECIO_SOBRE,
            "margen_sobredemanda": MARGEN_SOBREDEMANDA,
            "diferencia_minima_sobres": DIFERENCIA_MINIMA_SOBRES,
            "barrios": barrios,
            "serie_ciudad": city_history(temporada),
            "serie_ciudad_territorial": city_history(
                temporada, solo_mapeados=True
            ),
            "escenarios_ciudad": escenarios_ciudad(temporada),
            "resumen_ciudad": resumen_ciudad,
            "resumen_territorial": resumen_territorial_actual,
            "resumen_municipal": resumen_municipal,
            "muestra_umbrales": {
                "solicitudes_minimas": MUESTRA_MINIMA_SOLICITUDES,
                "anios_minimos": MUESTRA_MINIMA_ANIOS,
            },
            "advertencias": [
                (
                    "Los polígonos se muestran con geometría real cuando está disponible."
                ),
                (
                    "La proyeccion cubre solo barrios mapeados con datos; "
                    "el total municipal observado incluye registros sin "
                    "barrio y barrios fuera de la dimension geografica."
                ),
            ],
        }
    )


@app.route("/api/consulta_especifica")
def api_consulta_especifica():
    barrio_norm = request.args.get("barrio", "").strip()
    try:
        anio = int(request.args.get("anio", MAX_ANIO_OBSERVADO))
    except ValueError:
        return jsonify({"error": "Anio invalido"}), 400
    temporada = request.args.get("temporada", "PV").upper()
    if not barrio_norm:
        return jsonify({"error": "Falta el barrio"}), 400
    if temporada not in {"OI", "PV"}:
        return jsonify({"error": "Temporada invalida"}), 400

    summary = dict(barrio_summary(barrio_norm, anio, temporada))
    feature = barrio_feature(barrio_norm)
    summary["geometria"] = feature["geometry"] if feature else None
    summary["centroide"] = (
        {
            "lat": feature["properties"]["lat_centroide"],
            "lng": feature["properties"]["lng_centroide"],
        }
        if feature
        else None
    )
    return jsonify(summary)


@app.route("/api/prediccion", methods=["POST"])
def api_prediccion():
    payload = request.get_json(silent=True) or request.form.to_dict()
    try:
        anio = int(payload["anio"])
        temporada = str(payload["temporada"]).upper()
        if temporada not in {"OI", "PV"}:
            raise ValueError("temporada invalida")
        row = {
            "temporada": temporada,
            "tipo_huerta": payload.get("tipo_huerta", "familiar"),
            "tipo_localizacion": payload.get(
                "tipo_localizacion", "urbana"
            ),
            "experiencia": payload.get("experiencia", "primera vez"),
            "superficie": payload.get("superficie", "hasta 5 m2"),
            "destino": payload.get("destino", "autoconsumo"),
            "ocupacion": payload.get("ocupacion", "empleado/a"),
        }
    except (KeyError, ValueError):
        return jsonify({"error": "Datos incompletos o invalidos"}), 400

    paquetes = float(predict_packets(pd.DataFrame([row]), anio, temporada)[0])
    respuesta = {
        "anio": anio,
        "temporada": temporada,
        "target": "especies_equivalentes",
        "precio_sobre": PRECIO_SOBRE,
        "sobres_estimados": round(paquetes, 2),
        "variedades_estimadas": round(paquetes, 2),
        "presupuesto_estimado": round(paquetes * PRECIO_SOBRE, 2),
        "alerta_sobredemanda": None,
        "esperado_paquetes": None,
        "predicho_paquetes": round(paquetes, 2),
        "variacion_pct": None,
    }

    barrio_norm = str(payload.get("barrio", "")).strip()
    if barrio_norm:
        summary = barrio_summary(barrio_norm, anio, temporada)
        if not summary["sin_datos"]:
            respuesta.update(
                {
                    "barrio_norm": barrio_norm,
                    "esperado_barrio_paquetes": summary[
                        "esperado_paquetes"
                    ],
                    "predicho_barrio_paquetes": summary[
                        "predicho_paquetes"
                    ],
                    "variacion_barrio_pct": summary["variacion_pct"],
                    "alerta_sobredemanda": summary[
                        "alerta_sobredemanda"
                    ],
                }
            )
    return jsonify(respuesta)


@app.route("/api/health")
def api_health():
    return jsonify(
        {
            "ok": True,
            "model_version": METADATA["version"],
            "target": "especies_equivalentes",
            "precio_sobre": PRECIO_SOBRE,
            "filas": int(len(SOLICITUDES)),
            "filas_modeladas": int(len(ESPECIFICAS)),
            "barrios_geo": len(GEOJSON["features"]),
            "anios_proyeccion": list(ANIOS_PROYECCION),
            "margen_sobredemanda": MARGEN_SOBREDEMANDA,
            "diferencia_minima_sobres": DIFERENCIA_MINIMA_SOBRES,
            "muestra_umbrales": {
                "solicitudes_minimas": MUESTRA_MINIMA_SOLICITUDES,
                "anios_minimos": MUESTRA_MINIMA_ANIOS,
            },
        }
    )


if __name__ == "__main__":
    app.run(debug=True) 