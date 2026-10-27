# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import os

os.environ.setdefault("PLOTLY_API_KEY", "")
os.environ.setdefault("PLOTLY_USERNAME", "")
os.environ.setdefault("PLOTLY_CLOUD_URL", "")

import plotly
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "iframe"
pio.show_link = False
plotly.io.use_remote_plotly = False

import geopandas as gpd
import pydeck as pdk
from dash import Dash, Input, Output, State, dcc, html, no_update
import dash
import dash_bootstrap_components as dbc

import app as core

MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
VIEW_STATE = pdk.ViewState(
    latitude=-35.58,
    longitude=-58.01,
    zoom=13.0,
    pitch=45,
    bearing=-12,
    max_pitch=70,
)

SPROUT_ICON = "data:image/png;base64," + (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAACMklEQVR4nO1by1EDMQy13mwLVAAnCmC4UEIKoQJOnDhRAYWkBC4MBeREKqAImBwys7Oz/kiWvHKcd0tWlv2eZHnWa4dwxdiglp09/Xz8ldp+3j03GRt5IbyVIOSduLUQ1JL09+NLsb+Hr/cmYlAwJM8hLBWkVgTyTtxaCNIkb0m8RAiJCKRBviXxnBBcEdAz+bX+uSsQaZJPVW5roaSZQBLyHOJbClEiAlqSl9hzMR9fyXSYcgYxJzVEzm1b1I/T+FOZgFxjTwXPojBC4lQrjS2nQ2mwwJ332oNuJUIsC6bWb3McvP3uo89eb3Yq9YBihi2iP8e8nxRxiRCppRHBGTjkJfZLkOWaz8Hu9r7aRyobYlmAMDhQGn1LaEQ/Nx1iKwLCxtAiL60JCIMDHGPtaaEdfUkWYOv53xJrdQA1Ti4BkDS6JBEQBgekDU9ZIM0ETxmEWgdcMp7IF22JcUhxd4X3x4PJUsh5VZ40O/YW3S6K4P54UPXH3ShBcAAtESS7RAiDA2ubBNYfL2LRk0SQ03ZtUwTBGbgiSEUzWQW0cCalvSvcjQDaJFPA/MfWdcAS103RCLD84xKzoKsPI62BnEHvWZAbP7Y8qNwaa7xQYtxrFpScF4LEWQ8oHS9SD5eq9SIC58gccs56rwe58YPrxHsWcM8JEse551Nj0pOi4HTitSbUHJgGtzNvItSeFidpx0PfFzhj6Bsjcwx7Z2iOoW+NLTHkvcE1DHtztKe7w2F0/AM7bEfRW+y09gAAAABJRU5ErkJggg=="
)

SEASON_LABELS = {
    "OI": "Otoño - Invierno",
    "PV": "Primavera - Verano",
}
VARIABLE_LABELS = {
    "paquetes": "Sobres equivalentes",
    "presupuesto": "Presupuesto estimado",
}

PERIODS = core.available_periods()
YEARS = sorted(
    {
        int(item["anio"])
        for item in PERIODS
        if int(item["anio"]) > core.MAX_ANIO_OBSERVADO
    }
) or [int(core.MAX_ANIO_OBSERVADO) + 1]
BARRIOS = sorted(core.map_barrios(), key=lambda item: item["barrio_nombre"])
REAL_GEO_PATH = core.BASE_DIR / "datos" / "geospatial" / "chascomus_barrios_reales.geojson"
GDF = gpd.read_file(REAL_GEO_PATH if REAL_GEO_PATH.exists() else core.GEO_PATH)
GEOMETRIES = {
    str(row["barrio_norm"]): row.geometry.__geo_interface__["coordinates"]
    for _, row in GDF.iterrows()
}

DEFAULT_SEASON = "PV"
DEFAULT_YEAR = 2027 if 2027 in YEARS else YEARS[0]
DEFAULT_VARIABLE = "paquetes"
DEFAULT_BARRIO = next(
    (item["barrio_norm"] for item in BARRIOS if "esmeralda" in item["barrio_norm"]),
    BARRIOS[0]["barrio_norm"],
)


def _number(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def format_metric(value: float, variable: str, compact: bool = False) -> str:
    if variable == "presupuesto":
        if compact and abs(value) >= 1_000_000:
            return "$" + _number(value / 1_000_000.0, 2) + " M"
        if compact and abs(value) >= 1_000:
            return "$" + _number(value / 1_000.0, 0) + " k"
        return "$" + _number(value, 0)
    if compact and abs(value) >= 1_000:
        return _number(value / 1_000.0, 1) + "k"
    return _number(value, 0)


def format_pct(value: float) -> str:
    return f"{value:+.1f}%".replace(".", ",")


def metric_value(summary: dict, kind: str, variable: str) -> float:
    if variable == "presupuesto":
        return float(summary.get(f"{kind}_presupuesto", 0.0) or 0.0)
    return float(summary.get(f"{kind}_paquetes", 0.0) or 0.0)


def series_value(item: dict, variable: str) -> float:
    if variable == "presupuesto":
        return float(item.get("presupuesto", 0.0) or 0.0)
    return float(item.get("paquetes", 0.0) or 0.0)


def build_barrio_rows(anio: int, temporada: str, variable: str) -> list[dict]:
    rows = []
    for feature in core.GEOJSON["features"]:
        props = feature["properties"]
        norm = str(props["barrio_norm"])
        summary = core.barrio_summary(norm, anio, temporada)
        rows.append(
            {
                "norm": norm,
                "name": str(props["barrio_nombre"]),
                "lat": float(props["lat_centroide"]),
                "lng": float(props["lng_centroide"]),
                "radius_m": float(props.get("radio_m") or 260.0),
                "geometry": GEOMETRIES.get(norm)
                or feature.get("geometry", {}).get("coordinates"),
                "hist": metric_value(summary, "historico", variable),
                "proj": metric_value(summary, "proyectado", variable),
                "alerts": int(summary.get("alerta_sobredemanda", 0) or 0),
                "solicitudes": int(summary.get("solicitudes_esperadas", 0) or 0),
                "tasa_alerta": float(summary.get("tasa_alerta", 0.0) or 0.0),
                "alerta_barrio": int(summary.get("alerta_barrio", 0) or 0),
                "variation": float(summary.get("variacion_pct", 0.0) or 0.0),
                "sin_datos": bool(summary.get("sin_datos", True)),
                "summary": summary,
            }
        )
    return rows


def build_deck(
    rows: list[dict],
    anio: int,
    temporada: str,
    variable: str,
    selected_norm: str,
) -> str:
    max_value = max(
        [row["hist"] for row in rows] + [row["proj"] for row in rows] + [1.0]
    )
    elevation_scale = 1100.0 / max_value

    polygons = []
    hist_columns = []
    proj_columns = []
    labels = []
    icons = []

    screen_right = math.radians(55.0)

    for row in rows:
        offset_m = min(110.0, max(35.0, row["radius_m"] * 0.18))
        east_m = math.sin(screen_right) * offset_m
        north_m = math.cos(screen_right) * offset_m
        delta_lng = east_m / (111_320.0 * math.cos(math.radians(row["lat"])))
        delta_lat = north_m / 110_540.0
        is_selected = row["norm"] == selected_norm
        variation_label = (
            "s/d" if row["sin_datos"] else format_pct(row["variation"])
        )
        label = f"{row['name']} · {variation_label}"
        diff = row["proj"] - row["hist"]
        if diff >= 0:
            diff_label = "+" + format_metric(diff, variable, compact=True)
        else:
            diff_label = format_metric(diff, variable, compact=True)
        base = {
            "norm": row["norm"],
            "name": row["name"],
            "expected_label": format_metric(row["hist"], variable),
            "predicted_label": format_metric(row["proj"], variable),
            "var_label": variation_label,
            "alerta_label": "ALERTA" if row["alerta_barrio"] else "ESTABLE",
            "diff_label": diff_label,
        }
        
        # LÓGICA VISUAL DE POLÍGONOS NEUTRALES
        if row["sin_datos"]:
            fill_color = [120, 120, 120, 20]
            line_color = [100, 100, 100, 150]
            elevacion_base = 0.0
        else:
            # Color base neutral para todos los barrios con datos
            fill_color = [158, 158, 158, 30] 
            line_color = [158, 158, 158, 180]
            elevacion_base = 5.0 

        # Si está seleccionado, destaca en blanco
        if is_selected:
            fill_color = [255, 255, 255, 60]
            line_color = [255, 255, 255, 255]
            elevacion_base += 15.0

        polygons.append(
            {
                **base,
                "polygon": row["geometry"],
                "is_selected": is_selected,
                "alerta": bool(row["alerta_barrio"]),
                "fill_color": fill_color,
                "line_color": line_color,
                "elevation": elevacion_base,
            }
        )
        if row["hist"] > 0 and not row["sin_datos"]:
            hist_columns.append(
                {
                    **base,
                    "position": [row["lng"] - delta_lng, row["lat"] - delta_lat],
                    "value": row["hist"],
                    "is_selected": is_selected,
                }
            )
        if row["proj"] > 0 and not row["sin_datos"]:
            ratio = (row["proj"] / row["hist"]) if row["hist"] > 0 else 1.0
            
            # LÓGICA VISUAL DE LAS COLUMNAS (ALERTAS Y DEMANDA)
            if row["alerta_barrio"] or ratio >= 1.15:
                proj_color = [255, 61, 61, 248]   # Alerta (Rojo)
            elif ratio <= 0.95:
                proj_color = [33, 150, 243, 242]  # Baja demanda (Azul)
            elif ratio >= 1.05:
                proj_color = [255, 143, 0, 242]   # Crecimiento (Naranja)
            else:
                proj_color = [76, 175, 80, 238]   # Estable (Verde)
                
            if is_selected:
                proj_color = [min(255, proj_color[0] + 20), min(255, proj_color[1] + 20), min(255, proj_color[2] + 20), 255]
                
            proj_columns.append(
                {
                    **base,
                    "position": [row["lng"] + delta_lng, row["lat"] + delta_lat],
                    "value": row["proj"],
                    "is_selected": is_selected,
                    "fill_color": proj_color,
                }
            )
        labels.append(
            {
                **base,
                "position": [row["lng"], row["lat"] + 0.0009],
                "label": label,
                "text_anchor": "middle",
                "alignment_baseline": "top",
                "is_selected": is_selected,
            }
        )
        if row["hist"] > 0 and not row["sin_datos"]:
            icons.append(
                {
                    **base,
                    "position": [row["lng"], row["lat"] - 0.0012],
                    "icon_data": {
                        "url": SPROUT_ICON,
                        "width": 64,
                        "height": 64,
                        "anchorY": 64,
                    },
                }
            )

    polygon_layer = pdk.Layer(
        "PolygonLayer",
        data=polygons,
        get_polygon="polygon",
        get_fill_color="fill_color",
        get_line_color="line_color",
        get_line_width=3.2,
        line_width_min_pixels=2.6,
        line_width_units='"pixels"',
        stroked=True,
        filled=True,
        extruded=True,
        get_elevation="elevation",
        wireframe=False,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 50],
    )

    # El "glow" rojo perimetral se mantiene sutilmente para los barrios en alerta
    glow_polygons = [item for item in polygons if item.get("alerta")]
    glow_layer = pdk.Layer(
        "PolygonLayer",
        data=glow_polygons,
        get_polygon="polygon",
        get_line_color=[255, 61, 61, 70],
        get_line_width=9,
        line_width_min_pixels=8,
        line_width_units='"pixels"',
        stroked=True,
        filled=False,
        extruded=True,
        get_elevation="elevation",
        pickable=False,
    )

    hist_layer = pdk.Layer(
        "ColumnLayer",
        data=hist_columns,
        get_position="position",
        get_elevation="value",
        elevation_scale=elevation_scale,
        radius=60,
        get_fill_color=[144, 164, 174, 200],
        disk_resolution=6,
        coverage=0.86,
        pickable=True,
        auto_highlight=True,
        material={
            "ambient": 0.45,
            "diffuse": 0.7,
            "shininess": 28,
            "specularColor": [245, 248, 250],
        },
    )

    proj_layer = pdk.Layer(
        "ColumnLayer",
        data=proj_columns,
        get_position="position",
        get_elevation="value",
        elevation_scale=elevation_scale,
        radius=70,
        get_fill_color="fill_color",
        disk_resolution=6,
        coverage=0.92,
        pickable=True,
        auto_highlight=True,
        material={
            "ambient": 0.48,
            "diffuse": 0.75,
            "shininess": 32,
            "specularColor": [255, 250, 250],
        },
    )

    icon_layer = pdk.Layer(
        "IconLayer",
        data=icons,
        get_icon="icon_data",
        get_position="position",
        get_size=30,
        size_units="'pixels'",
        pickable=False,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=labels,
        get_position="position",
        get_text="label",
        get_size=12,
        get_color=[33, 33, 33],
        size_units="'pixels'",
        billboard=True,
        background=True,
        get_background_color=[255, 255, 255, 235],
        background_padding=[6, 2],
        get_text_anchor="text_anchor",
        get_alignment_baseline="alignment_baseline",
        font_family="'Inter, Arial, sans-serif'",
        pickable=False,
    )

    tooltip = {
        "html": (
            "<div style='font-family:Inter,Arial,sans-serif;font-size:12px;line-height:1.6'>"
            "<b style='font-size:13px'>{name}</b><br/>"
            "<span style='color:#90a4ae'>Histórico</span> {expected_label}<br/>"
            "<span style='color:#ff5252'>Proyectado</span> {predicted_label}<br/>"
            "<span style='color:#ff9800'>Exceso / Déficit</span> <b>{diff_label}</b><br/>"
            "Variación <b>{var_label}</b> &nbsp;·&nbsp; <b>{alerta_label}</b>"
            "</div>"
        ),
        "style": {
            "backgroundColor": "rgba(20, 22, 36, 0.98)",
            "border": "1px solid rgba(255, 82, 82, 0.6)",
            "borderRadius": "10px",
            "color": "#f8fafc",
            "padding": "10px 14px",
            "boxShadow": "0 14px 32px rgba(0,0,0,0.5)",
        },
    }

    deck = pdk.Deck(
        layers=[
            polygon_layer,
            glow_layer,
            hist_layer,
            proj_layer,
            icon_layer,
            text_layer,
        ],
        initial_view_state=VIEW_STATE,
        map_style=MAP_STYLE,
        map_provider="carto",
        tooltip=tooltip,
    )
    html_doc = deck.to_html(
        as_string=True,
        notebook_display=False,
        iframe_width="100%",
        iframe_height=800,
    )
    click_bridge = """
    if (typeof deckInstance !== 'undefined') {
      deckInstance.setProps({
        onClick: (info) => {
          if (info && info.object && info.object.norm) {
            window.parent.postMessage(
              {type: "prohuerta-barrio", barrio: info.object.norm},
              "*"
            );
          }
        }
      });
    }
    """
    nav_controls = """
    (function(){
      if (typeof deckInstance === 'undefined') return;
      try {
        deckInstance.setProps({
          controller: {
            dragPan: true,
            dragRotate: true,
            scrollZoom: true,
            touchZoom: true,
            touchRotate: true,
            keyboard: true,
            doubleClickZoom: true
          }
        });
      } catch(e) {}
      const container = document.querySelector('.deckgl-parent') || document.body;
      if (container.querySelector('.prohuerta-nav')) return;
      container.style.position = 'relative';
      const nav = document.createElement('div');
      nav.className = 'prohuerta-nav';
      nav.style.cssText = 'position:absolute;right:14px;bottom:72px;display:flex;flex-direction:column;gap:6px;z-index:10;';
      const zoomIn = document.createElement('button');
      zoomIn.style.cssText = 'width:30px;height:30px;border-radius:6px;border:1px solid #e6e0d6;background:rgba(255,255,255,0.98);color:#2e7d32;font-size:18px;cursor:pointer;line-height:1;';
      zoomIn.textContent = '+';
      const zoomOut = document.createElement('button');
      zoomOut.style.cssText = 'width:30px;height:30px;border-radius:6px;border:1px solid #e6e0d6;background:rgba(255,255,255,0.98);color:#2e7d32;font-size:18px;cursor:pointer;line-height:1;';
      zoomOut.textContent = '-';
      zoomIn.onclick = function(){ try { const vs = deckInstance.viewState || deckInstance.props.viewState || {}; const nv = {...vs, zoom: (vs.zoom||13)+0.5}; deckInstance.setProps({viewState: nv}); } catch(e){} };
      zoomOut.onclick = function(){ try { const vs = deckInstance.viewState || deckInstance.props.viewState || {}; const nv = {...vs, zoom: Math.max(9,(vs.zoom||13)-0.5)}; deckInstance.setProps({viewState: nv}); } catch(e){} };
      nav.appendChild(zoomIn);
      nav.appendChild(zoomOut);
      container.appendChild(nav);
      const compass = document.createElement('div');
      compass.style.cssText = 'position:absolute;right:14px;top:14px;width:30px;height:30px;border-radius:50%;border:1px solid #e6e0d6;background:rgba(255,255,255,0.98);display:flex;align-items:center;justify-content:center;color:#2e7d32;font-size:10px;z-index:10;';
      compass.textContent = 'N';
      container.appendChild(compass);
    })();
    """
    if "</script>" in html_doc:
        head, separator, tail = html_doc.rpartition("</script>")
        return head + click_bridge + nav_controls + separator + tail
    return html_doc + "<script>" + click_bridge + nav_controls + "</script>"

def rounded_panel(*children, class_name: str = ""):
    return dbc.Card(list(children), className=f"panel {class_name}".strip())


def field(label: str, control):
    return html.Div(
        [html.Div(label, className="field-label"), control],
        className="field",
    )


def dark_dropdown(component_id: str, options, value, searchable: bool = False):
    return dcc.Dropdown(
        id=component_id,
        options=options,
        value=value,
        clearable=False,
        searchable=searchable,
        className="dark-dropdown",
        optionHeight=36,
    )


def kpi_card(rows: list[dict], variable: str):
    valid = [row for row in rows if not row["sin_datos"]]
    total_hist = sum(row["hist"] for row in valid)
    total_proj = sum(row["proj"] for row in valid)
    delta = ((total_proj - total_hist) / total_hist * 100.0) if total_hist else 0.0
    delta_class = "positive" if delta >= 0 else "negative"
    arrow = "bi-arrow-up-right" if delta >= 0 else "bi-arrow-down-right"
    alerts = sum(1 for row in valid if row["alerta_barrio"])
    return rounded_panel(
        html.Div(
            [
                html.Span("Demanda total proyectada", className="kpi-label"),
                html.Span(
                    [html.I(className="bi bi-graph-up-arrow"), " Escenario proyectado"],
                    className="kpi-chip",
                ),
            ],
            className="kpi-head",
        ),
        html.Div(format_metric(total_proj, variable), className="kpi-value kpi-value-lg"),
        html.Div(
            [
                html.Div(
                    [
                        html.I(className=f"bi {arrow}"),
                        html.Span(format_pct(delta)),
                        html.Span(
                            " vs. demanda histórica",
                            className="kpi-delta-note",
                        ),
                    ],
                    className=f"kpi-delta {delta_class}",
                ),
                html.Div(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill"),
                        html.Span(f"{alerts} barrio{'s' if alerts != 1 else ''} en alerta"),
                    ],
                    className="kpi-alert-pill",
                )
                if alerts > 0
                else html.Div(
                    [
                        html.I(className="bi bi-check-circle-fill"),
                        html.Span("Sin alertas críticas"),
                    ],
                    className="kpi-ok-pill",
                ),
            ],
            className="kpi-foot",
        ),
        html.Div(
            f"Unidad de análisis: {VARIABLE_LABELS[variable].lower()} · {len(valid)} barrios con datos",
            className="kpi-sub",
        ),
        class_name="kpi-card kpi-card-hero",
    )


def alert_card(rows: list[dict]):
    valid = [row for row in rows if not row["sin_datos"]]
    barrios_alerta = sum(1 for row in valid if row["alerta_barrio"])
    note = (
        "Predicho > esperado × "
        f"{1 + core.MARGEN_SOBREDEMANDA:.2f} y diferencia ≥ "
        f"{core.DIFERENCIA_MINIMA_SOBRES:.0f} sobres"
    )
    if barrios_alerta == 0:
        return rounded_panel(
            html.Div(
                [html.I(className="bi bi-check-circle-fill"), "Barrios en alerta"],
                className="alert-title",
            ),
            html.Div("0", className="alert-value"),
            html.Div(
                f"Sin sobredemanda en {len(valid)} barrios con datos. {note}",
                className="alert-sub",
            ),
            class_name="alert-card ok",
        )
    return rounded_panel(
        html.Div(
            [html.I(className="bi bi-exclamation-triangle-fill"), "Barrios en alerta"],
            className="alert-title",
        ),
        html.Div(str(barrios_alerta), className="alert-value"),
        html.Div(
            f"{barrios_alerta} de {len(valid)} barrios con datos. {note}",
            className="alert-sub",
        ),
        class_name="alert-card",
    )


def detail_card(selected: dict | None, anio: int, temporada: str, variable: str):
    if selected is None:
        return rounded_panel(
            html.Div("Detalle territorial", className="kicker"),
            html.Div("Sin barrio seleccionado", className="detail-name"),
            class_name="detail-card",
        )

    summary = selected["summary"]
    has_data = not selected["sin_datos"]
    name = selected["name"]
    alerta = selected["alerta_barrio"]
    hist = selected["hist"]
    proj = selected["proj"]
    variation = selected["variation"]
    ref_year = summary.get("anio_referencia")
    top_species = summary.get("top_especies") or []
    solicitudes = summary.get("solicitudes_esperadas", 0)
    crecimiento = float(summary.get("crecimiento_anual", 0.0) or 0.0)
    anios = summary.get("anios_historicos", [])
    diferencia = proj - hist
    superficie_ha = summary.get("superficie_ha")
    radios_censales = summary.get("radios_censales")

    if has_data and alerta:
        badge = html.Span(
            [html.I(className="bi bi-exclamation-triangle-fill"), "ALERTA CRÍTICA"],
            className="badge-critical badge-critical-strong",
        )
    elif has_data:
        badge = html.Span("ESTABLE", className="badge-stable")
    else:
        badge = html.Span("SIN DATOS", className="badge-neutral")

    if has_data:
        variation_class = "up" if variation >= 0 else "down"
        variation_icon = (
            "bi-arrow-up-right" if variation >= 0 else "bi-arrow-down-right"
        )
        variation_text = format_pct(variation)
        variation_note = "predicho vs. esperado"
    else:
        variation_class = "flat"
        variation_icon = "bi-dash"
        variation_text = "s/d"
        variation_note = "sin referencia suficiente"

    if has_data and alerta:
        top_name = (
            top_species[0]["nombre"]
            if top_species
            else "las variedades de mayor rotación"
        )
        recommendation = (
            f"Sobredemanda: el escenario supera el baseline en "
            f"{format_metric(diferencia, variable, compact=True)} "
            f"({format_pct(variation)}). Reforzar el stock de {top_name} y "
            f"coordinar asistencia técnica en {name} durante "
            f"{SEASON_LABELS[temporada].lower()} {anio}."
        )
    elif has_data:
        recommendation = (
            "Demanda contenida: el escenario no supera el baseline con el margen "
            "definido. Mantener el abastecimiento estándar y monitorear la "
            "evolución semanal; reasignar excedentes hacia barrios con alerta."
        )
    else:
        recommendation = (
            "No hay solicitudes específicas suficientes para proyectar este barrio "
            "en la combinación elegida. Probar con otra temporada o año."
        )

    species_chips = [
        html.Span(
            f"{item['nombre']} · {item['solicitudes']}",
            className="species-chip",
        )
        for item in top_species
    ]

    risk_text = None
    if has_data:
        risk_text = (
            f"Alerta de sobredemanda: {'sí' if alerta else 'no'} · "
            f"Diferencia: {format_metric(diferencia, variable, compact=True)}"
        )

    footer_bits = []
    if has_data:
        footer_bits.append(
            f"Base: {ref_year} · {len(anios)} año{'s' if len(anios) != 1 else ''}"
        )
        footer_bits.append(
            f"Crecimiento anual: {format_pct(crecimiento * 100.0)}"
        )
        footer_bits.append(
            f"Solicitudes esperadas: {_number(float(solicitudes), 0)}"
        )
        if superficie_ha is not None:
            footer_bits.append(f"Superficie aprox.: {superficie_ha:.1f} ha")
        if radios_censales is not None:
            footer_bits.append(f"Radios censales INDEC: {radios_censales}")

    return rounded_panel(
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Detalle territorial", className="kicker"),
                        html.Div(name, className="detail-name"),
                    ]
                ),
                badge,
            ],
            className="detail-head",
        ),
        html.Div(
            html.Div("Demanda histórica vs. Proyección", className="compare-title"),
            className="compare-head",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            f"Histórica (ref. {ref_year or '—'})",
                            className="stat-label",
                        ),
                        html.Div(
                            format_metric(hist, variable),
                            className="stat-value muted stat-value-lg",
                        ),
                    ],
                    className="stat-box stat-box-strong",
                ),
                html.Div(
                    [
                        html.Div(f"Proyección {anio}", className="stat-label"),
                        html.Div(
                            format_metric(proj, variable),
                            className="stat-value proj stat-value-lg",
                        ),
                    ],
                    className="stat-box stat-box-strong stat-box-proj",
                ),
            ],
            className="detail-stats detail-stats-lg",
        ),
        html.Div(
            [
                html.I(className=f"bi {variation_icon}"),
                html.Span(variation_text, className="variation-value"),
                html.Span(variation_note, className="variation-note"),
            ],
            className=f"detail-variation {variation_class}",
        ),
        html.Div(
            [
                html.Div("Insights automáticos", className="insight-title"),
                html.Ul(
                    [
                        html.Li(recommendation),
                        html.Li(
                            f"Mayor atención en {name}: {variation_text} respecto a la referencia."
                        ),
                        html.Li(
                            f"Top especies con mayor rotación: {top_species[0]['nombre'] if top_species else 'sin datos'}."
                        ),
                    ],
                    className="insight-list",
                ),
            ],
            className="insight-panel",
        ),
        html.Div(species_chips, className="species-row") if species_chips else None,
        html.Div(
            " · ".join(footer_bits),
            className="detail-footer",
        )
        if footer_bits
        else None,
        class_name="detail-card",
    )


def bar_figure(
    rows: list[dict],
    selected_norm: str,
    anio: int,
    variable: str,
):
    valid = [row for row in rows if not row["sin_datos"]]
    valid.sort(key=lambda row: row["proj"], reverse=True)
    top = valid[:12]
    if selected_norm not in {row["norm"] for row in top}:
        selected = next((row for row in rows if row["norm"] == selected_norm), None)
        if selected is not None:
            top.append(selected)
    names = [row["name"] for row in top]
    expected = [row["hist"] for row in top]
    predicted = [row["proj"] for row in top]
    predicted_colors = [
        "#ff4d6d" if row["alerta_barrio"] else "#22d3ee" for row in top
    ]
    expected_colors = ["#3b82f6" for _ in top]
    predicted_custom = [
        [
            format_metric(row["hist"], variable),
            format_metric(row["proj"], variable),
            format_pct(row["variation"]),
            "ALERTA" if row["alerta_barrio"] else "ESTABLE",
        ]
        for row in top
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Demanda histórica",
            x=names,
            y=expected,
            marker=dict(color=expected_colors, line=dict(width=0)),
            opacity=0.95,
            customdata=[format_metric(value, variable) for value in expected],
            text=[format_metric(value, variable) for value in expected],
            textposition="outside",
            textfont=dict(size=8, color="#c9d1d9"),
            hovertemplate="<b>%{x}</b><br>Histórica: %{customdata}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name=f"Proyección {anio}",
            x=names,
            y=predicted,
            marker=dict(color=predicted_colors, line=dict(width=0)),
            customdata=predicted_custom,
            text=[format_metric(value, variable) for value in predicted],
            textposition="outside",
            textfont=dict(size=8, color="#f8fafc"),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Histórica: %{customdata[0]}<br>"
                "Proyectada: %{customdata[1]}<br>"
                "Variación: %{customdata[2]}<br>"
                "%{customdata[3]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        barmode="group",
        bargap=0.22,
        bargroupgap=0.08,
        margin=dict(l=48, r=28, t=28, b=90),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3e2723", family="Inter, Arial, sans-serif", size=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            x=0,
            font=dict(size=9, color="#4e342e"),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            tickangle=0,
            tickfont=dict(size=9, color="#4e342e"),
            gridcolor="rgba(0,0,0,0)",
            linecolor="#e6e0d6",
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(
                text=(
                    "Presupuesto ($)"
                    if variable == "presupuesto"
                    else "Sobres equivalentes"
                ),
                font=dict(size=9, color="#6d4c41"),
            ),
            tickfont=dict(size=8, color="#6d4c41"),
            gridcolor="rgba(109, 76, 65, 0.08)",
            linecolor="#e6e0d6",
            zeroline=False,
            fixedrange=True,
            tickformat="$,.0f" if variable == "presupuesto" else ",.0f",
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#e6e0d6",
            font=dict(color="#1b5e20", size=11),
        ),
    )
    return fig


def trend_figure(selected: dict | None, anio: int, variable: str):
    if selected is None:
        return go.Figure()

    summary = selected["summary"]
    series = summary.get("serie", [])
    scenarios = summary.get("escenarios", {}) or {}
    observed = {
        int(item["anio"]): series_value(item, variable) for item in series
    }
    future_years = sorted(int(year) for year in scenarios)

    expected_future = {}
    predicted_future = {}
    for year in future_years:
        item = scenarios[year]
        if variable == "presupuesto":
            expected_future[year] = float(
                item.get("esperado_presupuesto", 0.0) or 0.0
            )
            predicted_future[year] = float(
                item.get("predicho_presupuesto", 0.0) or 0.0
            )
        else:
            expected_future[year] = float(
                item.get("esperado_paquetes", 0.0) or 0.0
            )
            predicted_future[year] = float(
                item.get("predicho_paquetes", 0.0) or 0.0
            )

    fig = go.Figure()
    if observed:
        years = sorted(observed)
        fig.add_trace(
            go.Scatter(
                x=years,
                y=[observed[year] for year in years],
                mode="lines+markers",
                name="Observado",
                line=dict(color="#2e7d32", width=2.8, shape="spline"),
                marker=dict(
                    size=9,
                    color="#2e7d32",
                    line=dict(color="#ffffff", width=2),
                ),
                fill="tozeroy",
                fillcolor="rgba(46, 125, 50, 0.1)",
                customdata=[
                    format_metric(observed[year], variable) for year in years
                ],
                hovertemplate="<b>%{x}</b><br>Observado: %{customdata}<extra></extra>",
                showlegend=True,
            )
        )
        last_year = years[-1]
        last_value = observed[last_year]
        if future_years:
            link_years = [last_year] + future_years
            fig.add_trace(
                go.Scatter(
                    x=link_years,
                    y=[last_value] + [expected_future[year] for year in future_years],
                    mode="lines+markers",
                    name="Esperado (baseline)",
                    line=dict(color="#6d4c41", width=2.2, dash="dash"),
                    marker=dict(size=8, color="#6d4c41"),
                    customdata=[
                        format_metric(last_value, variable)
                    ]
                    + [
                        format_metric(expected_future[year], variable)
                        for year in future_years
                    ],
                    hovertemplate=(
                        "<b>%{x}</b><br>Esperado: %{customdata}<extra></extra>"
                    ),
                    showlegend=True,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=link_years,
                    y=[last_value] + [predicted_future[year] for year in future_years],
                    mode="lines+markers",
                    name="Proyectado",
                    line=dict(color="#d62828", width=3.0),
                    marker=dict(
                        size=[9] + [12] * len(future_years),
                        color="#d62828",
                        symbol=["circle"] + ["diamond"] * len(future_years),
                    ),
                    fill="tozeroy",
                    fillcolor="rgba(214, 40, 40, 0.09)",
                    customdata=[
                        format_metric(last_value, variable)
                    ]
                    + [
                        format_metric(predicted_future[year], variable)
                        for year in future_years
                    ],
                    hovertemplate=(
                        "<b>%{x}</b><br>Proyectado: %{customdata}<extra></extra>"
                    ),
                    showlegend=True,
                )
            )
            if last_year == 2026 and 2027 in future_years:
                fig.add_vline(
                    x=2026.5,
                    line_width=1,
                    line_dash="dot",
                    line_color="rgba(109, 76, 65, 0.5)",
                    annotation_text="Transición 2026 → 2027",
                    annotation_position="top",
                    annotation_font=dict(size=9, color="#6d4c41"),
                )

    annotation_year = anio if anio in predicted_future else (
        max(observed) if observed else anio
    )
    if annotation_year in predicted_future:
        annotation_value = predicted_future[annotation_year]
        fig.add_annotation(
            x=annotation_year,
            y=annotation_value,
            text=f"Proyectado {annotation_year}",
            showarrow=False,
            yshift=20,
            font=dict(size=9, color="#ffd6dc"),
            bgcolor="rgba(255,77,109,0.18)",
            bordercolor="rgba(255,77,109,0.5)",
            borderpad=4,
        )
    elif annotation_year in observed:
        annotation_value = observed[annotation_year]
        fig.add_annotation(
            x=annotation_year,
            y=annotation_value,
            text=f"Observado {annotation_year}",
            showarrow=False,
            yshift=20,
            font=dict(size=9, color="#9fe8ff"),
            bgcolor="rgba(34,211,238,0.16)",
            bordercolor="rgba(34,211,238,0.45)",
            borderpad=4,
        )

    all_years = sorted(set(observed) | set(future_years))
    min_year = min(all_years) if all_years else 2024
    max_year = max(all_years) if all_years else 2028
    fig.update_layout(
        margin=dict(l=48, r=18, t=34, b=38),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3e2723", family="Inter, Arial, sans-serif", size=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            x=0,
            font=dict(size=9, color="#4e342e"),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            tickmode="linear",
            dtick=1,
            range=[min_year - 0.2, max_year + 0.2],
            tickfont=dict(size=9, color="#4e342e"),
            gridcolor="rgba(109, 76, 65, 0.08)",
            linecolor="#e6e0d6",
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(
                text=(
                    "Presupuesto ($)"
                    if variable == "presupuesto"
                    else "Sobres equivalentes"
                ),
                font=dict(size=9, color="#6d4c41"),
            ),
            tickfont=dict(size=8, color="#6d4c41"),
            gridcolor="rgba(109, 76, 65, 0.08)",
            linecolor="#e6e0d6",
            zeroline=False,
            fixedrange=True,
            tickformat="$,.0f" if variable == "presupuesto" else ",.0f",
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#e6e0d6",
            font=dict(color="#1b5e20", size=11),
        ),
    )
    return fig


dash_app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
    title="ProHuerta · Inteligencia de demanda",
    update_title=None,
)

header = html.Header(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.I(className="bi bi-map-fill"),
                        html.Div(
                            [
                                html.Div("ProHuerta", className="brand-title"),
                                html.Div(
                                    "Inteligencia de demanda · Banco de Semillas",
                                    className="brand-sub",
                                ),
                            ],
                        ),
                    ],
                    className="brand-block",
                ),
            ],
            className="header-left",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.I(className="bi bi-grid-fill"),
                        html.Span("Mapa 3D"),
                    ],
                    className="nav-item active",
                ),
                html.Div(
                    [
                        html.I(className="bi bi-bar-chart-fill"),
                        html.Span("Análisis"),
                    ],
                    className="nav-item",
                ),
                html.Div(
                    [
                        html.I(className="bi bi-table"),
                        html.Span("Datos"),
                    ],
                    className="nav-item",
                ),
                html.Div(
                    [
                        html.I(className="bi bi-info-circle-fill"),
                        html.Span("Acerca de"),
                    ],
                    className="nav-item",
                ),
            ],
            className="header-nav",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [html.Span("CH")],
                            className="logo-mark",
                        ),
                        html.Div(
                            [
                                html.Div("Municipalidad de", className="logo-kicker"),
                                html.Div("Chascomús", className="logo-name"),
                            ],
                            className="logo-copy",
                        ),
                    ],
                    className="logo-block",
                ),
                html.Div(
                    [
                        html.I(className="bi bi-calendar3"),
                        html.Span(
                            "Primavera - Verano 2027",
                            id="period-pill",
                        ),
                    ],
                    className="period-pill period-pill-compact",
                ),
            ],
            className="header-right",
        ),
    ],
    className="app-header",
)

def priorities_card(rows: list[dict], variable: str):
    valid = [row for row in rows if not row["sin_datos"] and row["alerta_barrio"]]
    if not valid:
        return rounded_panel(
            html.Div(
                [html.I(className="bi bi-check-circle-fill"), "Prioridades a reforzar"],
                className="alert-title",
            ),
            html.Div("Sin barrios en alerta", className="alert-sub"),
            class_name="alert-card ok",
        )
    sorted_rows = sorted(valid, key=lambda r: (r["proj"] - r["hist"]), reverse=True)[:5]
    items = []
    for row in sorted_rows:
        diff = row["proj"] - row["hist"]
        diff_label = "+" + format_metric(diff, variable, compact=True) if diff >= 0 else format_metric(diff, variable, compact=True)
        items.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(row["name"], className="prio-name"),
                            html.Div(f"Exceso {diff_label}", className="prio-diff"),
                        ],
                        className="prio-row-text",
                    ),
                    html.Button(
                        "Ver",
                        id={"type": "prio-go", "norm": row["norm"]},
                        n_clicks=0,
                        className="prio-go-btn",
                    ),
                ],
                className="prio-row",
            )
        )
    return rounded_panel(
        html.Div(
            [html.I(className="bi bi-exclamation-triangle-fill"), "Prioridades a reforzar"],
            className="alert-title",
        ),
        html.Div(items, className="prio-list"),
        class_name="alert-card",
    )


sidebar = html.Div(
    [
        rounded_panel(
            html.Div("Filtros", className="section-title"),
            field(
                "Temporada",
                dark_dropdown(
                    "temporada",
                    [
                        {"label": label, "value": code}
                        for code, label in SEASON_LABELS.items()
                    ],
                    DEFAULT_SEASON,
                ),
            ),
            field(
                "Año proyectado",
                dark_dropdown(
                    "anio",
                    [{"label": str(year), "value": year} for year in YEARS],
                    DEFAULT_YEAR,
                ),
            ),
            html.Div(
                "2027-2028: baseline con crecimiento esperado por temporada; "
                "2025-2026 son históricos observados con barrio.",
                className="field-note",
            ),
            field(
                "Variable de análisis",
                dark_dropdown(
                    "variable",
                    [
                        {"label": label, "value": code}
                        for code, label in VARIABLE_LABELS.items()
                    ],
                    DEFAULT_VARIABLE,
                ),
            ),
            field(
                "Barrio",
                dark_dropdown(
                    "barrio",
                    [
                        {"label": item["barrio_nombre"], "value": item["barrio_norm"]}
                        for item in BARRIOS
                    ],
                    DEFAULT_BARRIO,
                    searchable=True,
                ),
            ),
            html.Button(
                [html.I(className="bi bi-stars me-2"), "Analizar escenario"],
                id="btn-analizar",
                n_clicks=0,
                className="analyze-btn",
            ),
            class_name="filter-card",
        ),
        html.Div(id="kpi-panel"),
        html.Div(id="alert-panel"),
        html.Div(id="priorities-panel"),
    ],
    className="sidebar",
)

main = html.Div(
    [
        html.Div(
            [
                rounded_panel(
                    html.Iframe(
                        id="map-frame",
                        srcDoc="",
                        style={
                            "width": "100%",
                            "height": "100%",
                            "border": "0",
                            "display": "block",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Mapa de demanda · Chascomús",
                                className="map-title",
                            ),
                            html.Div(
                                "Esperado vs. predicho · límites censales INDEC",
                                className="map-title-sub",
                            ),
                        ],
                        className="map-overlay-top",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(className="legend-dot cyan"),
                                    "Histórico",
                                ],
                                className="legend-item",
                            ),
                            html.Div(
                                [
                                    html.Span(className="legend-dot magenta"),
                                    "Predicho (ML)",
                                ],
                                className="legend-item",
                            ),
                            html.Div(
                                [
                                    html.Span(style={"width": "10px", "height": "10px", "borderRadius": "50%", "background": "#ff3d3d", "boxShadow": "0 0 8px rgba(255,61,61,0.8)"}),
                                    "Alerta / Exceso",
                                ],
                                className="legend-item",
                            ),
                            html.Div(
                                [
                                    html.Span(className="legend-leaf"),
                                    "Entrega de semillas",
                                ],
                                className="legend-item",
                            ),
                        ],
                        className="map-legend",
                    ),
                    class_name="map-card",
                ),
                html.Div(id="detail-panel", className="detail-slot"),
            ],
            className="top-row",
        ),
        html.Div(
            [
                rounded_panel(
                    html.Div(
                        [
                            html.Div("Comparativo por barrio", className="chart-title"),
                            html.Div(
                                "Esperado vs. predicho · Top 15 por predicción",
                                className="chart-sub",
                            ),
                        ],
                        className="chart-head",
                    ),
                    dcc.Graph(
                        id="bar-chart",
                        config={"displayModeBar": False, "responsive": True},
                        className="chart-graph",
                        style={"height": "100%", "width": "100%"},
                    ),
                    class_name="chart-card",
                ),
                rounded_panel(
                    html.Div(
                        [
                            html.Div("Tendencia temporal", className="chart-title"),
                            html.Div(
                                "Observado + baseline esperado + predicción 2027-2028",
                                className="chart-sub",
                            ),
                        ],
                        className="chart-head",
                    ),
                    dcc.Graph(
                        id="trend-chart",
                        config={"displayModeBar": False, "responsive": True},
                        className="chart-graph",
                        style={"height": "100%", "width": "100%"},
                    ),
                    class_name="chart-card",
                ),
            ],
            className="bottom-row",
        ),
    ],
    className="main",
)

dash_app.layout = html.Div(
    [
        header,
        html.Div([sidebar, main], className="app-body"),
        html.Footer(
            [
                html.Div(
                    [
                        html.Span("Fuente: Banco de Semillas ProHuerta · Chascomús"),
                        html.Span("·"),
                        html.Span("Arquitectura: Random Forest + GeoPandas + Pydeck"),
                    ],
                    className="footer-left",
                ),
                html.Div(
                    [
                        html.Span(id="footer-timestamp", className="footer-time"),
                        html.Button(
                            [html.I(className="bi bi-file-earmark-pdf me-2"), "Descargar informe PDF"],
                            id="btn-download-pdf",
                            n_clicks=0,
                            className="footer-btn",
                        ),
                    ],
                    className="footer-right",
                ),
            ],
            className="app-footer",
        ),
        dcc.Store(id="map-click-store"),
        dcc.Interval(id="footer-clock", interval=60000, n_intervals=0),
    ],
    className="app-shell",
)


@dash_app.callback(
    Output("barrio", "value"),
    Input("map-click-store", "data"),
    Input({"type": "prio-go", "norm": dash.ALL}, "n_clicks"),
    State({"type": "prio-go", "norm": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def select_barrio_from_map(payload, prio_clicks, prio_ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    trigger_id = ctx.triggered[0]["prop_id"]
    if trigger_id.startswith("map-click-store"):
        if payload and payload.get("barrio"):
            return payload["barrio"]
        return no_update
    if "prio-go" in trigger_id:
        if prio_clicks and any(prio_clicks) and prio_ids:
            for clicks, pid in zip(prio_clicks, prio_ids):
                if clicks and clicks > 0 and isinstance(pid, dict):
                    return pid.get("norm")
    return no_update


from datetime import datetime

@dash_app.callback(
    Output("period-pill", "children"),
    Output("map-frame", "srcDoc"),
    Output("kpi-panel", "children"),
    Output("alert-panel", "children"),
    Output("priorities-panel", "children"),
    Output("detail-panel", "children"),
    Output("bar-chart", "figure"),
    Output("trend-chart", "figure"),
    Input("temporada", "value"),
    Input("anio", "value"),
    Input("variable", "value"),
    Input("barrio", "value"),
    Input("btn-analizar", "n_clicks"),
)
def refresh_dashboard(temporada, anio, variable, barrio, _n_clicks):
    temporada = temporada if temporada in SEASON_LABELS else DEFAULT_SEASON
    variable = variable if variable in VARIABLE_LABELS else DEFAULT_VARIABLE
    anio = int(anio) if anio in YEARS else DEFAULT_YEAR
    barrio = barrio or DEFAULT_BARRIO

    rows = build_barrio_rows(anio, temporada, variable)
    selected = next((row for row in rows if row["norm"] == barrio), None)
    selected_norm = selected["norm"] if selected else barrio

    period_label = f"{SEASON_LABELS[temporada]} {anio}"
    map_html = build_deck(rows, anio, temporada, variable, selected_norm)

    return (
        period_label,
        map_html,
        kpi_card(rows, variable),
        alert_card(rows),
        priorities_card(rows, variable),
        detail_card(selected, anio, temporada, variable),
        bar_figure(rows, selected_norm, anio, variable),
        trend_figure(selected, anio, variable),
    )


@dash_app.callback(
    Output("footer-timestamp", "children"),
    Input("footer-clock", "n_intervals"),
)
def update_footer_time(_n_intervals):
    now = datetime.now()
    return f"Última actualización: {now.strftime('%d/%m/%Y %H:%M')}"


if __name__ == "__main__":
    dash_app.run(debug=True, host="127.0.0.1", port=8050)