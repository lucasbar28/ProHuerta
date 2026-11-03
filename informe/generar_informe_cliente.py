# -*- coding: utf-8 -*-
from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.tableofcontents import TableOfContents

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "Informe Final para el Cliente - ProHuerta.pdf"
COVER_IMG = BASE_DIR / "static" / "img" / "huerta-comunitaria.jpg"
FIG_DIR = Path(tempfile.gettempdir()) / "prohuerta_informe_cliente"
FIG_DIR.mkdir(parents=True, exist_ok=True)

FONT_DIR = Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONT_DIR / "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FONT_DIR / "arialbi.ttf")))
pdfmetrics.registerFontFamily(
    "Arial",
    normal="Arial",
    bold="Arial-Bold",
    italic="Arial-Italic",
    boldItalic="Arial-BoldItalic",
)

GREEN = colors.HexColor("#1f8f4e")
GREEN_DARK = colors.HexColor("#125c34")
GREEN_LIGHT = colors.HexColor("#eaf5ee")
BLUE = colors.HexColor("#2f6fb3")
BLUE_LIGHT = colors.HexColor("#eaf1f9")
GREY = colors.HexColor("#4b5563")
GREY_LIGHT = colors.HexColor("#f4f6f8")
GREY_MID = colors.HexColor("#d3dbe3")
AMBER = colors.HexColor("#b7791f")
AMBER_LIGHT = colors.HexColor("#fdf6e7")
RED = colors.HexColor("#b23a3a")
RED_LIGHT = colors.HexColor("#fbeeee")
WHITE = colors.white

PAGE_W, PAGE_H = A4
LM = RM = 2.2 * cm
TM = 2.45 * cm
BM = 2.0 * cm
CONTENT_W = PAGE_W - LM - RM


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(BASE_DIR / "datos" / "preparados" / name, encoding="utf-8-sig")


def fmt_int(value: float | int) -> str:
    return f"{value:,.0f}".replace(",", ".")


def fmt_dec(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def fmt_money(value: float) -> str:
    return f"${value:,.0f}".replace(",", ".")


SOL = read_csv("solicitudes_v2.csv")
ESP = read_csv("solicitud_especies.csv")
CAT = read_csv("catalogo_temporada.csv")

SOL["target_cobertura_valido"] = SOL["target_cobertura_valido"].fillna(False).astype(bool)
ESPECIFICAS = SOL[
    (SOL["esquema_entrega"] == "especifico")
    & SOL["target_cobertura_valido"]
    & SOL["especies_equivalentes"].notna()
].copy()


def build_context() -> dict:
    d = SOL
    es = ESPECIFICAS
    ctx: dict = {}
    ctx["total"] = int(len(d))
    ctx["especificas"] = int((d["esquema_entrega"] == "especifico").sum())
    ctx["genericas"] = int((d["esquema_entrega"] == "kit_generico").sum())
    ctx["modeladas"] = int(len(es))
    ctx["alta_demanda"] = int(es["alerta_alta_demanda"].sum())
    ctx["alta_demanda_pct"] = float(es["alerta_alta_demanda"].mean() * 100)
    ctx["cobertura_media"] = float(es["cobertura_catalogo"].mean())
    ctx["equiv_medio"] = float(es["especies_equivalentes"].mean())
    ctx["presupuesto_especifico"] = float(es["presupuesto_estimado"].sum())
    ctx["presupuesto_generico"] = float(
        d[d["esquema_entrega"] == "kit_generico"]["presupuesto_estimado"].sum()
    )
    ctx["presupuesto_total"] = float(d["presupuesto_estimado"].sum())
    ctx["especies_distintas"] = int(ESP["especie"].nunique())
    ctx["sin_barrio"] = int((d["barrio_norm"] == "sin_dato").sum())
    ctx["sin_barrio_pct"] = float((d["barrio_norm"] == "sin_dato").mean() * 100)
    ctx["con_coords"] = int(d["lat"].notna().sum())
    ctx["barrios_geo"] = 31

    camp = []
    for (anio, temp), sub in d.groupby(["anio", "temporada"]):
        camp.append(
            {
                "anio": int(anio),
                "temporada": temp,
                "n": int(len(sub)),
                "esquema": sub["esquema_entrega"].iloc[0],
                "equiv": float(sub["especies_equivalentes"].mean()),
                "cobertura": (
                    None
                    if sub["cobertura_catalogo"].isna().all()
                    else float(sub["cobertura_catalogo"].mean())
                ),
                "alerta": (
                    None
                    if sub["alerta_alta_demanda"].isna().all()
                    else float(sub["alerta_alta_demanda"].mean() * 100)
                ),
            }
        )
    ctx["campanas"] = camp

    spec = []
    for (anio, temp), sub in es.groupby(["anio", "temporada"]):
        spec.append(
            {
                "anio": int(anio),
                "temporada": temp,
                "n": int(len(sub)),
                "equiv": float(sub["especies_equivalentes"].mean()),
                "cobertura": float(sub["cobertura_catalogo"].mean()),
                "alerta": float(sub["alerta_alta_demanda"].mean() * 100),
            }
        )
    ctx["especificas_campanas"] = spec

    for t in ["OI", "PV"]:
        sub = ESP[ESP["temporada"] == t]
        n = sub["id_solicitud"].nunique()
        top = (
            sub.groupby("especie_nombre")["id_solicitud"]
            .nunique()
            .sort_values(ascending=False)
            .head(10)
        )
        ctx[f"top_{t}"] = [
            {
                "especie": str(k),
                "solicitudes": int(v),
                "pct": round(float(v / n * 100), 1),
            }
            for k, v in top.items()
        ]

    for col in ["tipo_huerta", "superficie", "experiencia", "destino", "tipo_localizacion"]:
        sub = es.groupby(col).agg(
            n=("id_solicitud", "size"),
            equiv=("especies_equivalentes", "mean"),
            cob=("cobertura_catalogo", "mean"),
            alerta=("alerta_alta_demanda", "mean"),
        )
        ctx[col] = {
            str(k): {
                "n": int(r["n"]),
                "equiv": round(float(r["equiv"]), 2),
                "cob": round(float(r["cob"]), 1),
                "alerta": round(float(r["alerta"] * 100), 1),
            }
            for k, r in sub.iterrows()
        }

    barrios = (
        d[d["barrio_norm"] != "sin_dato"]
        .groupby("barrio_nombre")
        .agg(n=("id_solicitud", "size"), equiv=("especies_equivalentes", "sum"))
        .sort_values("n", ascending=False)
    )
    ctx["barrios"] = [
        {"barrio": str(k), "n": int(r["n"]), "equiv": float(r["equiv"])}
        for k, r in barrios.head(10).iterrows()
    ]
    ctx["top5_share"] = float(barrios.head(5)["n"].sum() / barrios["n"].sum() * 100)
    ctx["barrios_con_datos"] = int(barrios.shape[0])

    ctx["catalogo"] = [
        {
            "anio": int(r["anio"]),
            "temporada": str(r["temporada"]),
            "oferta": int(r["oferta_catalogo"]),
        }
        for _, r in CAT.iterrows()
    ]
    return ctx


CTX = build_context()

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.edgecolor": "#9aa7b4",
        "axes.linewidth": 0.7,
        "xtick.color": "#4b5563",
        "ytick.color": "#4b5563",
        "text.color": "#1f2937",
        "axes.labelcolor": "#374151",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)
G = "#1f8f4e"
GD = "#125c34"
B = "#2f6fb3"
A = "#b7791f"
R = "#b23a3a"
MUTED = "#8b98a8"
LIGHT = "#eaf5ee"


def save_fig(fig, name: str) -> str:
    path = FIG_DIR / name
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def chart_campanas() -> str:
    labels = [f"{c['temporada']} {c['anio']}" for c in CTX["campanas"]]
    values = [c["n"] for c in CTX["campanas"]]
    colors_ = [MUTED if c["esquema"] == "kit_generico" else G for c in CTX["campanas"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.05))
    bars = ax.bar(labels, values, color=colors_, width=0.63)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 13,
            f"{value:,}".replace(",", "."),
            ha="center",
            va="bottom",
            fontsize=8.2,
            color="#374151",
            fontweight="bold",
        )
    ax.set_ylabel("Solicitudes registradas")
    ax.set_ylim(0, max(values) * 1.18)
    ax.set_title("Solicitudes registradas por campaña (2022–2026)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.7)
    ax.set_axisbelow(True)
    from matplotlib.patches import Patch
    ax.legend(
        handles=[
            Patch(color=MUTED, label="Kit genérico (sin detalle de variedades)"),
            Patch(color=G, label="Selección específica de variedades"),
        ],
        loc="upper right",
        frameon=False,
        fontsize=7.6,
    )
    fig.tight_layout()
    return save_fig(fig, "fig_campanas.png")


def chart_especies() -> str:
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.7))
    for ax, temporada, color, titulo in [
        (axes[0], "OI", G, "Otoño–Invierno (OI)"),
        (axes[1], "PV", B, "Primavera–Verano (PV)"),
    ]:
        rows = CTX[f"top_{temporada}"][::-1]
        names = [r["especie"] for r in rows]
        vals = [r["pct"] for r in rows]
        bars = ax.barh(names, vals, color=color, height=0.64)
        for bar, value in zip(bars, vals):
            ax.text(
                value + 1.5,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.0f}%",
                va="center",
                fontsize=7.6,
                color="#374151",
            )
        ax.set_xlim(0, 100)
        ax.set_xlabel("% de solicitudes de la temporada")
        ax.set_title(titulo, color=color)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color="#e5e7eb", linewidth=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", labelsize=8.2)
    fig.suptitle(
        "Las variedades más pedidas cambian según la temporada",
        fontsize=10.8,
        fontweight="bold",
        color="#125c34",
        y=1.02,
    )
    fig.tight_layout()
    return save_fig(fig, "fig_especies.png")


def chart_cobertura() -> str:
    rows = CTX["especificas_campanas"]
    labels = [f"{r['temporada']} {r['anio']}" for r in rows]
    cobertura = [r["cobertura"] for r in rows]
    alerta = [r["alerta"] for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.2, 3.15))
    bars = ax.bar(x, cobertura, color=G, width=0.58, label="Cobertura media del catálogo")
    for bar, value in zip(bars, cobertura):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{value:.0f}%",
            ha="center",
            va="bottom",
            fontsize=8.1,
            color="#374151",
            fontweight="bold",
        )
    ax.set_ylim(0, 100)
    ax.set_ylabel("Cobertura media (%)")
    ax.set_xticks(x, labels)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.7)
    ax.set_axisbelow(True)
    ax2 = ax.twinx()
    ax2.plot(
        x,
        alerta,
        color=A,
        marker="o",
        linewidth=2,
        markersize=4.8,
        label="Solicitudes con alta demanda",
    )
    for xi, value in zip(x, alerta):
        ax2.text(
            xi + 0.08,
            value + 3,
            f"{value:.0f}%",
            fontsize=7.8,
            color=A,
            fontweight="bold",
        )
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("Alta demanda (%)", color=A)
    ax2.tick_params(axis="y", colors=A)
    ax2.spines[["top"]].set_visible(False)
    lines, labels_ = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(
        lines + lines2,
        labels_ + labels2,
        loc="upper left",
        frameon=False,
        fontsize=7.6,
        ncol=2,
    )
    ax.set_title("Cobertura del catálogo y proporción de alta demanda")
    fig.tight_layout()
    return save_fig(fig, "fig_cobertura.png")


def chart_barrios() -> str:
    rows = CTX["barrios"][::-1]
    names = [r["barrio"] for r in rows]
    vals = [r["n"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.35))
    bars = ax.barh(names, vals, color=B, height=0.64)
    for bar, value in zip(bars, vals):
        ax.text(
            value + 2,
            bar.get_y() + bar.get_height() / 2,
            f"{value}",
            va="center",
            fontsize=8,
            color="#374151",
            fontweight="bold",
        )
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_xlabel("Solicitudes registradas (todas las campañas con barrio)")
    ax.set_title("Barrios con más solicitudes registradas")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=8.3)
    fig.tight_layout()
    return save_fig(fig, "fig_barrios.png")


def chart_perfiles() -> str:
    grupos = [
        (
            "Localización",
            {
                "Urbana": CTX["tipo_localizacion"]["urbana"]["cob"],
                "Periurbana": CTX["tipo_localizacion"]["periurbana"]["cob"],
                "Rural": CTX["tipo_localizacion"]["rural"]["cob"],
            },
            B,
        ),
        (
            "Destino",
            {
                "Autoconsumo": CTX["destino"]["autoconsumo"]["cob"],
                "Autoconsumo e intercambio": CTX["destino"]["autoconsumo e intercambio"]["cob"],
            },
            A,
        ),
        (
            "Superficie",
            {
                "Hasta 5 m²": CTX["superficie"]["hasta 5 m2"]["cob"],
                "6 a 20 m²": CTX["superficie"]["entre 6 y 20 m2"]["cob"],
                "Más de 20 m²": CTX["superficie"]["más de 20 m2"]["cob"],
            },
            G,
        ),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(8.3, 2.55))
    for ax, (titulo, data, color) in zip(axes, grupos):
        names = list(data.keys())[::-1]
        vals = list(data.values())[::-1]
        bars = ax.barh(names, vals, color=color, height=0.58)
        for bar, value in zip(bars, vals):
            ax.text(
                value + 1.2,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.0f}%",
                va="center",
                fontsize=7.6,
                color="#374151",
            )
        ax.set_xlim(0, 100)
        ax.set_title(titulo, fontsize=9.4, color=color)
        ax.set_xlabel("Cobertura media")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color="#e5e7eb", linewidth=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", labelsize=7.7)
    fig.suptitle(
        "Perfiles que suelen pedir más variedades (2024–2026)",
        fontsize=10.4,
        fontweight="bold",
        color="#125c34",
        y=1.03,
    )
    fig.tight_layout()
    return save_fig(fig, "fig_perfiles.png")


def chart_clima() -> str:
    mm = np.linspace(0, 900, 200)
    cobertura = np.clip(55.4973 + 0.013267 * mm, 0, 100)
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.plot(mm, cobertura, color=B, linewidth=2.4)
    ax.axvline(380, color=G, linestyle="--", linewidth=1.2)
    ax.axvline(650, color=A, linestyle="--", linewidth=1.2)
    ax.text(385, 18, "Promedio OI\n380 mm", color=G, fontsize=7.8, va="bottom")
    ax.text(655, 18, "Promedio PV\n650 mm", color=A, fontsize=7.8, va="bottom")
    ax.axvspan(0, 250, color=R, alpha=0.04)
    ax.axvspan(500, 800, color=G, alpha=0.04)
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Precipitaciones esperadas (mm)")
    ax.set_ylabel("Cobertura estimada (%)")
    ax.set_title("Relación estimada entre lluvia y cobertura del catálogo")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color="#e5e7eb", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.text(
        35,
        92,
        "+100 mm ≈ +1,3 puntos porcentuales",
        fontsize=8.2,
        color="#374151",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#f4faf6", edgecolor="#cfe5d7"),
    )
    fig.tight_layout()
    return save_fig(fig, "fig_clima.png")


CHART_CAMPANAS = chart_campanas()
CHART_ESPECIES = chart_especies()
CHART_COBERTURA = chart_cobertura()
CHART_BARRIOS = chart_barrios()
CHART_PERFILES = chart_perfiles()
CHART_CLIMA = chart_clima()


styles = getSampleStyleSheet()
S: dict[str, ParagraphStyle] = {}
S["body"] = ParagraphStyle(
    "body",
    fontName="Arial",
    fontSize=10.0,
    leading=14.8,
    alignment=TA_JUSTIFY,
    textColor=colors.HexColor("#1f2937"),
    spaceAfter=5.8,
)
S["body_first"] = ParagraphStyle("body_first", parent=S["body"], spaceBefore=2)
S["small"] = ParagraphStyle(
    "small", parent=S["body"], fontSize=8.5, leading=11.8, textColor=GREY
)
S["caption"] = ParagraphStyle(
    "caption",
    fontName="Arial-Italic",
    fontSize=8.2,
    leading=11,
    textColor=GREY,
    alignment=TA_CENTER,
    spaceBefore=3,
    spaceAfter=10,
)
S["h1"] = ParagraphStyle(
    "h1",
    fontName="Arial-Bold",
    fontSize=16,
    leading=19.5,
    textColor=GREEN_DARK,
    spaceBefore=17,
    spaceAfter=7,
    keepWithNext=1,
)
S["h2"] = ParagraphStyle(
    "h2",
    fontName="Arial-Bold",
    fontSize=12.0,
    leading=15.4,
    textColor=GREEN,
    spaceBefore=12,
    spaceAfter=4,
    keepWithNext=1,
)
S["h3"] = ParagraphStyle(
    "h3",
    fontName="Arial-Bold",
    fontSize=10.4,
    leading=13.8,
    textColor=colors.HexColor("#334155"),
    spaceBefore=8,
    spaceAfter=3,
    keepWithNext=1,
)
S["bullet"] = ParagraphStyle(
    "bullet",
    parent=S["body"],
    leftIndent=13,
    bulletIndent=3,
    spaceAfter=2.6,
    bulletFontName="Arial",
)
S["num"] = ParagraphStyle(
    "num",
    parent=S["body"],
    leftIndent=17,
    bulletIndent=2,
    spaceAfter=2.6,
    bulletFontName="Arial",
)
S["cell"] = ParagraphStyle(
    "cell",
    fontName="Arial",
    fontSize=8.2,
    leading=10.6,
    textColor=colors.HexColor("#1f2937"),
    alignment=TA_LEFT,
)
S["cell_center"] = ParagraphStyle("cell_center", parent=S["cell"], alignment=TA_CENTER)
S["cell_bold"] = ParagraphStyle("cell_bold", parent=S["cell"], fontName="Arial-Bold")
S["head"] = ParagraphStyle(
    "head",
    fontName="Arial-Bold",
    fontSize=8.4,
    leading=10.8,
    textColor=WHITE,
    alignment=TA_LEFT,
)
S["head_center"] = ParagraphStyle("head_center", parent=S["head"], alignment=TA_CENTER)
S["callout"] = ParagraphStyle(
    "callout",
    fontName="Arial",
    fontSize=9.0,
    leading=12.8,
    textColor=colors.HexColor("#1f2937"),
    alignment=TA_JUSTIFY,
)
S["kpi_num"] = ParagraphStyle(
    "kpi_num",
    fontName="Arial-Bold",
    fontSize=17,
    leading=19,
    textColor=GREEN_DARK,
    alignment=TA_CENTER,
)
S["kpi_label"] = ParagraphStyle(
    "kpi_label",
    fontName="Arial",
    fontSize=7.7,
    leading=9.6,
    textColor=GREY,
    alignment=TA_CENTER,
)
S["toc_title"] = ParagraphStyle(
    "toc_title",
    fontName="Arial-Bold",
    fontSize=16,
    leading=20,
    textColor=GREEN_DARK,
    spaceAfter=12,
)


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def H1(text: str, key: str | None = None) -> "TOCHeading":
    return TOCHeading(text, S["h1"], 0, key or text)


def H2(text: str, key: str | None = None) -> "TOCHeading":
    return TOCHeading(text, S["h2"], 1, key or text)


def H3(text: str, key: str | None = None) -> "TOCHeading":
    return TOCHeading(text, S["h3"], 2, key or text)


def B(text: str) -> Paragraph:
    return Paragraph(text, S["bullet"], bulletText="•")


def N(text: str, number: int) -> Paragraph:
    return Paragraph(text, S["num"], bulletText=f"{number}.")


def CALLOUT(text: str, kind: str = "info") -> Table:
    bg = {
        "info": BLUE_LIGHT,
        "warn": AMBER_LIGHT,
        "key": GREEN_LIGHT,
        "risk": RED_LIGHT,
    }[kind]
    bar = {"info": BLUE, "warn": AMBER, "key": GREEN, "risk": RED}[kind]
    t = Table([[Paragraph(text, S["callout"])]], colWidths=[CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3.2, bar),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return t


def table(
    rows: list[list],
    widths: list[float],
    header: bool = True,
    aligns: list[str] | None = None,
    zebra: bool = True,
    font_size: float | None = None,
    pad: float = 4,
) -> Table:
    data = []
    for r, row in enumerate(rows):
        out = []
        for c, cell in enumerate(row):
            if isinstance(cell, Flowable):
                out.append(cell)
            else:
                if header and r == 0:
                    st = S["head_center"] if (aligns and aligns[c] == "center") else S["head"]
                else:
                    st = S["cell_center"] if (aligns and aligns[c] == "center") else S["cell"]
                if font_size:
                    st = ParagraphStyle(
                        "tmp", parent=st, fontSize=font_size, leading=font_size * 1.3
                    )
                out.append(Paragraph(str(cell), st))
        data.append(out)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7dee5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), GREEN_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ]
    if zebra:
        start = 1 if header else 0
        for i in range(start, len(rows)):
            if (i - start) % 2 == 1:
                cmds.append(("BACKGROUND", (0, i), (-1, i), GREY_LIGHT))
    t.setStyle(TableStyle(cmds))
    return t


def CAPTION(text: str) -> Paragraph:
    return Paragraph(text, S["caption"])


def figure(path: str, width: float, caption: str) -> KeepTogether:
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        w, h = im.size
    img = Image(path, width=width, height=width * h / w)
    img.hAlign = "CENTER"
    return KeepTogether([img, CAPTION(caption)])


class TOCHeading(Paragraph):
    def __init__(
        self, text: str, style: ParagraphStyle, level: int = 0, key: str | None = None
    ):
        self._toc_level = level
        self._toc_key = key or text
        super().__init__(text, style)

    def draw(self):
        super().draw()
        key = self._toc_key
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(self.getPlainText(), key, self._toc_level, False)
        doc = getattr(self.canv, "_doctemplate", None)
        if doc is not None:
            doc.notify(
                "TOCEntry",
                (self._toc_level, self.getPlainText(), self.canv.getPageNumber(), key),
            )


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_footer(self, total: int):
        page = self._pageNumber
        if page == 1:
            return
        self.saveState()
        self.setStrokeColor(GREY_MID)
        self.setLineWidth(0.5)
        self.line(LM, 1.42 * cm, PAGE_W - RM, 1.42 * cm)
        self.setFont("Arial", 7.5)
        self.setFillColor(GREY)
        self.drawString(
            LM,
            1.02 * cm,
            "ProHuerta Chascomús · Informe para el equipo del Banco de Semillas",
        )
        self.drawRightString(PAGE_W - RM, 1.02 * cm, f"Página {page} de {total}")
        self.restoreState()


def on_first_page(canv, doc):
    pass


def on_later_pages(canv, doc):
    canv.saveState()
    canv.setFont("Arial", 7.4)
    canv.setFillColor(GREY)
    canv.drawString(
        LM,
        PAGE_H - 1.24 * cm,
        "ProHuerta Chascomús · Informe para el equipo del Banco de Semillas",
    )
    canv.drawRightString(
        PAGE_W - RM,
        PAGE_H - 1.24 * cm,
        "Documento de lectura para usuarios y referentes territoriales",
    )
    canv.setStrokeColor(GREY_MID)
    canv.setLineWidth(0.5)
    canv.line(LM, PAGE_H - 1.45 * cm, PAGE_W - RM, PAGE_H - 1.45 * cm)
    canv.restoreState()


def KPI_ROW(items: list[tuple[str, str]]) -> Table:
    widths = [CONTENT_W / len(items)] * len(items)
    top = [Paragraph(v, S["kpi_num"]) for v, _ in items]
    bottom = [Paragraph(l, S["kpi_label"]) for _, l in items]
    t = Table([top, bottom], colWidths=widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GREEN_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cfe5d7")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9e9df")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def FLOW(steps: list[str], color: colors.Color = GREEN_DARK) -> Table:
    cells = []
    widths = []
    for i, step in enumerate(steps):
        cells.append(
            Paragraph(
                step,
                ParagraphStyle(
                    "flowcell",
                    fontName="Arial-Bold",
                    fontSize=7.8,
                    leading=9.8,
                    textColor=WHITE,
                    alignment=TA_CENTER,
                ),
            )
        )
        widths.append((CONTENT_W - (len(steps) - 1) * 0.55 * cm) / len(steps))
        if i < len(steps) - 1:
            cells.append(
                Paragraph(
                    "→",
                    ParagraphStyle(
                        "arrow",
                        fontName="Arial-Bold",
                        fontSize=12,
                        leading=14,
                        textColor=color,
                        alignment=TA_CENTER,
                    ),
                )
            )
            widths.append(0.55 * cm)
    t = Table([cells], colWidths=widths)
    cmds = [("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i in range(0, len(cells), 2):
        cmds += [
            ("BACKGROUND", (i, 0), (i, 0), color),
            ("LEFTPADDING", (i, 0), (i, 0), 4),
            ("RIGHTPADDING", (i, 0), (i, 0), 4),
            ("TOPPADDING", (i, 0), (i, 0), 7),
            ("BOTTOMPADDING", (i, 0), (i, 0), 7),
            ("BOX", (i, 0), (i, 0), 0.4, color),
        ]
    t.setStyle(TableStyle(cmds))
    return t


def cover() -> list:
    story = []
    story.append(Spacer(1, 0.35 * cm))
    story.append(
        Paragraph(
            "INSTITUTO SUPERIOR DE FORMACIÓN DOCENTE Y TÉCNICA N.º 57",
            ParagraphStyle(
                "cov_inst",
                fontName="Arial-Bold",
                fontSize=9.2,
                leading=12.5,
                textColor=GREEN_DARK,
                alignment=TA_CENTER,
                spaceAfter=2,
            ),
        )
    )
    story.append(
        Paragraph(
            "Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial · Grupo 3",
            ParagraphStyle(
                "cov_carrera",
                fontName="Arial",
                fontSize=9,
                leading=12,
                textColor=GREY,
                alignment=TA_CENTER,
                spaceAfter=10,
            ),
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=2.8, color=GREEN, spaceBefore=0, spaceAfter=16)
    )
    story.append(
        Paragraph(
            "INFORME PARA EL EQUIPO DEL BANCO DE SEMILLAS",
            ParagraphStyle(
                "cov_kicker",
                fontName="Arial-Bold",
                fontSize=8.8,
                leading=11.5,
                textColor=GREEN,
                alignment=TA_CENTER,
                spaceAfter=6,
            ),
        )
    )
    story.append(
        Paragraph(
            "Prever la demanda de semillas<br/>para planificar mejores entregas",
            ParagraphStyle(
                "cov_title",
                fontName="Arial-Bold",
                fontSize=21.5,
                leading=26,
                textColor=GREEN_DARK,
                alignment=TA_CENTER,
                spaceAfter=8,
            ),
        )
    )
    story.append(
        Paragraph(
            "Cómo funciona el sistema ProHuerta Chascomús<br/>y qué nos enseñaron los datos",
            ParagraphStyle(
                "cov_sub",
                fontName="Arial",
                fontSize=12.2,
                leading=16,
                textColor=GREY,
                alignment=TA_CENTER,
                spaceAfter=4,
            ),
        )
    )
    story.append(
        Paragraph(
            "Documento de lectura para usuarios, coordinadores y referentes territoriales",
            ParagraphStyle(
                "cov_sub2",
                fontName="Arial-Italic",
                fontSize=10.2,
                leading=13.5,
                textColor=BLUE,
                alignment=TA_CENTER,
                spaceAfter=14,
            ),
        )
    )

    if COVER_IMG.exists():
        img = Image(str(COVER_IMG), width=15.4 * cm, height=15.4 * cm * 900 / 1600)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(
            Paragraph(
                "Huerta comunitaria. Imagen de referencia del proyecto ProHuerta Chascomús.",
                S["caption"],
            )
        )

    meta = [
        ["Preparado para", "Equipo coordinador del Banco de Intercambio de Semillas de Chascomús"],
        ["Elaborado por", "Barreu, Lucas · Quiroga, Franco · Pérez Cazal, Marcelo"],
        ["Fecha de elaboración", "Noviembre de 2026"],
        ["Versión", "1.0 · Documento para el cliente"],
        ["Datos analizados", "2.730 solicitudes · campañas 2022–2026"],
        ["Aplicación web", "https://pro-huerta.vercel.app/"],
    ]
    t = Table(
        [
            [Paragraph(f"<b>{a}</b>", S["cell"]), Paragraph(b, S["cell"])]
            for a, b in meta
        ],
        colWidths=[4.2 * cm, 10.6 * cm],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GREEN_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cfe5d7")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d9e9df")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    t.hAlign = "CENTER"
    story.append(t)
    story.append(Spacer(1, 0.35 * cm))
    story.append(
        Paragraph(
            "Trabajo Práctico Integrador · Modelos de Aprendizaje Automático · Instituto N.º 57",
            ParagraphStyle(
                "cov_foot",
                fontName="Arial",
                fontSize=8,
                leading=10,
                textColor=GREY,
                alignment=TA_CENTER,
            ),
        )
    )
    story.append(NextPageTemplate("main"))
    story.append(PageBreak())
    return story


def executive_summary() -> list:
    story = [H1("En pocas palabras", "resumen")]
    story.append(
        P(
            "El Banco de Semillas de ProHuerta Chascomús entrega kits sin saber de antemano cuántas "
            "variedades va a pedir cada persona. Preparar de más inmoviliza sobres que podrían usarse "
            "en otra huerta; preparar de menos deja a familias sin algunas variedades y obliga a "
            "resolver faltantes en el momento de la entrega. El sistema que desarrollamos convierte "
            "los formularios históricos en información útil para anticipar esa demanda y organizar "
            "mejor el armado de kits."
        )
    )
    story.append(
        P(
            "No se trata de adivinar el pedido exacto de una familia. Se trata de <b>estimar la demanda "
            "agregada por barrio y temporada</b>, detectar dónde puede aparecer una sobredemanda y "
            "ofrecer escenarios para decidir con más información. La aplicación reúne un mapa "
            "territorial, un simulador de stock, un módulo climático y un informe de datos."
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(
        KPI_ROW(
            [
                (f"{CTX['total']:,}".replace(",", "."), "solicitudes históricas"),
                (f"{CTX['modeladas']:,}".replace(",", "."), "solicitudes modeladas"),
                (f"{CTX['barrios_geo']}", "barrios en el mapa"),
                ("2027–2028", "escenarios proyectados"),
            ]
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        P(
            f"<b>Lo más importante.</b> La demanda no es pareja: un grupo pequeño de variedades "
            f"concentra la mayor parte de los pedidos y cambia según la temporada. Además, "
            f"<b>{CTX['alta_demanda_pct']:.0f} de cada 100 solicitudes</b> de la etapa con registro "
            f"detallado pidieron el 75% o más del catálogo. Eso significa que, en muchos casos, "
            f"conviene tener preparado un kit casi completo antes de que la persona llegue al mostrador."
        )
    )
    story.append(
        CALLOUT(
            "<b>La idea central.</b> El sistema es una brújula para la planificación, no un piloto "
            "automático. Ayuda a priorizar barrios, estimar cantidades y preparar stock; la decisión "
            "final sigue siendo del equipo del Banco de Semillas. Las proyecciones 2027–2028 son "
            "escenarios construidos con supuestos, no pronósticos validados.",
            "key",
        )
    )
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        P(
            "<b>Qué vas a encontrar en este informe.</b> Primero, el problema y la propuesta. Luego, "
            "lo que muestran los datos originales y las decisiones que tomamos a partir de ellos. "
            "Después, un recorrido por las seis pantallas de la aplicación, los análisis más "
            "relevantes, los límites del sistema y las recomendaciones para usarlo con criterio.",
            "body",
        )
    )
    story.append(PageBreak())
    return story


def toc() -> list:
    story = [Paragraph("Contenido", S["toc_title"])]
    t = TableOfContents()
    t.levelStyles = [
        ParagraphStyle(
            "toc0",
            fontName="Arial-Bold",
            fontSize=10.2,
            leading=16,
            textColor=GREEN_DARK,
            leftIndent=0,
            firstLineIndent=0,
        ),
        ParagraphStyle(
            "toc1",
            fontName="Arial",
            fontSize=9.2,
            leading=13.8,
            textColor=colors.HexColor("#334155"),
            leftIndent=14,
            firstLineIndent=0,
        ),
    ]
    t.tableStyle = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]
    )
    story.append(t)
    story.append(PageBreak())
    return story


def section_problem() -> list:
    story = [H1("1. El problema y la propuesta", "problema")]
    story.append(
        P(
            "Cada temporada, el Banco de Semillas recibe solicitudes de huertas familiares, escolares, "
            "comunitarias e institucionales. Cada persona elige variedades según su experiencia, el "
            "espacio disponible, el destino de la producción y el barrio donde vive. Esa diversidad "
            "hace que el armado de kits sea difícil de planificar: no todos piden lo mismo ni en la "
            "misma cantidad."
        )
    )
    story.append(
        P(
            "El equipo logístico debe decidir, antes de la entrega, si prepara <b>kits completos</b> "
            "o <b>kits básicos estandarizados</b>. Si prepara de más, inmoviliza insumos limitados. "
            "Si prepara de menos, faltan variedades en el mostrador, se afecta la diversidad de la "
            "huerta y la experiencia de las familias. El problema, en el fondo, es de "
            "<b>planificación bajo incertidumbre</b>."
        )
    )
    story.append(H2("1.1. Qué hace el sistema", "problema-hace"))
    story.append(
        P(
            "La aplicación analiza las solicitudes históricas y estima cuántos sobres equivalentes "
            "se pedirán en cada barrio y temporada. Un <b>sobre equivalente</b> representa una variedad "
            "solicitada: si una persona pide ocho variedades, son ocho sobres equivalentes. A partir "
            "de esa estimación, el sistema:"
        )
    )
    story.append(B("Proyecta la demanda por barrio y la compara con el histórico."))
    story.append(B("Marca los barrios donde se espera una sobredemanda."))
    story.append(B("Simula el stock necesario para un perfil de huerta."))
    story.append(B("Estima cómo puede influir el nivel de lluvias en la cobertura del catálogo."))
    story.append(B("Documenta datos, supuestos y limitaciones para que las decisiones sean trazables."))
    story.append(H2("1.2. Qué no hace el sistema", "problema-no-hace"))
    story.append(
        CALLOUT(
            "<b>No predice el pedido exacto de una familia.</b> Tampoco decide a quién entregar "
            "semillas ni reemplaza el criterio del equipo. Su unidad de planificación es el barrio y "
            "la temporada; su unidad de análisis es la solicitud. La estimación individual es una "
            "referencia, no una certeza.",
            "warn",
        )
    )
    story.append(Spacer(1, 0.18 * cm))
    story.append(
        P(
            "Este límite es deliberado. El sistema se diseñó como una herramienta de apoyo a la "
            "decisión: muestra tendencias, prioridades y escenarios para que el equipo pueda discutir "
            "y decidir mejor. No automatiza la asignación de insumos ni promete adivinar el futuro."
        )
    )
    story.append(H2("1.3. Cómo se lee este documento", "problema-lectura"))
    story.append(
        P(
            "El informe está escrito para personas que conocen el Banco de Semillas y su trabajo "
            "cotidiano, no necesariamente la tecnología. Los términos técnicos se explican en el "
            "glosario del final. Las cifras provienen de los formularios históricos y de los "
            "documentos de auditoría del proyecto; cuando hay un supuesto, se indica explícitamente."
        )
    )
    story.append(PageBreak())
    return story


def section_data() -> list:
    story = [H1("2. Lo que muestran los datos originales", "datos")]
    story.append(
        P(
            "Trabajamos con <b>2.730 solicitudes</b> registradas en siete campañas entre 2022 y 2026. "
            "La base no es homogénea: los formularios cambiaron con los años y eso obligó a tomar "
            "decisiones metodológicas. Esta sección resume qué encontramos y por qué importa."
        )
    )
    story.append(H2("2.1. Siete campañas, dos formas de registrar", "datos-campanas"))
    story.append(
        P(
            "Entre 2022 y 2023 se entregaba un <b>kit genérico de diez especies surtidas</b>. El "
            "formulario no detallaba qué variedades elegía cada persona. A partir de 2024, en cambio, "
            "se registra la <b>selección específica de variedades</b>. Esa diferencia es central: "
            "solo la etapa 2024–2026 permite observar la demanda real de cada solicitud."
        )
    )
    rows = [["Campaña", "Solicitudes", "Tipo de registro", "Sobres equivalentes promedio"]]
    for c in CTX["campanas"]:
        rows.append(
            [
                f"{c['temporada']} {c['anio']}",
                f"{c['n']:,}".replace(",", "."),
                "Kit genérico" if c["esquema"] == "kit_generico" else "Selección específica",
                fmt_dec(c["equiv"]),
            ]
        )
    story.append(
        table(
            rows,
            [2.9 * cm, 2.8 * cm, 5.2 * cm, 6.0 * cm],
            aligns=["left", "center", "left", "center"],
        )
    )
    story.append(
        CAPTION(
            "Tabla 1. Solicitudes por campaña. Los kits genéricos se contabilizan de otra manera y no "
            "se comparan directamente con la etapa específica."
        )
    )
    story.append(figure(CHART_CAMPANAS, 16.2 * cm, "Figura 1. Evolución del volumen de solicitudes registradas por campaña."))
    story.append(
        P(
            "El volumen de registros no crece de forma constante: depende de la campaña, de la "
            "difusión del programa y de los formularios utilizados. Por eso el sistema no trabaja "
            "con un único promedio general, sino con <b>referencias por barrio y temporada</b>."
        )
    )

    story.append(H2("2.2. La demanda se concentra en pocas variedades", "datos-especies"))
    story.append(
        P(
            "No todas las variedades se piden por igual. En Otoño–Invierno, el perejil, la acelga y "
            "la lechuga aparecen en más del 80% de las solicitudes. En Primavera–Verano el podio "
            "cambia: el tomate, la lechuga y la albahaca lideran. Esta rotación estacional es una de "
            "las razones por las que el sistema distingue OI de PV en todos sus cálculos."
        )
    )
    story.append(figure(CHART_ESPECIES, 16.2 * cm, "Figura 2. Variedades más pedidas en cada temporada, como porcentaje de solicitudes."))
    story.append(
        P(
            "Una consecuencia práctica es que la <b>canasta básica</b> de cada temporada no es la "
            "misma. Preparar un kit de OI con las variedades más pedidas en PV sería una mala "
            "aproximación. El sistema aprende de cada temporada por separado y muestra las especies "
            "más solicitadas en el detalle de cada barrio."
        )
    )

    story.append(H2("2.3. El catálogo creció y cambió la forma de medir", "datos-catalogo"))
    story.append(
        P(
            "La oferta de variedades pasó de <b>9</b> en Primavera–Verano 2024 a <b>18</b> en "
            "Primavera–Verano 2026. Ese crecimiento tiene una consecuencia importante: la misma "
            "cantidad de sobres puede representar una <b>cobertura menor</b> del catálogo. Por eso el "
            "sistema no mide solo cuántas variedades pide una persona, sino qué porcentaje del "
            "catálogo disponible representa esa elección."
        )
    )
    rows = [["Campaña", "Variedades ofrecidas", "75% del catálogo equivale a"]]
    for c in CTX["catalogo"]:
        if c["anio"] >= 2024:
            rows.append(
                [
                    f"{c['temporada']} {c['anio']}",
                    str(c["oferta"]),
                    f"{round(c['oferta'] * 0.75)} variedades",
                ]
            )
    story.append(table(rows, [4.0 * cm, 5.2 * cm, 7.7 * cm], aligns=["left", "center", "center"]))
    story.append(
        CAPTION(
            "Tabla 2. Crecimiento del catálogo en la etapa con registro específico. El umbral del 75% "
            "se vuelve más exigente a medida que crece la oferta."
        )
    )
    story.append(
        P(
            "Entre 2024 y 2026, la cantidad media de variedades pedidas subió de <b>5,6</b> a "
            "<b>10,2</b>. Sin embargo, el catálogo creció todavía más rápido. Por eso la cobertura "
            "media bajó en 2026: no necesariamente porque la gente pidiera menos, sino porque había "
            "más opciones disponibles. Esta es una lectura clave para no confundir <b>cantidad</b> "
            "con <b>cobertura</b>."
        )
    )

    story.append(H2("2.4. El perfil de la huerta ayuda, pero no alcanza", "datos-perfil"))
    story.append(
        P(
            "Los formularios registran características de la huerta: localización, tipo, experiencia, "
            "superficie, destino de la producción y ocupación. Algunas marcan diferencias claras. "
            "Las huertas <b>rurales</b> y <b>periurbanas</b> suelen pedir más variedades que las "
            "urbanas; quienes producen para <b>intercambio</b> también muestran una cobertura más "
            "alta que quienes producen solo para autoconsumo. La superficie también importa: las "
            "huertas de más de 20 m² tienen, en promedio, una cobertura mayor."
        )
    )
    story.append(figure(CHART_PERFILES, 16.2 * cm, "Figura 3. Cobertura media según localización, destino y superficie de la huerta."))
    story.append(
        P(
            "En cambio, el <b>tipo de huerta</b> (familiar o institucional) y la <b>experiencia</b> "
            "previa muestran diferencias más pequeñas. Esto no significa que no importen, sino que "
            "por sí solos no alcanzan para anticipar la demanda. El modelo combina varias señales y "
            "además incorpora el histórico del barrio."
        )
    )

    story.append(H2("2.5. El territorio importa", "datos-territorio"))
    story.append(
        P(
            f"De las solicitudes con barrio registrado, casi <b>4 de cada 10</b> se concentran en "
            f"cinco barrios: Centro, El Hueco, San Cayetano, Noria Chica e Ipora. El mapa de la "
            f"aplicación trabaja con <b>{CTX['barrios_geo']} barrios</b> que tienen representación "
            f"geográfica. Esa mirada territorial permite priorizar recorridos, entregas y refuerzos "
            f"de stock."
        )
    )
    story.append(figure(CHART_BARRIOS, 16.2 * cm, "Figura 4. Barrios con más solicitudes registradas en toda la serie histórica."))
    story.append(
        CALLOUT(
            f"<b>Un dato que condiciona el mapa.</b> Hay <b>{fmt_int(CTX['sin_barrio'])}</b> solicitudes "
            f"({CTX['sin_barrio_pct']:.0f}% del total) sin barrio registrado, sobre todo en 2024 y "
            f"en Otoño–Invierno 2025, porque esos formularios no incluían la pregunta. El mapa "
            f"proyecta solo los barrios mapeados con datos; el total municipal observado incluye "
            f"también esos registros sin barrio.",
            "warn",
        )
    )

    story.append(H2("2.6. Qué encontramos en los formularios", "datos-calidad"))
    story.append(
        P(
            "No se eliminó ninguna fila. Los problemas de calidad se documentaron con banderas para "
            "que puedan auditarse. Los controles principales fueron:"
        )
    )
    rows = [
        ["Control", "Resultado"],
        ["Solicitudes totales validadas", f"{CTX['total']:,}".replace(",", ".")],
        ["Solicitudes con selección específica (2024–2026)", f"{CTX['especificas']:,}".replace(",", ".")],
        ["Solicitudes utilizables para el modelo de variedades", f"{CTX['modeladas']:,}".replace(",", ".")],
        ["Registros 2022–2023 sin dato explícito de kits", "193"],
        ["Registros 2024–2026 sin texto de especies", "5"],
        ["Solicitudes sin barrio asignado", f"{CTX['sin_barrio']:,}".replace(",", ".")],
        ["Solicitudes con coordenadas geográficas", f"{CTX['con_coords']:,}".replace(",", ".")],
    ]
    story.append(table(rows, [12.0 * cm, 4.6 * cm], aligns=["left", "center"]))
    story.append(
        CAPTION(
            "Tabla 3. Controles de calidad del dataset consolidado. Los registros problemáticos se "
            "conservan y se marcan para auditoría."
        )
    )
    story.append(
        P(
            "Esta forma de trabajar es importante para la transparencia: en lugar de borrar los casos "
            "difíciles, el sistema los conserva y advierte cuándo una lectura puede ser menos "
            "confiable. Así, el equipo puede saber qué parte de la información está completa y qué "
            "parte requiere cautela."
        )
    )
    story.append(PageBreak())
    return story


def section_decisions() -> list:
    story = [H1("3. Decisiones tomadas a partir de los datos", "decisiones")]
    story.append(
        P(
            "Los datos no solo sirvieron para entrenar un modelo. También obligaron a tomar decisiones "
            "sobre qué medir, qué comparar y cómo comunicar los resultados. Estas son las decisiones "
            "principales y su impacto en la aplicación."
        )
    )
    rows = [
        ["Lo que vimos en los datos", "Lo que decidimos", "Por qué", "Dónde se ve"],
        [
            "2022–2023 no registran variedades, solo cantidad de kits.",
            "Entrenar el modelo de variedades solo con 2024–2026 (1.487 solicitudes).",
            "Evitar inventar una composición que el formulario no registró.",
            "Mapa y control de stock.",
        ],
        [
            "El catálogo pasó de 9 a 18 variedades.",
            "Medir la demanda como cobertura porcentual del catálogo.",
            "Permitir comparaciones entre temporadas con distinta oferta.",
            "Cobertura y alertas.",
        ],
        [
            "El 75% del catálogo equivale a 3 de cada 4 variedades.",
            "Definir alta demanda cuando la cobertura llega al 75%.",
            "Es el punto operativo para decidir si conviene armar un kit completo.",
            "Control de stock.",
        ],
        [
            "Quedarse corto es más costoso que preparar de más.",
            "Priorizar la detección de alta demanda aunque haya avisos de más.",
            "Un falso negativo cuesta el doble que un falso positivo.",
            "Doble alerta y recomendación.",
        ],
        [
            "La demanda individual es difícil de predecir.",
            "Planificar por barrio y temporada, no por familia.",
            "Al sumar muchas solicitudes, los errores se compensan.",
            "Mapa y textos de advertencia.",
        ],
        [
            "Los barrios pequeños pueden dar variaciones engañosas.",
            "Activar alerta territorial solo con +10% y +10 sobres.",
            "Evitar falsas alarmas por variaciones porcentuales sobre bases mínimas.",
            "Mapa de demanda.",
        ],
        [
            "La oferta de catálogo está relacionada con la cobertura.",
            "Entrenar el modelo climático solo con milímetros de lluvia.",
            "Evitar que el modelo use una variable que no estará disponible al planificar.",
            "Análisis climático.",
        ],
        [
            "Los formularios tienen datos faltantes y cambios de formato.",
            "Conservar todas las filas y marcar la calidad con banderas.",
            "Permitir auditoría y no ocultar limitaciones.",
            "Informe de datos.",
        ],
    ]
    story.append(
        table(
            rows,
            [4.1 * cm, 4.4 * cm, 4.2 * cm, 3.4 * cm],
            aligns=["left", "left", "left", "left"],
            font_size=7.5,
            pad=4,
        )
    )
    story.append(
        CAPTION(
            "Tabla 4. Principales decisiones metodológicas y su relación con la aplicación."
        )
    )

    story.append(H2("3.1. Entrenar solo con lo que está completo", "decisiones-entrenar"))
    story.append(
        P(
            "Los formularios de 2022 y 2023 no detallan variedades. Si los hubiéramos usado para "
            "entrenar el modelo de variedades, habríamos tenido que inventar una composición. Por eso "
            "el modelo principal se entrenó con las <b>1.487 solicitudes específicas</b> de 2024–2026 "
            "que tienen especies observadas. Los registros anteriores se conservaron para analizar "
            "volumen y presupuesto, pero no para aprender qué variedades pide la gente."
        )
    )
    story.append(
        CALLOUT(
            "<b>Por qué importa.</b> Un modelo entrenado con datos imputados habría aprendido de "
            "suposiciones, no de la realidad. Preferimos un modelo con menos datos, pero con datos "
            "observados y auditables.",
            "info",
        )
    )

    story.append(H2("3.2. Medir en porcentaje, no solo en cantidad", "decisiones-cobertura"))
    story.append(
        P(
            "Cuando el catálogo crece, pedir diez variedades puede significar cosas muy distintas: "
            "en un catálogo de nueve, es casi todo; en uno de dieciocho, es un poco más de la mitad. "
            "Por eso la aplicación mide la <b>cobertura del catálogo</b>: el porcentaje de variedades "
            "disponibles que solicita una persona. Esto permite comparar temporadas con distinta "
            "oferta y evita conclusiones equivocadas."
        )
    )

    story.append(H2("3.3. Definir alta demanda en 75%", "decisiones-umbral"))
    story.append(
        P(
            "El umbral del <b>75%</b> significa que una persona pide al menos tres de cada cuatro "
            "variedades del catálogo. Es un punto operativo: a partir de ahí conviene preparar un kit "
            "casi completo por adelantado. En la etapa específica, <b>608 de 1.487 solicitudes</b> "
            f"({fmt_dec(CTX['alta_demanda_pct'])}%) alcanzaron ese umbral. No es una regla natural ni "
            "definitiva: es una decisión de gestión que puede revisarse con el equipo."
        )
    )
    story.append(
        P(
            "El umbral también explica parte de la caída de 2026: con 17 variedades en OI, el 75% "
            "equivale a 13 variedades; con 9, equivalía a 7. La misma persona podía pedir más "
            "variedades y, aun así, quedar por debajo del umbral porque el catálogo había crecido."
        )
    )

    story.append(H2("3.4. Preferir avisar de más", "decisiones-costos"))
    story.append(
        P(
            "En la planificación logística, los errores no cuestan lo mismo. Un <b>falso positivo</b> "
            "es preparar un kit completo para alguien que finalmente pide menos: inmoviliza stock, "
            "pero los sobres pueden reasignarse. Un <b>falso negativo</b> es no preparar el kit y "
            "dejar a una familia sin variedades: afecta la diversidad de la huerta y la experiencia "
            "del programa. Por eso asignamos un costo de <b>1</b> al falso positivo y <b>2</b> al "
            "falso negativo, y ajustamos el sistema para detectar la mayor cantidad posible de casos "
            "de alta demanda."
        )
    )
    story.append(
        P(
            "En términos prácticos, el sistema detecta aproximadamente <b>88 de cada 100</b> "
            "solicitudes que realmente necesitaban un kit completo. A cambio, genera avisos de más: "
            "cerca de la mitad de las alertas corresponden a casos que finalmente no eran de alta "
            "demanda. Es una decisión deliberada: preferimos que sobre stock reasignable a que falte "
            "en el mostrador."
        )
    )
    story.append(
        CALLOUT(
            "<b>Cómo usarlo.</b> Si el sistema marca alta demanda, no significa que esa familia "
            "seguro pedirá todo. Significa que, con la información disponible, es prudente tener "
            "preparado un kit completo. La decisión final sigue siendo del equipo.",
            "key",
        )
    )

    story.append(H2("3.5. Planificar por barrio y temporada, no por familia", "decisiones-agregado"))
    story.append(
        P(
            "El modelo individual tiene un error típico de <b>2,6 sobres</b> sobre un pedido promedio "
            "de <b>7,7</b>. Es decir, no es suficientemente preciso para decidir el kit exacto de una "
            "persona. Pero cuando se suman muchas solicitudes por barrio y temporada, los errores "
            "tienden a compensarse y la estimación agregada resulta más estable. Por eso el producto "
            "se diseñó para <b>planificación territorial</b>, no para asignación individual."
        )
    )
    story.append(
        P(
            "La aplicación lo dice explícitamente en varias pantallas: las estimaciones sirven para "
            "planificar en forma agregada y las proyecciones 2027–2028 son escenarios base, no "
            "pronósticos validados."
        )
    )

    story.append(H2("3.6. Dos alertas mejor que una", "decisiones-doble"))
    story.append(
        P(
            "El control de stock muestra dos sistemas independientes. Uno estima el porcentaje de "
            "cobertura y aplica el umbral del 75%; el otro clasifica directamente si la solicitud es "
            "de alta demanda. Cuando ambos coinciden, la decisión es más confiable. Cuando discrepan, "
            "la aplicación recomienda preparar el kit completo, porque el costo de quedarse corto es "
            "mayor. Esta doble lectura ayuda a detectar casos cercanos al umbral y a evitar decisiones "
            "automáticas sobre situaciones dudosas."
        )
    )

    story.append(H2("3.7. Una alerta territorial con dos condiciones", "decisiones-territorial"))
    story.append(
        P(
            "En el mapa, un barrio no se marca en alerta solo porque su demanda proyectada sea algo "
            "mayor que la histórica. Se exigen dos condiciones simultáneas: que la proyección supere "
            "el baseline en al menos <b>10%</b> y que la diferencia sea de al menos <b>10 sobres</b>. "
            "El doble criterio evita falsas alarmas en barrios pequeños, donde una variación "
            "porcentual grande puede originarse en una base mínima."
        )
    )
    story.append(
        P(
            "Además, los barrios con menos de <b>10 solicitudes históricas</b> o menos de <b>2 años "
            "de datos</b> se marcan como <b>muestra limitada</b>. En esos casos la alerta se acompaña "
            "de una advertencia de cautela."
        )
    )

    story.append(H2("3.8. Un modelo climático aparte y sin trampas", "decisiones-clima"))
    story.append(
        P(
            "El módulo climático estima cómo varía la cobertura según las precipitaciones. En una "
            "versión preliminar, el modelo usaba también el tamaño del catálogo; eso era una trampa, "
            "porque la oferta está matemáticamente relacionada con la cobertura y no siempre se conoce "
            "de antemano. El modelo final se reentrenó usando <b>solo milímetros de lluvia</b>. El "
            "resultado indica que cada <b>100 mm adicionales</b> se asocian con un aumento de "
            "aproximadamente <b>1,3 puntos porcentuales</b> en la cobertura estimada."
        )
    )
    story.append(figure(CHART_CLIMA, 16.0 * cm, "Figura 5. Relación estimada entre precipitaciones y cobertura del catálogo."))
    story.append(
        P(
            "La influencia es leve: el clima acompaña la planificación, pero no alcanza para explicar "
            "por sí solo la demanda. Por eso el módulo se presenta como un complemento y no como el "
            "factor principal de decisión."
        )
    )

    story.append(H2("3.9. Cuidar los datos y no borrar evidencia", "decisiones-privacidad"))
    story.append(
        P(
            "El sistema no muestra datos personales: el mapa trabaja con totales por barrio y el "
            "simulador de stock no pide nombre, teléfono ni dirección. Para el modelado se excluyeron "
            "datos personales directos y la localidad, porque casi todas las solicitudes corresponden "
            "a Chascomús y esa variable no aportaba información útil. Además, no se eliminaron filas: "
            "los problemas se marcaron con banderas para que puedan auditarse."
        )
    )
    story.append(PageBreak())
    return story


def section_app() -> list:
    story = [H1("4. Cómo funciona la aplicación", "app")]
    story.append(
        P(
            "La aplicación es una página web que se abre desde el navegador, sin instalar nada. "
            "Los modelos ya están entrenados y cargados: la aplicación no aprende en tiempo real, "
            "sino que usa lo aprendido en las campañas históricas para hacer estimaciones en "
            "milisegundos. Cuando se suman nuevas campañas, los modelos se reentrenan y se actualiza "
            "la aplicación."
        )
    )
    story.append(
        FLOW(
            [
                "Datos históricos<br/>2022–2026",
                "Aprendizaje<br/>de patrones",
                "Proyección<br/>por barrio",
                "Mapa y alertas<br/>para decidir",
                "Armado de kits<br/>y presupuesto",
            ]
        )
    )
    story.append(
        CAPTION(
            "Figura 6. Recorrido general: de los formularios históricos a la decisión logística."
        )
    )
    story.append(H2("4.1. En palabras simples, cómo aprende", "app-aprende"))
    story.append(
        P(
            "Para estimar cuántos sobres puede pedir una solicitud, el sistema busca las <b>41 "
            "solicitudes históricas más parecidas</b> —por temporada, tipo de huerta, localización, "
            "experiencia, superficie, destino, ocupación y barrio— y usa su promedio. Es como "
            "consultar a un grupo de vecinos con huertas similares antes de decidir cuánto stock "
            "preparar."
        )
    )
    story.append(
        P(
            "Para la alerta de alta demanda, usa un <b>árbol de preguntas</b>: combina condiciones "
            "sobre el perfil y el histórico para decidir si conviene preparar un kit completo. Para "
            "el clima, usa una <b>recta</b> que relaciona milímetros de lluvia con cobertura estimada. "
            "Ninguno de estos mecanismos es una bola de cristal: son formas de ordenar la evidencia "
            "disponible."
        )
    )
    story.append(H2("4.2. Las seis pantallas", "app-pantallas"))
    rows = [
        ["Pantalla", "Qué muestra", "Para qué sirve"],
        ["Portada", "Presentación del proyecto, objetivos y acceso al sistema.", "Conocer la iniciativa e ingresar."],
        ["Inicio", "Cifras generales, herramientas y pasos de uso.", "Tener una vista rápida y elegir por dónde empezar."],
        ["Mapa de demanda", "Mapa 3D por barrio, comparación con el histórico, alertas, prioridades y tendencias.", "Decidir dónde reforzar stock y qué barrios mirar primero."],
        ["Control de stock", "Simulación por perfil de huerta, cobertura estimada y dos alertas.", "Decidir si conviene preparar un kit completo o uno básico."],
        ["Análisis climático", "Estimación de cobertura según lluvias y contexto hídrico.", "Anticipar escenarios de sequía o lluvias intensas."],
        ["Informe de datos", "Documentación, variables, métricas y limitaciones.", "Entender de dónde salen las estimaciones y cómo interpretarlas."],
    ]
    story.append(
        table(
            rows,
            [3.0 * cm, 7.7 * cm, 6.0 * cm],
            aligns=["left", "left", "left"],
            font_size=7.9,
            pad=4,
        )
    )
    story.append(CAPTION("Tabla 5. Las seis pantallas principales de la aplicación."))

    story.append(H3("Portada"))
    story.append(
        P(
            "Es la primera pantalla. Presenta el proyecto, su relación con la comunidad y los "
            "objetivos. Desde aquí se ingresa al sistema. No requiere conocimientos técnicos."
        )
    )
    story.append(H3("Inicio"))
    story.append(
        P(
            "Muestra las cifras generales del proyecto —solicitudes registradas, solicitudes "
            "modeladas, barrios mapeados y horizonte de proyección— y explica en cuatro pasos cómo "
            "funciona el sistema: datos, modelo, agregación y alerta. También advierte que las "
            "estimaciones sirven para planificar en forma agregada."
        )
    )
    story.append(H3("Mapa de demanda"))
    story.append(
        P(
            "Es la pantalla más visual. Permite elegir temporada, año, variable (sobres, solicitudes "
            "o presupuesto) y barrio. El mapa muestra columnas 3D que comparan la referencia histórica "
            "con la proyección. Los colores indican el estado: gris para referencia, azul cuando la "
            "proyección baja, verde cuando se mantiene estable, naranja cuando sube y rojo cuando hay "
            "alerta de sobredemanda. El panel izquierdo resume la demanda total, las alertas y las "
            "prioridades a reforzar. Al seleccionar un barrio se ve su detalle, su muestra histórica, "
            "sus especies más pedidas y una tendencia. Debajo hay una comparativa por barrio y una "
            "serie de evolución."
        )
    )
    story.append(
        CALLOUT(
            "<b>Cómo leer el mapa.</b> Primero mirá los barrios en rojo y naranja: son los que "
            "requieren atención. Luego revisá la muestra histórica: si dice <i>muestra limitada</i>, "
            "la estimación es menos robusta. Por último, usá el detalle del barrio para ver qué "
            "especies explican su demanda.",
            "info",
        )
    )
    story.append(H3("Control de stock"))
    story.append(
        P(
            "El formulario pide características de una solicitud: temporada, año, localización, tipo "
            "de huerta, experiencia, superficie, destino y ocupación. No pide datos personales. Al "
            "presionar <b>«Analizar escenario»</b>, muestra la cobertura estimada del catálogo y "
            "cuántas variedades representan ese porcentaje. Luego presenta las dos alertas: "
            "regresión con umbral y clasificador directo. Si ambas coinciden, indica que la decisión "
            "es más confiable; si discrepan, recomienda preparar el kit completo."
        )
    )
    story.append(H3("Análisis climático"))
    story.append(
        P(
            "Permite elegir temporada, año y milímetros de lluvia esperados. El sistema estima la "
            "cobertura asociada y clasifica el escenario como sequía, régimen promedio o "
            "precipitaciones intensas. Los promedios históricos que muestra la pantalla son "
            "<b>650 mm para PV</b> y <b>380 mm para OI</b>. Sirve como herramienta de estrés rápido "
            "ante un pronóstico del Niño o de la Niña, pero no reemplaza el análisis de demanda."
        )
    )
    story.append(H3("Informe de datos"))
    story.append(
        P(
            "Reúne la documentación del proyecto: fuentes, variables, modelos, métricas, reglas de "
            "alerta y limitaciones. Es la pantalla para responder preguntas del tipo «¿de dónde sale "
            "este número?» o «¿qué tan confiable es esta estimación?»."
        )
    )
    story.append(H2("4.3. Un recorrido de uso en cinco pasos", "app-recorrido"))
    story.append(N("<b>Mirar el mapa</b> de la temporada que se está planificando y detectar los barrios en rojo o naranja.", 1))
    story.append(N("<b>Revisar las prioridades</b> del panel izquierdo y el detalle de cada barrio, incluyendo la muestra histórica.", 2))
    story.append(N("<b>Simular un perfil típico</b> en control de stock para ver si conviene preparar kits completos.", 3))
    story.append(N("<b>Comparar las dos alertas</b>; si discrepan, optar por la alternativa más conservadora.", 4))
    story.append(N("<b>Usar el módulo climático</b> como contexto adicional y registrar la decisión para la próxima campaña.", 5))
    story.append(
        CALLOUT(
            "<b>La aplicación no guarda los datos que se ingresan en el simulador.</b> El formulario "
            "solo se usa para calcular una estimación en el momento. El mapa y los informes trabajan "
            "con datos agregados por barrio.",
            "key",
        )
    )
    story.append(PageBreak())
    return story


def section_findings() -> list:
    story = [H1("5. Análisis y hallazgos", "hallazgos")]
    story.append(
        P(
            "Esta sección reúne las lecturas que consideramos más útiles para el equipo del Banco de "
            "Semillas. No son verdades absolutas: son patrones que aparecen en los datos y que "
            "conviene tener en cuenta al planificar."
        )
    )
    story.append(H2("5.1. La demanda cambia con la temporada", "hallazgos-temporada"))
    story.append(
        P(
            "Otoño–Invierno y Primavera–Verano no solo cambian de nombre: cambian las variedades. En "
            "OI predominan perejil, acelga, lechuga, cebolla, remolacha y espinaca. En PV aparecen "
            "con fuerza tomate, albahaca, morrón, zapallo de tronco y berenjena. Por eso el sistema "
            "mantiene referencias separadas y no mezcla las temporadas en una sola estimación."
        )
    )
    story.append(
        P(
            "La comparación entre campañas muestra otro fenómeno: la cantidad de variedades pedidas "
            "creció, pero la cobertura no siempre creció al mismo ritmo porque el catálogo se amplió. "
            "En OI 2026, por ejemplo, la cobertura media bajó a <b>49,5%</b> y la proporción de alta "
            "demanda a <b>17,7%</b>, aun cuando el promedio de variedades pedidas subió a <b>8,5</b>. "
            "La lectura correcta no es «la gente pide menos», sino «el catálogo creció y el umbral "
            "del 75% se volvió más exigente»."
        )
    )
    story.append(figure(CHART_COBERTURA, 16.2 * cm, "Figura 7. Cobertura media y proporción de solicitudes de alta demanda por campaña específica."))

    story.append(H2("5.2. Cuatro de cada diez solicitudes son de alta demanda", "hallazgos-demanda"))
    story.append(
        P(
            f"En la etapa con registro específico, <b>{fmt_int(CTX['alta_demanda'])}</b> de "
            f"<b>{fmt_int(CTX['modeladas'])}</b> solicitudes alcanzaron el 75% o más del catálogo "
            f"({fmt_dec(CTX['alta_demanda_pct'])}%). Es decir, aproximadamente <b>4 de cada 10</b>. "
            f"Esto no significa que todas esas personas necesiten un kit completo, pero sí que el "
            f"equipo debe estar preparado para una proporción importante de pedidos amplios."
        )
    )
    story.append(
        P(
            "La distribución no es pareja entre campañas: va de <b>17,7%</b> en OI 2026 a <b>54,5%</b> "
            "en PV 2025. La oferta de catálogo y el tamaño de la muestra explican parte de esas "
            "diferencias. Por eso la alerta siempre se acompaña del contexto de la temporada y de la "
            "muestra histórica."
        )
    )

    story.append(H2("5.3. El territorio concentra la demanda", "hallazgos-territorio"))
    story.append(
        P(
            f"Los cinco barrios con más solicitudes concentran cerca del <b>{CTX['top5_share']:.0f}%</b> "
            f"de los registros con barrio. Esa concentración no implica descuidar a los barrios "
            f"pequeños: precisamente porque tienen menos datos, el sistema los marca con <b>muestra "
            f"limitada</b> y evita sacar conclusiones demasiado firmes. La prioridad territorial "
            f"debe combinarse con el conocimiento de los promotores y referentes."
        )
    )

    story.append(H2("5.4. Los perfiles que más piden", "hallazgos-perfiles"))
    rows = [
        ["Perfil", "Cobertura media", "Alta demanda", "Lectura"],
        [
            f"Rural ({fmt_int(CTX['tipo_localizacion']['rural']['n'])} solicitudes)",
            f"{CTX['tipo_localizacion']['rural']['cob']:.0f}%",
            f"{CTX['tipo_localizacion']['rural']['alerta']:.0f}%",
            "Suele pedir más variedades que la huerta urbana.",
        ],
        [
            f"Periurbana ({fmt_int(CTX['tipo_localizacion']['periurbana']['n'])} solicitudes)",
            f"{CTX['tipo_localizacion']['periurbana']['cob']:.0f}%",
            f"{CTX['tipo_localizacion']['periurbana']['alerta']:.0f}%",
            "Perfil intermedio, con demanda más amplia que la urbana.",
        ],
        [
            f"Urbana ({fmt_int(CTX['tipo_localizacion']['urbana']['n'])} solicitudes)",
            f"{CTX['tipo_localizacion']['urbana']['cob']:.0f}%",
            f"{CTX['tipo_localizacion']['urbana']['alerta']:.0f}%",
            "Perfil mayoritario; suele pedir menos variedades.",
        ],
        [
            f"Autoconsumo e intercambio ({fmt_int(CTX['destino']['autoconsumo e intercambio']['n'])} solicitudes)",
            f"{CTX['destino']['autoconsumo e intercambio']['cob']:.0f}%",
            f"{CTX['destino']['autoconsumo e intercambio']['alerta']:.0f}%",
            "El intercambio se asocia con mayor diversidad.",
        ],
        [
            f"Autoconsumo ({fmt_int(CTX['destino']['autoconsumo']['n'])} solicitudes)",
            f"{CTX['destino']['autoconsumo']['cob']:.0f}%",
            f"{CTX['destino']['autoconsumo']['alerta']:.0f}%",
            "Perfil más frecuente y más acotado.",
        ],
        [
            f"Más de 20 m² ({fmt_int(CTX['superficie']['más de 20 m2']['n'])} solicitudes)",
            f"{CTX['superficie']['más de 20 m2']['cob']:.0f}%",
            f"{CTX['superficie']['más de 20 m2']['alerta']:.0f}%",
            "Mayor superficie se asocia con mayor cobertura.",
        ],
        [
            f"Hasta 5 m² ({fmt_int(CTX['superficie']['hasta 5 m2']['n'])} solicitudes)",
            f"{CTX['superficie']['hasta 5 m2']['cob']:.0f}%",
            f"{CTX['superficie']['hasta 5 m2']['alerta']:.0f}%",
            "Superficie pequeña, demanda más acotada.",
        ],
    ]
    story.append(
        table(
            rows,
            [6.1 * cm, 2.6 * cm, 2.5 * cm, 5.5 * cm],
            aligns=["left", "center", "center", "left"],
            font_size=7.7,
            pad=4,
        )
    )
    story.append(
        CAPTION(
            "Tabla 6. Cobertura media y alta demanda según perfiles seleccionados (2024–2026)."
        )
    )
    story.append(
        P(
            "Estos patrones son orientativos. No deben usarse para etiquetar a una persona ni para "
            "negarle variedades. Sirven para entender qué perfiles tienden a pedir más y para "
            "preparar stock con mayor margen en los barrios donde esos perfiles son frecuentes."
        )
    )

    story.append(H2("5.5. El presupuesto de referencia", "hallazgos-presupuesto"))
    story.append(
        P(
            f"Con un valor fijo de <b>$500 por sobre equivalente</b>, la etapa específica representa "
            f"un presupuesto estimado de <b>{fmt_money(CTX['presupuesto_especifico'])}</b> y la etapa de "
            f"kits genéricos, <b>{fmt_money(CTX['presupuesto_generico'])}</b>. El total histórico ronda "
            f"los <b>{fmt_money(CTX['presupuesto_total'])}</b>. Es importante aclarar que <b>$500 es un "
            f"valor de referencia</b>, no un precio de mercado: sirve para comparar escenarios y "
            f"dimensionar el esfuerzo, no para confeccionar un presupuesto oficial."
        )
    )
    story.append(
        P(
            "El sistema muestra el presupuesto proyectado en el mapa y en el simulador. Si el valor "
            "del sobre cambia, conviene actualizarlo antes de usar esas cifras para una decisión "
            "real."
        )
    )

    story.append(H2("5.6. Qué tan acertado es el sistema", "hallazgos-acierto"))
    story.append(
        P(
            "La estimación de demanda tiene un error típico de <b>2,6 sobres</b> por solicitud, sobre "
            "un pedido promedio de <b>7,7</b>. En planificación individual es una referencia; en "
            "totales agregados por barrio y temporada, los errores tienden a compensarse. La validación "
            "temporal mostró que el modelo apenas mejora a una referencia histórica simple: por eso "
            "insistimos en usarlo como apoyo y no como oráculo."
        )
    )
    story.append(
        P(
            "La alerta de alta demanda, en cambio, está calibrada para <b>no dejar pasar casos</b>: "
            "detecta aproximadamente 88 de cada 100 solicitudes que realmente necesitaban un kit "
            "completo, a costa de generar avisos de más. Esa asimetría es coherente con el costo "
            "social de quedarse corto."
        )
    )

    story.append(H2("5.7. Una mirada a 2027–2028", "hallazgos-proyecciones"))
    story.append(
        P(
            "El mapa permite explorar escenarios para 2027 y 2028. Esos años no tienen datos "
            "observados: se construyen repitiendo la última oferta de catálogo y aplicando un "
            "crecimiento anual supuesto del 5%. En los escenarios cargados al cierre de este "
            "informe, no aparece una sobredemanda generalizada en los barrios mapeados; sí se "
            "encienden alertas puntuales en Primavera–Verano. La mayoría de los barrios tiene "
            "muestra limitada, y el sistema lo advierte."
        )
    )
    story.append(
        CALLOUT(
            "<b>Importante.</b> Las proyecciones 2027–2028 son escenarios base, no pronósticos "
            "validados. Sirven para conversar sobre prioridades y dimensionar stock, pero no para "
            "comprometer cantidades exactas ni para tomar decisiones automáticas.",
            "warn",
        )
    )
    return story


def section_limits() -> list:
    story = [H1("6. Qué puede y qué no puede hacer el sistema", "limites")]
    story.append(
        P(
            "Un sistema útil no es el que promete todo, sino el que deja claro para qué sirve y "
            "dónde están sus límites. Esta sección resume ambas cosas."
        )
    )
    rows = [
        ["Puede hacer", "No puede hacer"],
        [
            "Estimar la demanda agregada por barrio y temporada.",
            "Predecir el pedido exacto de una familia.",
        ],
        [
            "Priorizar barrios y perfiles para reforzar stock.",
            "Decidir a quién entregar o negar semillas.",
        ],
        [
            "Simular el efecto de un perfil de huerta en la cobertura.",
            "Garantizar que una persona pedirá lo que el modelo estima.",
        ],
        [
            "Aportar contexto climático para escenarios de sequía o lluvia intensa.",
            "Explicar por sí solo la demanda a partir del clima.",
        ],
        [
            "Documentar datos, supuestos y limitaciones.",
            "Reemplazar el conocimiento territorial de los promotores.",
        ],
        [
            "Generar escenarios 2027–2028 para planificar.",
            "Validar esos escenarios como pronósticos ciertos.",
        ],
    ]
    t = Table(
        [
            [
                Paragraph(rows[0][0], S["head"]),
                Paragraph(rows[0][1], S["head"]),
            ]
        ]
        + [
            [Paragraph(a, S["cell"]), Paragraph(b, S["cell"])]
            for a, b in rows[1:]
        ],
        colWidths=[8.3 * cm, 8.3 * cm],
    )
    cmds = [
        ("BACKGROUND", (0, 0), (0, 0), GREEN_DARK),
        ("BACKGROUND", (1, 0), (1, 0), RED),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7dee5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), GREY_LIGHT))
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(CAPTION("Tabla 7. Alcance real del sistema."))

    story.append(H2("6.1. Limitaciones que conviene tener presentes", "limites-lista"))
    story.append(B("<b>La serie es corta.</b> Siete campañas y cambios de formulario limitan la comparabilidad estricta entre años."))
    story.append(B("<b>Faltan barrios.</b> 2024 y OI 2025 no registran barrio; por eso hay 786 solicitudes sin asignación territorial."))
    story.append(B("<b>El catálogo cambia.</b> Las proyecciones repiten la última oferta observada; si el catálogo cambia, la cobertura estimada también cambia."))
    story.append(B("<b>El precio es supuesto.</b> $500 por sobre es un valor de referencia, no un precio de mercado."))
    story.append(B("<b>La alerta no es una probabilidad.</b> Es una regla de decisión; no expresa «probabilidad de que pase»."))
    story.append(B("<b>La muestra de algunos barrios es pequeña.</b> Menos de 10 solicitudes o menos de 2 años de datos reducen la confiabilidad."))
    story.append(B("<b>El clima no lo explica todo.</b> La relación es leve y debe usarse como contexto, no como factor único."))
    story.append(B("<b>El modelo no aprende solo.</b> Necesita reentrenamiento con nuevas campañas y revisión humana."))
    story.append(
        CALLOUT(
            "<b>Regla de oro.</b> Usar el sistema para ordenar la conversación y priorizar recursos, "
            "no para automatizar decisiones sobre familias. Si una estimación contradice el "
            "conocimiento territorial del equipo, conviene revisar los datos y el contexto antes de "
            "actuar.",
            "risk",
        )
    )
    story.append(PageBreak())
    return story


def section_conclusions() -> list:
    story = [H1("7. Conclusiones y recomendaciones", "conclusiones")]
    story.append(
        P(
            "El proyecto logró convertir un conjunto disperso de formularios en información "
            "accionable para la planificación del Banco de Semillas. No resolvió la incertidumbre "
            "por completo —eso no es posible—, pero sí aportó una forma más ordenada de mirarla."
        )
    )
    story.append(H2("7.1. Conclusiones", "conclusiones-lista"))
    story.append(
        P(
            "<b>1. La demanda se puede anticipar mejor en agregado que en forma individual.</b> El "
            "modelo no es preciso para una familia, pero sí útil para estimar totales por barrio y "
            "temporada, que es la unidad de planificación del Banco."
        )
    )
    story.append(
        P(
            "<b>2. El territorio y la temporada son las dimensiones más importantes.</b> La demanda "
            "se concentra en pocos barrios y cambia de variedades entre OI y PV. Una planificación "
            "única para toda la ciudad y todo el año sería menos útil."
        )
    )
    story.append(
        P(
            "<b>3. La cobertura es más informativa que la cantidad absoluta.</b> El catálogo creció "
            "de 9 a 18 variedades; medir porcentaje permite comparar temporadas y evita conclusiones "
            "engañosas."
        )
    )
    story.append(
        P(
            "<b>4. La transparencia es parte del producto.</b> Las métricas honestas, las advertencias "
            "en pantalla y la documentación de límites hacen que el sistema sea más confiable y "
            "mejorable que un modelo que promete precisión exagerada."
        )
    )
    story.append(
        CALLOUT(
            "<b>Conclusión final.</b> El mayor valor del sistema no está en adivinar el pedido de una "
            "persona, sino en ayudar a decidir dónde poner atención, cuánto stock preparar y cómo "
            "aprender de cada campaña. Es una herramienta para pensar mejor la logística del Banco "
            "de Semillas.",
            "key",
        )
    )

    story.append(H2("7.2. Recomendaciones para el equipo", "conclusiones-recomendaciones"))
    story.append(N("<b>Incorporar el barrio como campo obligatorio</b> en todos los formularios. Es la mejora con mayor impacto potencial para el mapa y las proyecciones.", 1))
    story.append(N("<b>Registrar siempre las variedades solicitadas</b>, aunque se entregue un kit genérico. Sin ese dato, no se puede aprender de la demanda real.", 2))
    story.append(N("<b>Estandarizar las opciones de respuesta</b> (superficie, experiencia, destino, ocupación) para reducir la limpieza manual y mejorar la comparabilidad.", 3))
    story.append(N("<b>Usar el mapa para priorizar</b> barrios y recorridos, y el control de stock para decidir el tipo de kit. No usar una sola pantalla como única fuente.", 4))
    story.append(N("<b>Revisar las alertas con criterio territorial.</b> Si el sistema marca un barrio, contrastar con el conocimiento de los promotores y con la muestra histórica.", 5))
    story.append(N("<b>Actualizar el valor del sobre</b> antes de usar las cifras de presupuesto para una decisión real.", 6))
    story.append(N("<b>Validar después de cada campaña.</b> Comparar lo proyectado con lo observado y ajustar supuestos, umbrales y modelos.", 7))
    story.append(N("<b>Reentrenar los modelos con nuevas campañas</b> y mantener la documentación de datos y limitaciones.", 8))
    story.append(N("<b>Cuidar la privacidad.</b> Mantener el mapa en agregados por barrio y no ingresar datos personales en el simulador.", 9))

    story.append(H2("7.3. Próximos pasos sugeridos", "conclusiones-pasos"))
    rows = [
        ["Prioridad", "Acción", "Resultado esperado"],
        ["Alta", "Barrio obligatorio y registro de variedades en todos los formularios.", "Mejor cobertura territorial y modelos más confiables."],
        ["Alta", "Validación post-campaña con el equipo del Banco.", "Ajuste de umbrales y supuestos con evidencia local."],
        ["Media", "Actualización anual del precio del sobre y del catálogo.", "Presupuestos y escenarios más realistas."],
        ["Media", "Capacitación breve a referentes en el uso del mapa y del simulador.", "Uso más extendido y consistente."],
        ["Baja", "Integración con el stock físico y con nuevas fuentes de datos.", "Planificación más automatizada y precisa."],
    ]
    story.append(
        table(
            rows,
            [2.0 * cm, 8.0 * cm, 6.6 * cm],
            aligns=["center", "left", "left"],
            font_size=7.8,
            pad=4,
        )
    )
    story.append(CAPTION("Tabla 8. Próximos pasos sugeridos para el Banco de Semillas."))
    return story


def section_faq() -> list:
    story = [H1("8. Preguntas frecuentes y glosario", "faq")]
    story.append(H2("8.1. Preguntas frecuentes", "faq-preguntas"))
    qa = [
        (
            "¿El sistema predice lo que va a pedir una familia?",
            "No. Estima la demanda agregada por barrio y temporada. La estimación individual es una referencia y tiene un error típico de 2,6 sobres.",
        ),
        (
            "¿Por qué no usa los datos de 2022 y 2023?",
            "Porque esos formularios no registran las variedades elegidas, solo la cantidad de kits. Usarlos habría obligado a inventar una composición.",
        ),
        (
            "¿Por qué el umbral es 75%?",
            "Porque equivale a tres de cada cuatro variedades del catálogo. Es un punto operativo para decidir si conviene preparar un kit completo. No es una regla natural ni definitiva.",
        ),
        (
            "¿Qué hago si las dos alertas del control de stock no coinciden?",
            "Preparar el kit completo. Un falso negativo (quedarse corto) cuesta el doble que un falso positivo (preparar de más).",
        ),
        (
            "¿Cada cuánto se actualiza el sistema?",
            "Cuando se suman nuevas campañas y se reentrenan los modelos. La aplicación no aprende sola en tiempo real.",
        ),
        (
            "¿Qué significa «muestra limitada»?",
            "Que un barrio tiene menos de 10 solicitudes históricas o menos de 2 años de datos. En esos casos la estimación es menos robusta.",
        ),
        (
            "¿Qué significa «sin dato»?",
            "Que el formulario no registró el barrio. Esos registros se conservan para el total municipal, pero no se asignan al mapa.",
        ),
        (
            "¿La aplicación guarda datos personales?",
            "El simulador de stock no guarda los datos que se ingresan. El mapa trabaja con totales agregados por barrio.",
        ),
    ]
    for q, a in qa:
        story.append(
            Paragraph(
                f"<b>{q}</b>",
                ParagraphStyle(
                    "q",
                    fontName="Arial-Bold",
                    fontSize=9.6,
                    leading=13,
                    textColor=GREEN_DARK,
                    spaceBefore=5,
                    spaceAfter=1,
                ),
            )
        )
        story.append(P(a, "body"))

    story.append(H2("8.2. Glosario", "faq-glosario"))
    rows = [
        ["Término", "Qué significa"],
        ["Sobre equivalente", "Unidad que representa una variedad solicitada. Si alguien pide ocho variedades, son ocho sobres equivalentes."],
        ["Cobertura del catálogo", "Porcentaje de variedades disponibles que pide una solicitud."],
        ["Alta demanda", "Cobertura igual o superior al 75% del catálogo de la temporada."],
        ["Baseline", "Referencia histórica de demanda por barrio y temporada, ajustada por un crecimiento supuesto."],
        ["Sobredemanda", "Proyección que supera el baseline en al menos 10% y 10 sobres."],
        ["Muestra limitada", "Barrio con menos de 10 solicitudes o menos de 2 años de datos."],
        ["Escenario base", "Proyección construida con supuestos explícitos; no es un pronóstico validado."],
        ["Kit genérico", "Kit de diez especies surtidas de 2022–2023, sin registro de variedades."],
        ["Selección específica", "Registro de las variedades elegidas por cada solicitud a partir de 2024."],
    ]
    story.append(
        table(
            rows,
            [4.4 * cm, 12.2 * cm],
            aligns=["left", "left"],
            font_size=8.0,
            pad=4,
        )
    )
    story.append(CAPTION("Tabla 9. Glosario para leer el sistema sin conocimientos técnicos."))

    story.append(H2("8.3. Ficha técnica resumida", "faq-ficha"))
    rows = [
        ["Aspecto", "Detalle"],
        ["Datos analizados", "2.730 solicitudes de siete campañas (2022–2026)."],
        ["Datos usados para el modelo", "1.487 solicitudes específicas con variedades observadas (2024–2026)."],
        ["Modelo de demanda", "Vecinos cercanos (k = 41); error típico de 2,6 sobres por solicitud."],
        ["Modelo de alerta", "Árbol de decisión; detecta aproximadamente 88 de cada 100 casos de alta demanda."],
        ["Modelo climático", "Regresión lineal simple: +100 mm de lluvia ≈ +1,3 puntos de cobertura."],
        ["Precio de referencia", "$500 por sobre equivalente (valor supuesto, no de mercado)."],
        ["Aplicación", "Flask, desplegada en Vercel: https://pro-huerta.vercel.app/"],
        ["Documentación", "Auditoría de datos, diccionario de variables y métricas del proyecto."],
    ]
    story.append(
        table(
            rows,
            [4.6 * cm, 12.0 * cm],
            aligns=["left", "left"],
            font_size=8.0,
            pad=4,
        )
    )
    story.append(CAPTION("Tabla 10. Ficha técnica para quien quiera profundizar."))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        CALLOUT(
            "<b>Nota de entrega.</b> Este documento está pensado para el equipo del Banco de "
            "Semillas. El informe técnico completo, con metodología, métricas y reproducibilidad, "
            "se entrega por separado. Si el equipo lo considera útil, podemos preparar una "
            "capacitación breve y una guía de una página para el uso cotidiano.",
            "info",
        )
    )
    return story


def build() -> None:
    story = []
    story += cover()
    story += executive_summary()
    story += toc()
    story += section_problem()
    story += section_data()
    story += section_decisions()
    story += section_app()
    story += section_findings()
    story += section_limits()
    story += section_conclusions()
    story += section_faq()

    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=LM,
        rightMargin=RM,
        topMargin=TM,
        bottomMargin=BM,
        title="Informe Final para el Cliente - ProHuerta Chascomús",
        author="Barreu, Quiroga, Pérez Cazal",
        subject="Sistema de previsión de demanda y planificación logística del Banco de Semillas",
        creator="ProHuerta Chascomús",
    )
    frame = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="normal")
    cover_frame = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="cover")
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[cover_frame], onPage=on_first_page),
            PageTemplate(id="main", frames=[frame], onPage=on_later_pages),
        ]
    )
    doc.multiBuild(story, canvasmaker=NumberedCanvas)
    print("PDF generado:", OUTPUT)
    print("Páginas:", doc.page)


if __name__ == "__main__":
    build()
