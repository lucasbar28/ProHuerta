# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datos" / "preparados"
MODEL_DIR = BASE_DIR / "modelos"

# Carga segura del modelo de lluvias si se encuentra disponible
MODELO_LLUVIAS_PATH = MODEL_DIR / "modelo_lluvias.joblib"
modelo_lluvias = joblib.load(MODELO_LLUVIAS_PATH) if MODELO_LLUVIAS_PATH.exists() else None

def analizar_impacto_lluvias(df: pd.DataFrame) -> dict:
    """
    Analiza estadísticamente el comportamiento de la cobertura y la demanda 
    agrupado por los niveles históricos de precipitaciones.
    """
    if df.empty or "Precipitaciones_Hist_mm" not in df.columns:
        return {"error": "Dataset vacío o sin columna de precipitaciones."}

    resumen = df.groupby(["Temporada", "Precipitaciones_Hist_mm"]).agg(
        total_registros=("Año", "count"),
        promedio_cobertura=("Cobertura_Catalogo", "mean"),
        tasa_alerta_demanda=("Alerta_Alta_Demanda", "mean")
    ).reset_index().to_dict(orient="records")

    return {
        "estado": "ok",
        "analisis_precipitaciones": resumen
    }

def estimar_cobertura_clima(precipitaciones_mm: float, oferta_catalogo: float) -> float:
    """
    Utiliza el modelo de regresión entrenado para estimar la cobertura 
    esperada del catálogo en función de los milímetros de lluvia y la oferta.
    """
    if modelo_lluvias is not None:
        X_input = pd.DataFrame([[precipitaciones_mm, oferta_catalogo]], columns=["Precipitaciones_Hist_mm", "Oferta_Catalogo"])
        pred = float(modelo_lluvias.predict(X_input)[0])
        return max(0.0, min(100.0, pred))
    
    # Fallback matemático si el modelo no estuviera cargado
    base = 88.0 if precipitaciones_mm < 500 else 64.0
    return float(base)

def calcular_factor_sensibilidad_climatica(temporada: str, precipitaciones_mm: float) -> float:
    """
    Calcula un factor multiplicador de ajuste para la demanda de sobres 
    según las variaciones climáticas respecto al promedio estacional.
    """
    media_estacional = 650.0 if temporada.upper() == "PV" else 380.0
    if media_estacional == 0:
        return 1.0
    
    ratio = precipitaciones_mm / media_estacional
    # Acotamos el factor entre 0.85 y 1.15 para asegurar estabilidad en las proyecciones
    return float(np.clip(ratio, 0.85, 1.15)) 