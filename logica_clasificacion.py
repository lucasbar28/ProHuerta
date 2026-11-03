# -*- coding: utf-8 -*-
"""Decisión operativa del clasificador de alta demanda."""
from __future__ import annotations

from typing import Any

import pandas as pd

UMBRAL_ALTA_DEMANDA = 0.37


def preparar_entrada_clasificador(
    temporada: str,
    oferta_catalogo: float,
    tipo_huerta: str,
    tipo_localizacion: str,
    experiencia: str,
    superficie: str,
    destino: str,
    ocupacion: str,
) -> pd.DataFrame:
    """Adapta los datos del formulario al contrato del clasificador."""
    return pd.DataFrame(
        [
            {
                "temporada": str(temporada).upper(),
                "oferta_catalogo": float(oferta_catalogo),
                "tipo_huerta": tipo_huerta,
                "tipo_localizacion": tipo_localizacion,
                "experiencia": experiencia,
                "superficie": superficie,
                "destino": destino,
                "ocupacion": ocupacion,
            }
        ]
    )


def predecir_alerta_alta_demanda(
    modelo: Any,
    entrada: pd.DataFrame,
    umbral: float = UMBRAL_ALTA_DEMANDA,
) -> tuple[int, float | None]:
    """Devuelve la clase operativa y la probabilidad de alta demanda."""
    if hasattr(modelo, "predict_proba"):
        probabilidades = modelo.predict_proba(entrada)
        if probabilidades.ndim == 2 and probabilidades.shape[1] >= 2:
            clases = list(getattr(modelo, "classes_", []))
            indice = clases.index(1) if 1 in clases else probabilidades.shape[1] - 1
            probabilidad = float(probabilidades[0, indice])
            return int(probabilidad >= float(umbral)), probabilidad
    return int(modelo.predict(entrada)[0]), None
