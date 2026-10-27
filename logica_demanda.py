# -*- coding: utf-8 -*-
"""Reglas de negocio de demanda, variaciones, alertas y calidad de muestra.

Este modulo no conoce Flask ni el modelo: recibe valores ya calculados para
que las mismas reglas se usen en API, interfaz y pruebas.
"""
from __future__ import annotations

import math

MUESTRA_MINIMA_SOLICITUDES = 10
MUESTRA_MINIMA_ANIOS = 2


def _numero(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def calcular_variacion(
    predicho: object, referencia: object
) -> float | None:
    """Variacion porcentual; None si falta la base o no es comparable."""
    pred = _numero(predicho)
    ref = _numero(referencia)
    if pred is None or ref is None or ref <= 0:
        return None
    return (pred - ref) / ref * 100.0


def clasificar_muestra(
    solicitudes_historicas: object, anios_historicos: object
) -> dict[str, object]:
    """Marca muestras pequenas sin alterar el calculo de la prediccion."""
    solicitudes = max(0, int(_numero(solicitudes_historicas) or 0))
    anios = max(0, int(_numero(anios_historicos) or 0))
    limitada = (
        solicitudes < MUESTRA_MINIMA_SOLICITUDES
        or anios < MUESTRA_MINIMA_ANIOS
    )
    motivo = None
    if limitada:
        motivo = (
            "Muestra historica limitada: "
            f"{solicitudes} solicitudes en {anios} anio(s); "
            "se requieren al menos "
            f"{MUESTRA_MINIMA_SOLICITUDES} solicitudes y "
            f"{MUESTRA_MINIMA_ANIOS} anios para una lectura mas robusta."
        )
    return {
        "muestra_limitada": limitada,
        "motivo_muestra": motivo,
        "n_solicitudes_historicas": solicitudes,
        "n_anios_historicos": anios,
    }


def evaluar_alerta(
    predicho: object,
    referencia: object,
    margen: float,
    diferencia_minima: float,
    muestra_limitada: bool = False,
) -> dict[str, object]:
    """Aplica la regla unica de sobredemanda y devuelve un estado explicito."""
    pred = _numero(predicho)
    ref = _numero(referencia)
    if pred is None or ref is None:
        return {
            "alerta": None,
            "estado": "sin_datos",
            "diferencia_absoluta": None,
            "variacion_pct": None,
            "motivo": "No hay datos suficientes para evaluar la alerta.",
            "muestra_limitada": bool(muestra_limitada),
        }

    diferencia = pred - ref
    variacion = calcular_variacion(pred, ref)
    if ref <= 0:
        return {
            "alerta": False,
            "estado": "sin_referencia",
            "diferencia_absoluta": diferencia,
            "variacion_pct": None,
            "motivo": (
                "La referencia es cero o no comparable; no se calcula "
                "variacion porcentual ni se activa la alerta."
            ),
            "muestra_limitada": bool(muestra_limitada),
        }

    supera_margen = pred > ref * (1.0 + float(margen))
    supera_diferencia = diferencia >= float(diferencia_minima)
    if supera_margen and supera_diferencia:
        motivo = (
            f"La prediccion supera la referencia en {diferencia:.1f} "
            f"sobres ({variacion:+.1f}%) y cumple los umbrales "
            f"(+{float(margen) * 100:.0f}% y "
            f">={float(diferencia_minima):.0f} sobres)."
        )
        if muestra_limitada:
            motivo += " Interpretar con cautela por muestra limitada."
        return {
            "alerta": True,
            "estado": "aumento_relevante",
            "diferencia_absoluta": diferencia,
            "variacion_pct": variacion,
            "motivo": motivo,
            "muestra_limitada": bool(muestra_limitada),
        }

    if muestra_limitada:
        motivo = (
            "No se activa la alerta con la regla vigente. "
            "La muestra historica es limitada."
        )
    else:
        motivo = "No se activa la alerta con la regla vigente."
    return {
        "alerta": False,
        "estado": "sin_alerta",
        "diferencia_absoluta": diferencia,
        "variacion_pct": variacion,
        "motivo": motivo,
        "muestra_limitada": bool(muestra_limitada),
    }
