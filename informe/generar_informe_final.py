# -*- coding: utf-8 -*-
"""
Genera el Informe Final de Entrega del proyecto ProHuerta Chascomus en PDF.
Requiere: reportlab, pillow.
Uso: python informe/generar_informe_final.py
"""
from __future__ import annotations

import os
from pathlib import Path

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
    ListFlowable,
    ListItem,
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
OUTPUT = BASE_DIR / "Informe Final de Entrega - ProHuerta.pdf"
COVER_IMG = BASE_DIR / "static" / "img" / "huerta-comunitaria.jpg"

# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------
FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONT_DIR / "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FONT_DIR / "arialbi.ttf")))
pdfmetrics.registerFontFamily(
    "Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-BoldItalic"
)

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
GREEN = colors.HexColor("#1f8f4e")
GREEN_DARK = colors.HexColor("#125c34")
GREEN_LIGHT = colors.HexColor("#eaf5ee")
BLUE = colors.HexColor("#2f6fb3")
BLUE_LIGHT = colors.HexColor("#eaf1f9")
GREY = colors.HexColor("#4b5563")
GREY_LIGHT = colors.HexColor("#f3f5f7")
GREY_MID = colors.HexColor("#c9d1d9")
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

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

S = {}
S["body"] = ParagraphStyle(
    "body", fontName="Arial", fontSize=9.7, leading=14.2, alignment=TA_JUSTIFY,
    textColor=colors.HexColor("#1f2937"), spaceAfter=5.5,
)
S["body_first"] = ParagraphStyle("body_first", parent=S["body"], spaceBefore=2)
S["body_keep"] = ParagraphStyle("body_keep", parent=S["body"], keepWithNext=1)
S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=8.3, leading=11.5, textColor=GREY)
S["caption"] = ParagraphStyle(
    "caption", fontName="Arial-Italic", fontSize=8.2, leading=11, textColor=GREY,
    alignment=TA_CENTER, spaceBefore=3, spaceAfter=10,
)
S["h1"] = ParagraphStyle(
    "h1", fontName="Arial-Bold", fontSize=15.5, leading=19, textColor=GREEN_DARK,
    spaceBefore=16, spaceAfter=7, keepWithNext=1,
)
S["h2"] = ParagraphStyle(
    "h2", fontName="Arial-Bold", fontSize=11.6, leading=15, textColor=GREEN,
    spaceBefore=11, spaceAfter=4, keepWithNext=1,
)
S["h3"] = ParagraphStyle(
    "h3", fontName="Arial-Bold", fontSize=10.1, leading=13.5,
    textColor=colors.HexColor("#334155"), spaceBefore=8, spaceAfter=3, keepWithNext=1,
)
S["bullet"] = ParagraphStyle(
    "bullet", parent=S["body"], leftIndent=13, bulletIndent=3, spaceAfter=2.2,
)
S["bullet2"] = ParagraphStyle(
    "bullet2", parent=S["bullet"], leftIndent=25, bulletIndent=15,
)
S["num"] = ParagraphStyle(
    "num", parent=S["body"], leftIndent=17, bulletIndent=2, spaceAfter=2.2,
)
S["cell"] = ParagraphStyle(
    "cell", fontName="Arial", fontSize=8.15, leading=10.4, textColor=colors.HexColor("#1f2937"),
    alignment=TA_LEFT,
)
S["cell_center"] = ParagraphStyle("cell_center", parent=S["cell"], alignment=TA_CENTER)
S["cell_bold"] = ParagraphStyle("cell_bold", parent=S["cell"], fontName="Arial-Bold")
S["head"] = ParagraphStyle(
    "head", fontName="Arial-Bold", fontSize=8.3, leading=10.6, textColor=WHITE,
    alignment=TA_LEFT,
)
S["head_center"] = ParagraphStyle("head_center", parent=S["head"], alignment=TA_CENTER)
S["formula"] = ParagraphStyle(
    "formula", fontName="Courier", fontSize=8.6, leading=12, textColor=colors.HexColor("#123b2a"),
    alignment=TA_LEFT,
)
S["callout"] = ParagraphStyle(
    "callout", fontName="Arial", fontSize=8.9, leading=12.6, textColor=colors.HexColor("#1f2937"),
    alignment=TA_JUSTIFY,
)
S["toc_title"] = ParagraphStyle(
    "toc_title", fontName="Arial-Bold", fontSize=16, leading=20, textColor=GREEN_DARK,
    spaceAfter=12,
)

# ---------------------------------------------------------------------------
# Helpers de contenido
# ---------------------------------------------------------------------------
def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def H1(text: str, key: str | None = None) -> "TOCHeading":
    return TOCHeading(text, S["h1"], 0, key or text)


def H2(text: str, key: str | None = None) -> "TOCHeading":
    return TOCHeading(text, S["h2"], 1, key or text)


def H3(text: str, key: str | None = None) -> "TOCHeading":
    return TOCHeading(text, S["h3"], 2, key or text)


def B(text: str, style: str = "bullet") -> Paragraph:
    return Paragraph(text, S[style], bulletText="•")


def N(text: str, number: int) -> Paragraph:
    return Paragraph(text, S["num"], bulletText=f"{number}.")


def FORMULA(text: str) -> Table:
    t = Table([[Paragraph(text, S["formula"])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4faf6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfe5d7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def CALLOUT(text: str, kind: str = "info") -> Table:
    bg = {"info": BLUE_LIGHT, "warn": AMBER_LIGHT, "key": GREEN_LIGHT, "risk": RED_LIGHT}[kind]
    bar = {"info": BLUE, "warn": AMBER, "key": GREEN, "risk": RED}[kind]
    t = Table([[Paragraph(text, S["callout"])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3.2, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def table(
    rows: list[list], widths: list[float], header: bool = True,
    aligns: list[str] | None = None, zebra: bool = True, font_size: float | None = None,
    pad: float = 4,
) -> Table:
    """rows: first row is header. Cells may be str or Flowable."""
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
                    st = ParagraphStyle("tmp", parent=st, fontSize=font_size, leading=font_size * 1.28)
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


# ---------------------------------------------------------------------------
# Encabezados con entrada de indice
# ---------------------------------------------------------------------------
class TOCHeading(Paragraph):
    def __init__(self, text: str, style: ParagraphStyle, level: int = 0, key: str | None = None):
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
            doc.notify("TOCEntry", (self._toc_level, self.getPlainText(), self.canv.getPageNumber(), key))


# ---------------------------------------------------------------------------
# Diagrama de flujo basado en tabla
# ---------------------------------------------------------------------------
def FLOW(steps: list[str], color: colors.Color = GREEN_DARK) -> Table:
    cells = []
    widths = []
    for i, s in enumerate(steps):
        cells.append(Paragraph(s, ParagraphStyle(
            "flowcell", fontName="Arial-Bold", fontSize=7.6, leading=9.6,
            textColor=WHITE, alignment=TA_CENTER,
        )))
        widths.append((CONTENT_W - (len(steps) - 1) * 0.55 * cm) / len(steps))
        if i < len(steps) - 1:
            cells.append(Paragraph("→", ParagraphStyle(
                "arrow", fontName="Arial-Bold", fontSize=12, leading=14,
                textColor=color, alignment=TA_CENTER,
            )))
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


# ---------------------------------------------------------------------------
# Canvas con numeracion total
# ---------------------------------------------------------------------------
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
        self.drawString(LM, 1.02 * cm, "ProHuerta Chascomús · Informe Final Integrador")
        self.drawRightString(PAGE_W - RM, 1.02 * cm, f"Página {page} de {total}")
        self.restoreState()


def on_first_page(canv, doc):
    pass


def on_later_pages(canv, doc):
    canv.saveState()
    canv.setFont("Arial", 7.4)
    canv.setFillColor(GREY)
    canv.drawString(LM, PAGE_H - 1.24 * cm, "ProHuerta Chascomús · Informe Final Integrador")
    canv.drawRightString(PAGE_W - RM, PAGE_H - 1.24 * cm,
                         "Modelos de Aprendizaje Automático · Instituto N.º 57")
    canv.setStrokeColor(GREY_MID)
    canv.setLineWidth(0.5)
    canv.line(LM, PAGE_H - 1.45 * cm, PAGE_W - RM, PAGE_H - 1.45 * cm)
    canv.restoreState()


# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------
def cover() -> list:
    story = []
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "INSTITUTO SUPERIOR DE FORMACIÓN DOCENTE Y TÉCNICA N.º 57",
        ParagraphStyle("cov_inst", fontName="Arial-Bold", fontSize=9.5, leading=13,
                       textColor=GREEN_DARK, alignment=TA_CENTER, spaceAfter=2),
    ))
    story.append(Paragraph(
        "Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial",
        ParagraphStyle("cov_carrera", fontName="Arial", fontSize=9, leading=12,
                       textColor=GREY, alignment=TA_CENTER, spaceAfter=10),
    ))
    story.append(HRFlowable(width="100%", thickness=2.8, color=GREEN, spaceBefore=0, spaceAfter=16))

    story.append(Paragraph(
        "INFORME FINAL INTEGRADOR",
        ParagraphStyle("cov_kicker", fontName="Arial-Bold", fontSize=9, leading=12,
                       textColor=GREEN, alignment=TA_CENTER, spaceAfter=6),
    ))
    story.append(Paragraph(
        "Sistema Inteligente de Predicción de Demanda de Variedades<br/>"
        "y Planificación Logística del Banco de Semillas",
        ParagraphStyle("cov_title", fontName="Arial-Bold", fontSize=21, leading=26,
                       textColor=GREEN_DARK, alignment=TA_CENTER, spaceAfter=8),
    ))
    story.append(Paragraph(
        "ProHuerta · Chascomús, Buenos Aires",
        ParagraphStyle("cov_sub", fontName="Arial", fontSize=12.5, leading=16,
                       textColor=GREY, alignment=TA_CENTER, spaceAfter=4),
    ))
    story.append(Paragraph(
        "Modelos de Aprendizaje Automático · Grupo 3",
        ParagraphStyle("cov_sub2", fontName="Arial-Italic", fontSize=10.5, leading=14,
                       textColor=BLUE, alignment=TA_CENTER, spaceAfter=16),
    ))

    if COVER_IMG.exists():
        img = Image(str(COVER_IMG), width=15.2 * cm, height=15.2 * cm * 900 / 1600)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Paragraph(
            "Huerta comunitaria. Imagen de referencia del proyecto ProHuerta Chascomús.",
            S["caption"],
        ))

    meta = [
        ["Integrantes", "Barreu, Lucas · Quiroga, Franco · Pérez Cazal, Marcelo"],
        ["Docente", "[Completar]"],
        ["Comisión", "[Completar]"],
        ["Fecha de entrega", "3 de noviembre de 2026"],
        ["Versión del informe", "1.0"],
        ["Aplicación web (demo)", "https://pro-huerta.vercel.app/"],
        ["Repositorio", "github.com/lucasbar28/ProHuerta"],
    ]
    t = Table(
        [[Paragraph(f"<b>{a}</b>", S["cell"]), Paragraph(b, S["cell"])] for a, b in meta],
        colWidths=[4.4 * cm, 10.4 * cm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cfe5d7")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d9e9df")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    t.hAlign = "CENTER"
    story.append(t)
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph(
        "Trabajo Práctico Integrador · Ciencia de Datos e Inteligencia Artificial",
        ParagraphStyle("cov_foot", fontName="Arial", fontSize=8, leading=10,
                       textColor=GREY, alignment=TA_CENTER),
    ))
    story.append(NextPageTemplate("main"))
    story.append(PageBreak())
    return story


# ---------------------------------------------------------------------------
# Contenido
# ---------------------------------------------------------------------------
def executive_summary() -> list:
    story = [H1("Resumen ejecutivo", "resumen")]
    story.append(P(
        "El presente informe documenta el desarrollo, la evaluación y el despliegue de un sistema "
        "de apoyo a la planificación logística para el Banco de Intercambio de Semillas del programa "
        "ProHuerta en Chascomús. El problema central es la incertidumbre sobre la cantidad y diversidad "
        "de variedades que solicitará cada persona al retirar su kit de semillas: preparar de más "
        "inmoviliza insumos limitados y preparar de menos genera faltantes, demoras y una experiencia "
        "deficiente para las familias."
    ))
    story.append(P(
        "La solución construida integra un pipeline reproducible de preparación de datos, modelos "
        "supervisados de regresión y clasificación, reglas de negocio explícitas y una aplicación web "
        "Flask con visualización territorial en 3D. El sistema se alimenta de <b>2.730 solicitudes</b> "
        "históricas correspondientes a siete campañas estacionales (2022–2026). Para el modelado se "
        "utilizan las <b>1.487 solicitudes específicas</b> con variedades observadas entre 2024 y 2026, "
        "evitando el sesgo de los kits genéricos de 2022–2023."
    ))
    story.append(P(
        "El modelo principal de demanda es un <b>KNeighborsRegressor (k = 41)</b> que estima los sobres "
        "equivalentes por solicitud a partir del perfil socio-productivo y del histórico barrial. La "
        "evaluación final sobre el conjunto de prueba calibrado arroja <b>RMSE = 3,39</b> y "
        "<b>MAE = 2,60 sobres</b>. En paralelo, un <b>árbol de decisión</b> estima la alerta de alta "
        "demanda (cobertura del catálogo ≥ 75 %) y un <b>modelo lineal</b> purgado evalúa el efecto de "
        "las precipitaciones sobre la cobertura. La aplicación expone estos modelos mediante una API "
        "REST y cinco vistas: portada, inicio, mapa de demanda, control de stock, análisis climático e "
        "informe de datos."
    ))
    story.append(CALLOUT(
        "<b>Resultado principal.</b> El sistema no pretende predecir con exactitud el pedido de una "
        "familia individual; su valor está en la <b>planificación agregada por barrio y temporada</b>, "
        "en la detección temprana de sobredemanda y en la trazabilidad metodológica. La honestidad de "
        "las métricas y la documentación de las limitaciones forman parte del diseño y de la "
        "evaluación crítica del trabajo.",
        "key",
    ))
    story.append(Spacer(1, 0.25 * cm))
    story.append(P(
        "<b>Palabras clave:</b> aprendizaje automático, ProHuerta, predicción de demanda, planificación "
        "logística, regresión, clasificación, visualización geoespacial, Flask, scikit-learn.",
        "small",
    ))
    story.append(PageBreak())
    return story


def toc() -> list:
    story = [Paragraph("Índice de contenidos", S["toc_title"])]
    t = TableOfContents()
    t.levelStyles = [
        ParagraphStyle("toc0", fontName="Arial-Bold", fontSize=9.8, leading=15,
                       textColor=GREEN_DARK, leftIndent=0, firstLineIndent=0),
        ParagraphStyle("toc1", fontName="Arial", fontSize=9, leading=13.5,
                       textColor=colors.HexColor("#334155"), leftIndent=14, firstLineIndent=0),
        ParagraphStyle("toc2", fontName="Arial", fontSize=8.4, leading=12.5,
                       textColor=GREY, leftIndent=28, firstLineIndent=0),
    ]
    t.tableStyle = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ])
    story.append(t)
    story.append(PageBreak())
    return story


def section_intro() -> list:
    story = [H1("1. Introducción", "intro")]
    story.append(H2("1.1. Contexto institucional y territorial", "intro-contexto"))
    story.append(P(
        "El programa ProHuerta, impulsado por el INTA y articulado con municipios y organizaciones "
        "locales, promueve la producción agroecológica de alimentos y el acceso a semillas de calidad. "
        "En Chascomús, el Banco de Intercambio de Semillas cumple un rol central en la entrega de kits "
        "estacionales de semillas a huertas familiares, escolares, comunitarias e institucionales. Cada "
        "campaña se organiza en dos temporadas: <b>Otoño–Invierno (OI)</b> y <b>Primavera–Verano (PV)</b>."
    ))
    story.append(P(
        "La diversidad de variedades que solicita cada participante depende de múltiples factores: el "
        "tipo de huerta, la superficie disponible, la experiencia previa, el destino de la producción, "
        "la ocupación de la persona responsable y el barrio donde se localiza la huerta. Esa "
        "heterogeneidad dificulta la preparación anticipada de kits completos y la asignación "
        "presupuestaria."
    ))
    story.append(H2("1.2. Problemática", "intro-problema"))
    story.append(P(
        "El equipo logístico debe decidir, antes de la entrega, si prepara kits completos o kits "
        "básicos estandarizados. Si prepara de más, inmoviliza sobres que podrían haberse destinado a "
        "otras familias; si prepara de menos, faltan variedades en el mostrador y se afecta la "
        "diversidad de la huerta y la experiencia del programa. El problema es, en esencia, un problema "
        "de <b>predicción de demanda y planificación bajo incertidumbre</b>."
    ))
    story.append(H2("1.3. Objetivos", "intro-objetivos"))
    story.append(P("<b>Objetivo general.</b> Diseñar e implementar un sistema de aprendizaje automático "
                   "que anticipe la demanda de variedades de semillas y aporte información para la "
                   "planificación logística, presupuestaria y territorial del Banco de Semillas de "
                   "Chascomús."))
    story.append(P("<b>Objetivos específicos.</b>"))
    story.append(N("Consolidar y auditar las bases históricas de solicitudes de semillas de las "
                   "temporadas 2022–2026, resolviendo inconsistencias de formato, barrio y especies.", 1))
    story.append(N("Construir un dataset modelable con variables socio-productivas disponibles al "
                   "momento de la inscripción, evitando fugas de información.", 2))
    story.append(N("Entrenar y comparar modelos de regresión para estimar la cantidad de sobres "
                   "equivalentes por solicitud.", 3))
    story.append(N("Entrenar un clasificador de alta demanda y definir reglas de negocio para la "
                   "activación de alertas logísticas.", 4))
    story.append(N("Desarrollar una aplicación web que integre los modelos, un mapa territorial en 3D "
                   "y módulos de simulación de stock y clima.", 5))
    story.append(N("Documentar métricas, supuestos, limitaciones y reproducibilidad del sistema.", 6))
    story.append(H2("1.4. Alcance y usuarios", "intro-alcance"))
    story.append(P(
        "El sistema está orientado a coordinadores logísticos, promotores territoriales y referentes "
        "de la Dirección de Ambiente y Desarrollo Sustentable. Se utiliza como <b>apoyo a la decisión</b>, "
        "no como mecanismo automático de asignación de insumos. La unidad de análisis es la solicitud "
        "individual de retiro de semillas; la unidad de planificación es el barrio y la temporada."
    ))
    story.append(H2("1.5. Organización del documento", "intro-organizacion"))
    story.append(P(
        "El documento se organiza en ocho secciones y cuatro anexos. Las secciones 2 y 3 describen los "
        "datos y la metodología; la sección 4 presenta los modelos y sus métricas; la sección 5 detalla "
        "la arquitectura de la aplicación; la sección 6 discute los resultados; las secciones 7 y 8 "
        "sintetizan conclusiones y trabajo futuro. Los anexos contienen la estructura del repositorio, "
        "los endpoints de la API, los comandos de reproducción y un glosario."
    ))
    story.append(PageBreak())
    return story


def section_data() -> list:
    story = [H1("2. Datos", "datos")]
    story.append(H2("2.1. Fuentes y volumetría", "datos-fuentes"))
    story.append(P(
        "La información proviene de los formularios de retiro de semillas del Banco de Intercambio de "
        "Semillas de Chascomús. El script <b>preparar_datos.py</b> consolida siete archivos Excel "
        "correspondientes a siete campañas estacionales, entre 2022 y 2026. La Tabla 1 resume las "
        "fuentes y la cantidad de filas procesadas."
    ))
    rows = [
        ["Año", "Temp.", "Archivo de origen", "Hoja", "Filas"],
        ["2022", "OI", "2022 registro de huerta otoño-invierno 2022.xlsx", "general", "488"],
        ["2023", "OI", "2023 Relevamiento otoño invierno para filtrar.xlsx", "DATOS", "750"],
        ["2024", "PV", "2024 retiro de semillas prim-ver. 2024. + seguimiento + devolución.xlsx", "familiares", "273"],
        ["2025", "OI", "2025 RETIRO de semillas 2025 por primera vez OI 2025 (respuestas).xlsx", "Respuestas de formulario 1", "295"],
        ["2025", "PV", "2025 retiro de semillas por primera vez PV 2025 (respuestas).xlsx", "Respuestas de formulario 1", "464"],
        ["2026", "OI", "2026 Retiro de semillas por primera vez O-I 2026 (respuestas).xlsx", "Respuestas de formulario 1", "237"],
        ["2026", "PV", "2026 Retiro de semillas P-V 2026 (respuestas).xlsx", "Respuestas de formulario 1", "223"],
    ]
    story.append(table(rows, [1.15 * cm, 1.35 * cm, 8.0 * cm, 4.0 * cm, 1.4 * cm],
                       aligns=["center", "center", "left", "left", "center"]))
    story.append(CAPTION("Tabla 1. Fuentes de datos y filas procesadas por campaña. Total: 2.730 solicitudes."))

    story.append(H2("2.2. Esquemas de entrega: kits genéricos y específicos", "datos-esquemas"))
    story.append(P(
        "El histórico presenta dos esquemas de entrega. Entre 2022 y 2023 se entregaba un <b>kit genérico "
        "de diez especies surtidas</b>, sin detalle de variedades en el formulario. A partir de 2024 se "
        "registra la <b>selección específica de variedades</b>, lo que permite observar la demanda real "
        "de cada solicitud. Esta diferencia es central: los kits genéricos solo pueden imputarse "
        "mediante una canasta de referencia, mientras que las solicitudes específicas contienen el "
        "target observado."
    ))
    rows = [
        ["Esquema", "Período", "Filas", "Cobertura media", "Alerta media", "Sobres equivalentes medios", "Presupuesto total"],
        ["Específico", "2024–2026", "1.492", "62,84 %", "0,409", "7,74", "$ 5.754.500"],
        ["Kit genérico", "2022–2023", "1.238", "N/A (imputada)", "N/A", "13,47", "$ 7.040.000"],
    ]
    story.append(table(rows, [2.4 * cm, 1.9 * cm, 1.3 * cm, 2.5 * cm, 2.0 * cm, 3.4 * cm, 3.1 * cm],
                       aligns=["left", "center", "center", "center", "center", "center", "center"]))
    story.append(CAPTION("Tabla 2. Distribución por esquema de entrega. El presupuesto se calcula con un valor fijo de $500 por sobre."))
    story.append(CALLOUT(
        "<b>Decisión metodológica.</b> Para entrenar los modelos se utilizan únicamente las "
        "<b>1.487 solicitudes específicas con especies observadas</b>. Los kits genéricos se conservan "
        "en el dataset para auditoría y análisis de volumen, pero no se usan como target de los modelos "
        "principales, porque su contenido de variedades es una imputación y no un dato observado.",
        "info",
    ))

    story.append(H2("2.3. Auditoría y control de calidad", "datos-auditoria"))
    story.append(P(
        "El proceso de preparación aplica controles de reconciliación sobre todas las filas. La Tabla 3 "
        "resume los principales indicadores de calidad. No se eliminó ninguna fila: los problemas se "
        "documentan mediante banderas de calidad (<i>flags</i>) para que puedan auditarse."
    ))
    rows = [
        ["Control técnico", "Resultado"],
        ["Solicitudes totales validadas", "2.730"],
        ["Registros 2022–2023 sin dato explícito de kits", "193"],
        ["Registros 2022–2023 con 0 kits reales", "8"],
        ["Registros 2024–2026 sin texto descriptivo de especies", "5"],
        ["Registros 2024–2026 con conteo de 0 especies", "1"],
        ["Solicitudes sin asignación de barrio (sin_dato)", "786"],
        ["Solicitudes con geolocalización (coordenadas)", "969"],
        ["Solicitudes genéricas con demanda imputada por canasta", "1.037"],
        ["Sobres equivalentes totales imputados (kits × 10)", "14.080"],
    ]
    story.append(table(rows, [11.2 * cm, 5.4 * cm], aligns=["left", "center"]))
    story.append(CAPTION("Tabla 3. Controles de calidad y reconciliación del dataset consolidado."))
    story.append(P(
        "Los registros sin barrio se concentran en 2024 y en la temporada OI 2025, cuyos formularios no "
        "incluían la pregunta de barrio. Esa limitación se explicita en el mapa: la proyección futura "
        "solo cubre los <b>31 barrios mapeados con datos</b>, mientras que el total municipal observado "
        "incluye los registros sin barrio y los barrios fuera de la dimensión geográfica."
    ))

    story.append(H2("2.4. Diccionario resumido de variables", "datos-diccionario"))
    story.append(P(
        "El dataset consolidado <b>solicitudes_v2.csv</b> contiene una fila por solicitud. La Tabla 4 "
        "presenta las variables principales. El diccionario completo se encuentra en "
        "<b>informe/diccionario_datos.md</b>."
    ))
    rows = [
        ["Variable", "Tipo", "Descripción"],
        ["id_solicitud", "texto", "Identificador único: año-temporada-fila."],
        ["anio / temporada", "entero / texto", "Campaña (2022–2026) y temporada OI o PV."],
        ["esquema_entrega", "texto", "kit_generico (2022–2023) o especifico (2024–2026)."],
        ["barrio_norm / barrio_nombre", "texto", "Barrio normalizado y nombre para mostrar."],
        ["tipo_huerta", "texto", "familiar, institucional o no especificado."],
        ["tipo_localizacion", "texto", "urbana, periurbana, rural o no especificado."],
        ["experiencia", "texto", "primera vez, 1 a 3 años, más de 3 años o no especificado."],
        ["superficie", "texto", "hasta 5 m², entre 6 y 20 m², más de 20 m² o no especificado."],
        ["destino", "texto", "autoconsumo, autoconsumo e intercambio, venta / excedentes."],
        ["ocupacion", "texto", "Ocupación agrupada del responsable de la huerta."],
        ["kits", "decimal", "Kits entregados en 2022–2023; nulo si no hay dato."],
        ["cantidad_variedades", "decimal", "Especies distintas solicitadas en 2024–2026."],
        ["especies_equivalentes", "decimal", "kits × 10 (genérico) o cantidad_variedades (específico)."],
        ["oferta_catalogo", "entero", "Especies ofrecidas en el catálogo de la temporada."],
        ["cobertura_catalogo", "decimal", "min(100, especies_equivalentes / oferta × 100)."],
        ["alerta_alta_demanda", "entero", "1 si cobertura ≥ 75 %, 0 en caso contrario."],
        ["presupuesto_estimado", "decimal", "especies_equivalentes × 500."],
        ["flags_calidad", "texto", "Banderas de calidad separadas por punto y coma."],
    ]
    story.append(table(rows, [4.4 * cm, 2.6 * cm, 9.6 * cm], aligns=["left", "center", "left"]))
    story.append(CAPTION("Tabla 4. Diccionario resumido de variables del dataset consolidado."))

    story.append(H2("2.5. Análisis exploratorio", "datos-eda"))
    story.append(P(
        "El análisis exploratorio muestra que la demanda de variedades no es uniforme: un grupo "
        "reducido de especies concentra la mayor parte de las solicitudes. La Tabla 5 presenta el top "
        "diez de especies observadas en las temporadas OI 2025 y OI 2026, utilizado para construir la "
        "canasta de referencia de los kits genéricos."
    ))
    rows = [
        ["#", "Especie", "Solicitudes", "% de solicitudes", "En canasta top 10"],
        ["1", "Perejil", "451", "85,1 %", "Sí"],
        ["2", "Acelga", "441", "83,2 %", "Sí"],
        ["3", "Lechuga", "429", "80,9 %", "Sí"],
        ["4", "Cebolla", "348", "65,7 %", "Sí"],
        ["5", "Remolacha", "345", "65,1 %", "Sí"],
        ["6", "Espinaca", "340", "64,2 %", "Sí"],
        ["7", "Flor", "249", "47,0 %", "Sí"],
        ["8", "Rabanito", "247", "46,6 %", "Sí"],
        ["9", "Habas", "237", "44,7 %", "Sí"],
        ["10", "Rúcula", "155", "29,2 %", "Sí"],
    ]
    story.append(table(rows, [1.0 * cm, 4.6 * cm, 3.0 * cm, 3.6 * cm, 4.4 * cm],
                       aligns=["center", "left", "center", "center", "center"]))
    story.append(CAPTION("Tabla 5. Top 10 de especies observadas en OI 2025–2026 (canasta OI_2025_2026_v1)."))
    story.append(P(
        "La distribución por temporada y año (Tabla 1) evidencia un crecimiento de la oferta de "
        "catálogo: pasó de 9 variedades en 2024 PV a 18 en 2026 PV. Esa variación justifica normalizar "
        "la demanda como <b>cobertura porcentual del catálogo</b> y no solo como cantidad absoluta de "
        "variedades. También explica por qué el modelo principal incorpora el año y la oferta como "
        "variables de contexto."
    ))

    story.append(H2("2.6. Limitaciones de los datos", "datos-limitaciones"))
    story.append(B("Los formularios de 2024 y OI 2025 no registran barrio; por eso una parte importante "
                   "de las solicitudes queda como <b>sin_dato</b> y no puede asignarse al mapa."))
    story.append(B("Los kits genéricos de 2022–2023 no detallan variedades: su composición es una "
                   "imputación basada en la canasta OI 2025–2026, con confianza baja."))
    story.append(B("La serie histórica es corta (siete campañas) y presenta cambios de formulario entre "
                   "años, lo que limita la comparabilidad estricta."))
    story.append(B("El precio de $500 por sobre es un valor fijo de referencia, no un precio de mercado."))
    story.append(PageBreak())
    return story


def section_method() -> list:
    story = [H1("3. Metodología y preparación de datos", "metodo")]
    story.append(H2("3.1. Arquitectura del pipeline", "metodo-pipeline"))
    story.append(P(
        "El flujo de trabajo separa estrictamente la fase <b>offline</b> de preparación y entrenamiento "
        "de la fase <b>online</b> de inferencia. La aplicación web no entrena modelos en tiempo de "
        "ejecución: carga artefactos serializados y ejecuta únicamente <i>predict</i>. Esta separación "
        "garantiza tiempos de respuesta bajos, reproducibilidad y trazabilidad."
    ))
    story.append(FLOW([
        "Excel<br/>7 campañas",
        "preparar_datos.py<br/>limpieza y features",
        "CSV + GeoJSON<br/>datos preparados",
        "Entrenamiento<br/>Pipelines scikit-learn",
        ".joblib<br/>artefactos",
        "Flask + API<br/>inferencia online",
    ]))
    story.append(CAPTION("Figura 1. Flujo general del proyecto: de los formularios Excel a la aplicación web."))

    story.append(H2("3.2. Limpieza, normalización e ingeniería de variables", "metodo-limpieza"))
    story.append(P(
        "El script <b>preparar_datos.py</b> implementa un proceso de limpieza robusto que incluye "
        "corrección de codificación (<i>mojibake</i>), normalización de textos, detección automática de "
        "columnas por patrones y mapeo de categorías. Las principales transformaciones son:"
    ))
    story.append(B("<b>Barrios:</b> normalización a una clave canónica, eliminación de prefijos "
                   "(<i>barrio</i>, <i>B°</i>), resolución de alias y errores de escritura, y asignación "
                   "de <b>sin_dato</b> cuando no hay información."))
    story.append(B("<b>Especies:</b> tokenización por punto y coma, coma o salto de línea, eliminación "
                   "de tokens inválidos (<i>otra</i>, <i>ninguna</i>, etc.) y canonicalización a un "
                   "catálogo controlado de especies."))
    story.append(B("<b>Experiencia:</b> estandarización en tres niveles: primera vez, 1 a 3 años y más "
                   "de 3 años."))
    story.append(B("<b>Superficie:</b> conversión de rangos y textos heterogéneos a tres categorías "
                   "(hasta 5 m², entre 6 y 20 m², más de 20 m²)."))
    story.append(B("<b>Tipo de huerta:</b> consolidación en familiar, institucional o no especificado."))
    story.append(B("<b>Destino y ocupación:</b> agrupamiento de respuestas abiertas en categorías "
                   "comparables."))
    story.append(P(
        "La ingeniería de variables del modelo principal incorpora, además del perfil socio-productivo, "
        "señales históricas agregadas por barrio y temporada: media histórica de sobres, cantidad de "
        "solicitudes, cantidad de años con datos, ratio del barrio frente a la temporada y ratio del "
        "perfil frente al barrio. Estas variables permiten que el modelo combine información individual "
        "con contexto territorial."
    ))

    story.append(H2("3.3. Partición y estratificación", "metodo-particion"))
    story.append(P(
        "Para el modelo principal, el conjunto de <b>1.487 solicitudes específicas</b> se dividió en "
        "entrenamiento, validación y prueba con una proporción 60/20/20. La partición se estratificó "
        "por temporada, año y tercil de demanda, con <b>random_state = 42</b>, para preservar la "
        "proporción de clases y reducir el riesgo de fugas interanuales."
    ))
    rows = [
        ["Conjunto", "Observaciones", "Uso"],
        ["Entrenamiento", "892", "Ajuste de codificadores, escaladores y modelos."],
        ["Validación", "297", "Selección de hiperparámetros, umbrales y calibración."],
        ["Prueba", "298", "Evaluación final, reservada a ciegas."],
    ]
    story.append(table(rows, [4.6 * cm, 3.0 * cm, 9.0 * cm], aligns=["left", "center", "left"]))
    story.append(CAPTION("Tabla 6. Partición del dataset modelado (60/20/20)."))

    story.append(H2("3.4. Prevención de fuga de información (data leakage)", "metodo-leakage"))
    story.append(P(
        "Se aplicaron tres controles para evitar que el modelo aprenda información que no estará "
        "disponible al momento de la predicción:"
    ))
    story.append(N("Se excluyeron del conjunto de predictores las variables derivadas del target: "
                   "<b>cobertura_catalogo</b>, <b>alerta_alta_demanda</b> y <b>presupuesto_estimado</b>.", 1))
    story.append(N("Se excluyó <b>cantidad_variedades</b> bruta, que es el insumo directo del target de "
                   "regresión, y <b>kits</b>, que solo existe en la era genérica.", 2))
    story.append(N("Todo el preprocesamiento se encapsuló en <b>Pipelines</b> y <b>ColumnTransformer</b> "
                   "de scikit-learn, ajustados únicamente sobre el conjunto de entrenamiento.", 3))
    story.append(P(
        "En el módulo climático se detectó y corrigió un caso adicional de fuga: la versión preliminar "
        "usaba <b>Oferta_Catalogo</b> para predecir la cobertura, pero la oferta está matemáticamente "
        "relacionada con el target. El modelo final se reentrenó usando exclusivamente "
        "<b>Precipitaciones_Hist_mm</b>."
    ))
    story.append(PageBreak())
    return story


def section_models() -> list:
    story = [H1("4. Modelado", "modelos")]
    story.append(P(
        "El proyecto implementa dos familias de modelos complementarias. La primera trabaja a nivel de "
        "<b>solicitud</b> y estima la cantidad de sobres equivalentes; se usa para el mapa territorial y "
        "la planificación agregada. La segunda trabaja a nivel de <b>perfil de huerta</b> y estima la "
        "cobertura del catálogo y la alerta de alta demanda; se usa en el módulo de control de stock. "
        "A ellas se suma un modelo climático simple para el módulo de lluvias."
    ))
    story.append(CALLOUT(
        "<b>Unidad de medida.</b> Un <b>sobre equivalente</b> representa una variedad solicitada. "
        "En 2022–2023 se calcula como <i>kits × 10</i>; en 2024–2026 coincide con la cantidad de "
        "variedades observadas. El valor de referencia presupuestario es de <b>$500 por sobre</b>.",
        "info",
    ))

    story.append(H2("4.1. Modelo de regresión de demanda", "modelos-regresion"))
    story.append(H3("4.1.1. Variable objetivo y predictores"))
    story.append(P(
        "El target es <b>especies_equivalentes</b>. Sus estadísticas descriptivas sobre el conjunto "
        "modelado son: media 7,74; mediana 8; desvío estándar 3,75; mínimo 0 y máximo 29. El modelo "
        "recibe trece predictores: año indexado, temporada, tipo de huerta, tipo de localización, "
        "experiencia, superficie, destino, ocupación, media histórica del barrio, cantidad histórica "
        "de solicitudes, cantidad de años históricos, ratio barrio/temporada y ratio perfil/barrio."
    ))
    story.append(P(
        "Las variables se procesan mediante un <b>ColumnTransformer</b>: las numéricas se estandarizan "
        "con <b>StandardScaler</b> y las categóricas se codifican con <b>OneHotEncoder</b>. Esto es "
        "especialmente importante para KNN, que depende de distancias entre observaciones."
    ))
    story.append(H3("4.1.2. Comparación de algoritmos"))
    story.append(P(
        "Se compararon distintos algoritmos y configuraciones sobre el conjunto de validación. La "
        "Tabla 7 muestra los cinco mejores resultados por RMSE. El <b>KNeighborsRegressor con k = 41</b> "
        "obtuvo el menor error y fue seleccionado."
    ))
    rows = [
        ["Algoritmo e hiperparámetros", "RMSE", "MAE", "R²"],
        ["KNeighborsRegressor (k=41, weights=uniform)", "3,543", "2,669", "0,1957"],
        ["KNeighborsRegressor (k=21, weights=uniform)", "3,583", "2,693", "0,1775"],
        ["Ridge (alpha=1000.0)", "3,605", "2,706", "0,1669"],
        ["RandomForestRegressor (depth=6, leaf=3)", "3,626", "2,699", "0,1575"],
        ["RandomForestRegressor (depth=4, leaf=5)", "3,635", "2,718", "0,1532"],
    ]
    story.append(table(rows, [8.2 * cm, 2.6 * cm, 2.6 * cm, 3.2 * cm],
                       aligns=["left", "center", "center", "center"]))
    story.append(CAPTION("Tabla 7. Comparación de algoritmos de regresión en validación (fuente: comparacion_regresion.csv)."))
    story.append(H3("4.1.3. Calibración estacional"))
    story.append(P(
        "Las predicciones crudas presentaban un sesgo sistemático por temporada. Se aplicó un factor "
        "de calibración multiplicativo: <b>1,0815 para OI</b> y <b>1,0745 para PV</b>. La calibración "
        "mejora levemente el RMSE y el MAE de validación, aunque no corrige la baja varianza explicada "
        "a nivel individual."
    ))
    story.append(H3("4.1.4. Métricas finales"))
    rows = [
        ["Conjunto", "RMSE", "MAE", "R²"],
        ["Entrenamiento", "2,793", "2,119", "0,4466"],
        ["Validación (cruda)", "3,543", "2,669", "0,1957"],
        ["Validación (calibrada)", "3,498", "2,652", "0,2158"],
        ["Prueba (cruda)", "3,327", "2,574", "0,0999"],
        ["Prueba (calibrada)", "3,393", "2,602", "0,0644"],
    ]
    story.append(table(rows, [5.4 * cm, 3.4 * cm, 3.4 * cm, 4.4 * cm],
                       aligns=["left", "center", "center", "center"]))
    story.append(CAPTION("Tabla 8. Métricas de regresión por conjunto. La validación cruzada de 5 folds arroja RMSE = 2,865."))
    story.append(H3("4.1.5. Backtest temporal"))
    story.append(P(
        "Para evaluar la capacidad de generalización temporal se entrenó con 2024–2025 y se evaluó en "
        "2026. El modelo obtuvo un RMSE de 5,296 frente a 5,500 del baseline ingenuo, un MAE de 4,006 "
        "frente a 4,073 y un R² de −0,131. La mejora es marginal: el modelo apenas supera al baseline "
        "y no captura de forma robusta la variación interanual."
    ))
    rows = [
        ["Métrica", "Modelo", "Baseline ingenuo"],
        ["RMSE", "5,296", "5,500"],
        ["MAE", "4,006", "4,073"],
        ["R²", "−0,131", "—"],
    ]
    story.append(table(rows, [5.0 * cm, 5.8 * cm, 5.8 * cm], aligns=["left", "center", "center"]))
    story.append(CAPTION("Tabla 9. Backtest temporal: entrenamiento 2024–2025, evaluación 2026."))
    story.append(CALLOUT(
        "<b>Lectura crítica.</b> El MAE de prueba (2,60 sobres) representa aproximadamente el 33,6 % de "
        "la media del target (7,74). El R² de prueba es bajo (0,064) y la brecha entrenamiento–prueba "
        "es amplia (0,382). En consecuencia, el modelo <b>no es adecuado para decisiones individuales</b>: "
        "se utiliza para estimar totales agregados por barrio y temporada, donde los errores tienden a "
        "compensarse.",
        "warn",
    ))

    story.append(H2("4.2. Modelo de clasificación y alerta de alta demanda", "modelos-clasificacion"))
    story.append(H3("4.2.1. Variable objetivo y umbral"))
    story.append(P(
        "La variable binaria <b>alerta_alta_demanda</b> vale 1 cuando la cobertura del catálogo es "
        "igual o superior al <b>75 %</b>, es decir, cuando la solicitud pide al menos tres de cada "
        "cuatro variedades disponibles. Ese umbral es el punto de inflexión operativo a partir del cual "
        "conviene preparar anticipadamente un kit casi completo. La cobertura se define como:"
    ))
    story.append(FORMULA("cobertura_catalogo = min(100, especies_equivalentes / oferta_catalogo × 100)"))
    story.append(Spacer(1, 0.18 * cm))
    story.append(P(
        "Se evaluaron distintas configuraciones de árboles de decisión, con y sin balanceo de clases, y "
        "distintos umbrales de decisión. La Tabla 10 resume la mejor configuración encontrada y el "
        "efecto del ajuste de umbral."
    ))
    rows = [
        ["Configuración", "Precision", "Recall", "F1", "F2", "Costo"],
        ["Árbol depth=5, hoja=1, entropía (umbral 0,50)", "0,531", "0,779", "0,631", "0,712", "138"],
        ["Árbol depth=5, hoja=1, entropía (umbral 0,37)", "0,517", "0,877", "0,650", "0,770", "130"],
    ]
    story.append(table(rows, [7.3 * cm, 2.0 * cm, 2.0 * cm, 1.6 * cm, 1.6 * cm, 2.1 * cm],
                       aligns=["left", "center", "center", "center", "center", "center"]))
    story.append(CAPTION("Tabla 10. Evaluación del clasificador de alta demanda (fuente: comparacion_clasificacion.csv)."))
    story.append(P(
        "El ajuste del umbral a 0,37 reduce los falsos negativos de 27 a 15 y baja el costo total de "
        "138 a 130, a costa de aumentar los falsos positivos de 84 a 100. Esta decisión es coherente "
        "con el esquema de costos adoptado.",
        "body_keep",
    ))
    story.append(H3("4.2.2. Esquema de costos"))
    story.append(P(
        "El proyecto asigna un costo social y operativo asimétrico a los errores del clasificador:"
    ))
    story.append(B("<b>Falso positivo (FP):</b> se predice alta demanda, pero la persona solicita un kit "
                   "acotado. Se preparó un kit completo de más; los sobres no retirados se reasignan. "
                   "Costo asignado: <b>1 unidad</b>."))
    story.append(B("<b>Falso negativo (FN):</b> se predice demanda estándar, pero la persona necesitaba "
                   "un kit completo. Faltan variedades en el mostrador y se afecta la diversidad de la "
                   "huerta. Costo asignado: <b>2 unidades</b>."))
    story.append(FORMULA("Costo total = 1 × FP + 2 × FN"))
    story.append(Spacer(1, 0.18 * cm))
    story.append(P(
        "Por eso los hiperparámetros y umbrales se ajustaron priorizando el <b>Recall</b> y el "
        "<b>F2-Score</b> por sobre la precisión. En el módulo de stock se muestran dos sistemas "
        "independientes —regresión con umbral y clasificador directo— para que el usuario detecte casos "
        "dudosos y, ante una discrepancia, opte por preparar el kit completo."
    ))

    story.append(H2("4.3. Modelo climático", "modelos-clima"))
    story.append(P(
        "El módulo de análisis climático estima cómo varía la cobertura del catálogo según las "
        "precipitaciones históricas. El modelo final es una <b>regresión lineal simple</b> entrenada "
        "únicamente con <b>Precipitaciones_Hist_mm</b>, luego de detectar y eliminar una fuga de "
        "información asociada a <b>Oferta_Catalogo</b>."
    ))
    story.append(FORMULA("cobertura_estimada (%) = 55,4973 + 0,013267 × precipitaciones (mm)"))
    story.append(Spacer(1, 0.18 * cm))
    story.append(P(
        "El coeficiente indica que cada 100 mm adicionales de lluvia se asocian con un aumento de "
        "aproximadamente <b>1,33 puntos porcentuales</b> en la cobertura estimada. La salida se acota "
        "lógicamente entre 0 % y 100 %. La interfaz clasifica el escenario en sequía, régimen promedio "
        "o precipitaciones intensas según la temporada y los milímetros ingresados."
    ))

    story.append(H2("4.4. Regla de alerta territorial", "modelos-alerta"))
    story.append(P(
        "Para el mapa de demanda, la alerta no se dispara con el clasificador individual sino con una "
        "regla de negocio sobre la proyección agregada por barrio. Un barrio queda en alerta cuando la "
        "demanda proyectada supera el baseline histórico y se cumplen dos condiciones simultáneas:"
    ))
    story.append(FORMULA("predicho > esperado × (1 + 0,10)   Y   (predicho − esperado) ≥ 10 sobres"))
    story.append(Spacer(1, 0.18 * cm))
    story.append(P(
        "El doble criterio evita falsas alarmas en barrios pequeños, donde una variación porcentual "
        "grande puede originarse en una base mínima. El baseline se calcula como la media anual histórica "
        "de sobres por barrio y temporada, ajustada por un crecimiento anual supuesto del 5 %:"
    ))
    story.append(FORMULA("esperado(año) = media_anual_sobres × (1 + 0,05)^(año − último_año)"))
    story.append(Spacer(1, 0.18 * cm))
    story.append(P(
        "Los barrios con menos de <b>10 solicitudes históricas</b> o menos de <b>2 años de datos</b> se "
        "marcan como <b>muestra limitada</b>, y la alerta se acompaña de una advertencia de cautela. La "
        "proyección se calcula para 2027 y 2028, repitiendo la última oferta de catálogo observada y "
        "aplicando el crecimiento supuesto. Se trata de <b>escenarios base</b>, no de pronósticos "
        "validados."
    ))
    story.append(PageBreak())
    return story


def section_app() -> list:
    story = [H1("5. Arquitectura de la aplicación", "app")]
    story.append(H2("5.1. Visión general", "app-vision"))
    story.append(P(
        "La aplicación es una <b>aplicación web Flask</b> con renderizado del lado del servidor mediante "
        "plantillas Jinja2, estilos CSS propios y JavaScript para las visualizaciones interactivas. Los "
        "modelos se cargan desde archivos <b>.joblib</b> al iniciar el proceso; las consultas se "
        "responden con inferencia en memoria y sin base de datos. El despliegue en producción se realiza "
        "en <b>Vercel</b> mediante el runtime <b>@vercel/python</b>."
    ))
    story.append(FLOW([
        "Usuario<br/>navegador",
        "Flask<br/>rutas y API",
        "Modelos<br/>.joblib",
        "Datos<br/>CSV + GeoJSON",
        "Respuesta<br/>HTML / JSON",
        "Visualización<br/>deck.gl + Chart.js",
    ], color=BLUE))
    story.append(CAPTION("Figura 2. Arquitectura lógica de la aplicación y flujo de una consulta."))

    story.append(H2("5.2. Estructura del repositorio", "app-estructura"))
    rows = [
        ["Elemento", "Contenido"],
        ["app.py", "Aplicación Flask principal: rutas, API, carga de modelos y lógica de agregación territorial."],
        ["dash_app.py", "Prototipo alternativo de tablero en Dash (puerto 8050). No es necesario para el despliegue principal."],
        ["preparar_datos.py", "Pipeline de consolidación, limpieza, normalización y generación de CSVs auditados."],
        ["logica_demanda.py", "Reglas de negocio de variación, alertas y calidad de muestra, independientes de Flask."],
        ["logica_lluvias.py", "Carga y uso del modelo climático purgado."],
        ["entrenar_guardar_modelos.py", "Entrenamiento de los modelos de cobertura y clasificación del módulo de stock."],
        ["act_lluvia.py / entrenar_modelo_lluvias.py", "Reentrenamiento del modelo climático; la versión vigente es la purgada."],
        ["modelos/", "Artefactos .joblib y metadata_modelos.json."],
        ["templates/", "Vistas Jinja2: portada, inicio, mapa, inventario, lluvias e informe."],
        ["static/", "CSS, JavaScript, imágenes y basemap de Chascomús."],
        ["datos/preparados/", "CSVs consolidados, especies, catálogo, canasta y dimensión de barrios."],
        ["datos/geospatial/", "GeoJSON de barrios, radios censales y extensiones territoriales."],
        ["informe/", "Auditoría, diccionario, comparación de modelos y predicciones de test."],
    ]
    story.append(table(rows, [4.6 * cm, 12.0 * cm], aligns=["left", "left"]))
    story.append(CAPTION("Tabla 11. Estructura principal del repositorio."))

    story.append(H2("5.3. Módulos y vistas", "app-vistas"))
    story.append(P(
        "La navegación se unifica mediante un diccionario centralizado <b>NAV_URLS</b> inyectado por un "
        "procesador de contexto de Flask. La Tabla 12 describe las seis vistas principales."
    ))
    rows = [
        ["Vista", "Ruta", "Función principal"],
        ["Portada", "/", "Presentación institucional, iniciativa, objetivos y acceso al sistema."],
        ["Inicio", "/inicio", "Panel de acceso a herramientas y KPIs reales del proyecto."],
        ["Mapa de demanda", "/mapa", "Mapa 3D por barrio, comparativa, tendencia y alertas de sobredemanda."],
        ["Control de stock", "/inventario", "Simulación de cobertura por perfil de huerta y doble alerta."],
        ["Análisis climático", "/lluvias", "Estimación del impacto de las precipitaciones en la cobertura."],
        ["Informe de datos", "/informe", "Documentación técnica, variables, métricas y limitaciones."],
    ]
    story.append(table(rows, [3.6 * cm, 3.0 * cm, 10.0 * cm], aligns=["left", "center", "left"]))
    story.append(CAPTION("Tabla 12. Vistas principales de la aplicación."))

    story.append(H3("Mapa de demanda"))
    story.append(P(
        "El mapa utiliza <b>deck.gl</b> para renderizar un basemap satelital de Chascomús, los polígonos "
        "de los barrios y columnas 3D extruidas que comparan la demanda de referencia con la proyectada. "
        "El panel lateral permite filtrar por <b>temporada, año, variable</b> (sobres, solicitudes o "
        "presupuesto) y <b>barrio</b>. Al seleccionar un barrio se muestra su detalle: valores de "
        "referencia y proyección, variación porcentual, estado de alerta, muestra histórica, superficie, "
        "radios censales y especies más solicitadas. Debajo se presentan una comparativa por barrio "
        "(Chart.js) y una serie de tendencia con datos observados, baseline y proyección."
    ))
    story.append(H3("Control de stock"))
    story.append(P(
        "El formulario de control de stock recibe el perfil de una solicitud (temporada, año, "
        "localización, tipo de huerta, experiencia, superficie, destino y ocupación) y estima la "
        "cobertura porcentual del catálogo. A partir de esa estimación se muestran dos alertas: la "
        "regresión con umbral (≥ 75 %) y el clasificador directo. Si ambos coinciden, la interfaz lo "
        "indica; si discrepan, recomienda preparar el kit completo porque el falso negativo cuesta el "
        "doble. El módulo usa los modelos <b>modelo_regresion_cobertura.joblib</b> y "
        "<b>modelo_clasificacion_dash.joblib</b>."
    ))
    story.append(H3("Análisis climático"))
    story.append(P(
        "El módulo de lluvias recibe temporada, año y milímetros esperados. A partir de esos datos "
        "estima la cobertura con el modelo lineal purgado y presenta un semáforo de impacto: sequía, "
        "régimen promedio o precipitaciones intensas. El resultado se acota entre 0 % y 100 % y se "
        "contextualiza con los promedios históricos de 650 mm para PV y 380 mm para OI."
    ))

    story.append(H2("5.4. API REST", "app-api"))
    story.append(P(
        "El backend expone una API JSON que alimenta las vistas y permite integraciones futuras. La "
        "Tabla 13 resume los endpoints principales."
    ))
    rows = [
        ["Método", "Ruta", "Descripción"],
        ["GET", "/api/health", "Estado del servicio, versión del modelo, filas, barrios, años de proyección y umbrales."],
        ["GET", "/api/filtros", "Períodos disponibles, barrios mapeados, margen de sobredemanda y precio del sobre."],
        ["GET", "/api/mapa_completo?anio=&temporada=", "Datos agregados por barrio, series de ciudad, escenarios y resúmenes territorial y municipal."],
        ["GET", "/api/consulta_especifica?barrio=&anio=&temporada=", "Detalle de un barrio: métricas, geometría, centroide y especies."],
        ["POST", "/api/prediccion", "Predicción puntual de sobres equivalentes y presupuesto a partir de un perfil."],
    ]
    story.append(table(rows, [1.5 * cm, 6.3 * cm, 8.8 * cm], aligns=["center", "left", "left"]))
    story.append(CAPTION("Tabla 13. Endpoints principales de la API Flask."))
    story.append(P(
        "El endpoint <b>/api/mapa_completo</b> es el más complejo: integra la proyección por barrio, el "
        "baseline, las alertas, el resumen territorial (solo barrios mapeados con datos) y el resumen "
        "municipal observado (incluye registros sin barrio). Esta separación es explícita en la "
        "respuesta para evitar comparaciones engañosas entre universos distintos."
    ))

    story.append(H2("5.5. Frontend y visualización", "app-frontend"))
    story.append(P(
        "La interfaz utiliza <b>Bootstrap 5</b> con el tema <b>Darkly</b>, íconos de Bootstrap Icons y "
        "la tipografía <b>Inter</b>. Los estilos propios se concentran en <b>static/css/prohuerta.css</b> "
        "y <b>portada.css</b>. La lógica de estado de los filtros se comparte en "
        "<b>static/js/common.js</b>, que persiste la selección en <b>localStorage</b> y en la "
        "querystring. Las visualizaciones del mapa se implementan en <b>static/js/mapa.js</b> con "
        "deck.gl y Chart.js. El diseño es responsivo y contempla navegación móvil."
    ))
    story.append(CALLOUT(
        "<b>Accesibilidad y transparencia.</b> Las vistas incluyen etiquetas ARIA, textos alternativos "
        "y advertencias visibles sobre el alcance de las estimaciones. El mapa distingue visualmente "
        "referencia, proyección, estabilidad, aumento y alerta de sobredemanda.",
        "info",
    ))

    story.append(H2("5.6. Despliegue y ejecución local", "app-despliegue"))
    story.append(P(
        "El despliegue en producción se realiza en <b>Vercel</b>. El archivo <b>vercel.json</b> declara "
        "el runtime <b>@vercel/python</b> y redirige todas las rutas a <b>app.py</b>. Como la aplicación "
        "no entrena en vivo ni depende de una base de datos pesada, la inferencia se ejecuta en "
        "milisegundos y el entorno gratuito es suficiente para la demo académica. La aplicación está "
        "disponible en <b>https://pro-huerta.vercel.app/</b>."
    ))
    story.append(P(
        "Para ejecutarla localmente se requiere Python y las dependencias de <b>requirements.txt</b>. "
        "El comando <b>python app.py</b> inicia el servidor en <b>http://localhost:5000</b>. La Tabla 14 "
        "resume las dependencias principales."
    ))
    rows = [
        ["Librería", "Versión", "Uso"],
        ["Flask", "3.0.3", "Backend web, rutas y API."],
        ["scikit-learn", "1.9.1", "Pipelines, preprocesamiento, modelos y métricas."],
        ["pandas / numpy", "2.2.3 / 2.1.2", "Manipulación de datos y cálculo numérico."],
        ["joblib", "1.4.2", "Serialización y carga de modelos."],
        ["Dash / Plotly", "≥ 2.17 / ≥ 5.22", "Prototipo alternativo de tablero."],
        ["gunicorn", "23.0.0", "Servidor WSGI para despliegue."],
    ]
    story.append(table(rows, [4.0 * cm, 3.4 * cm, 9.2 * cm], aligns=["left", "center", "left"]))
    story.append(CAPTION("Tabla 14. Dependencias principales del proyecto (requirements.txt)."))
    story.append(PageBreak())
    return story


def section_results() -> list:
    story = [H1("6. Resultados y discusión", "resultados")]
    story.append(H2("6.1. Desempeño del modelo de regresión", "resultados-regresion"))
    story.append(P(
        "El modelo de regresión logra un ajuste aceptable en entrenamiento (R² = 0,447) pero pierde "
        "capacidad explicativa en validación (R² = 0,216 calibrado) y prueba (R² = 0,064). El MAE de "
        "prueba calibrado es de 2,60 sobres, sobre una media de 7,74. En términos relativos, el error "
        "ronda el 33,6 % del valor medio. El backtest temporal confirma la dificultad: el RMSE apenas "
        "mejora al baseline ingenuo (5,30 vs. 5,50) y el R² es negativo (−0,131)."
    ))
    story.append(P(
        "Estos resultados no invalidan el sistema, pero delimitan su uso. La predicción individual es "
        "ruidosa porque la decisión de cada familia depende de factores no registrados en el formulario "
        "(preferencias, disponibilidad de semillas, clima, decisiones del momento). En cambio, al sumar "
        "muchas solicitudes por barrio y temporada, los errores individuales tienden a compensarse y la "
        "estimación agregada resulta más estable. Por eso el producto se diseña como una herramienta de "
        "<b>planificación territorial</b> y no como un predictor de casos puntuales."
    ))
    story.append(H2("6.2. Desempeño del clasificador y del sistema de alertas", "resultados-clasificacion"))
    story.append(P(
        "El clasificador de alta demanda, ajustado a un umbral de 0,37, alcanza un <b>Recall de 0,877</b> "
        "y un <b>F2 de 0,770</b>, con un costo total de 130. La prioridad es detectar la mayor cantidad "
        "posible de solicitudes de alta demanda, aun a costa de un aumento de falsos positivos. En un "
        "contexto donde un falso negativo deja a una familia sin variedades y un falso positivo solo "
        "inmoviliza stock temporalmente, esta asimetría es razonable."
    ))
    story.append(P(
        "La convivencia de dos sistemas —regresión con umbral y clasificador directo— aporta "
        "transparencia: cuando ambos coinciden, la decisión es más confiable; cuando discrepan, el "
        "usuario recibe una advertencia y puede optar por la alternativa más conservadora. Esta doble "
        "lectura es una decisión de diseño orientada a la gestión del riesgo logístico."
    ))
    story.append(H2("6.3. Interpretación operativa", "resultados-operativo"))
    story.append(P(
        "El sistema permite responder cuatro preguntas de gestión:"
    ))
    story.append(N("<b>¿Cuánto se espera demandar?</b> Mediante la proyección de sobres por barrio y "
                   "temporada, con comparación contra el baseline histórico.", 1))
    story.append(N("<b>¿Dónde se concentra el riesgo?</b> Mediante el mapa 3D, las alertas de "
                   "sobredemanda y el listado de prioridades a reforzar.", 2))
    story.append(N("<b>¿Qué perfil de huerta requiere un kit completo?</b> Mediante el módulo de stock y "
                   "la cobertura estimada del catálogo.", 3))
    story.append(N("<b>¿Cómo puede afectar el clima?</b> Mediante el módulo de lluvias y el escenario "
                   "hídrico simulado.", 4))
    story.append(H2("6.4. Limitaciones y advertencias", "resultados-limitaciones"))
    story.append(P("El informe y la propia aplicación explicitan las siguientes limitaciones:"))
    story.append(B("Las proyecciones 2027–2028 repiten la oferta de catálogo de 2026 y aplican un "
                   "crecimiento supuesto del 5 %: son <b>escenarios</b>, no pronósticos validados."))
    story.append(B("El resumen territorial suma solo los barrios mapeados con datos; los registros sin "
                   "barrio y los barrios fuera de la dimensión geográfica no se incluyen en la "
                   "proyección futura."))
    story.append(B("Los años 2024 y OI 2025 no tienen barrio en el formulario original; el baseline "
                   "barrial usa solo los años con barrio."))
    story.append(B("El precio de $500 por sobre es un valor fijo supuesto, no un precio de mercado."))
    story.append(B("La alerta es una regla de decisión sobre la proyección, no una probabilidad "
                   "calibrada."))
    story.append(B("El desempeño individual del modelo es limitado; no debe usarse para decidir sobre "
                   "una familia en particular."))
    story.append(B("La muestra histórica es corta y los formularios cambian entre campañas, lo que "
                   "limita la comparabilidad y la robustez de las series."))
    story.append(H2("6.5. Aportes del proyecto", "resultados-aportes"))
    story.append(B("<b>Integración completa:</b> datos, modelos, reglas de negocio, API, interfaz y "
                   "despliegue en un solo sistema reproducible."))
    story.append(B("<b>Auditoría y trazabilidad:</b> cada transformación y cada bandera de calidad queda "
                   "documentada; el dataset conserva todas las filas."))
    story.append(B("<b>Prevención de fuga de información:</b> exclusión de variables derivadas del target "
                   "y corrección explícita del modelo climático."))
    story.append(B("<b>Visualización territorial:</b> mapa 3D interactivo con comparación referencia vs. "
                   "proyección y alertas por barrio."))
    story.append(B("<b>Transparencia:</b> métricas honestas, limitaciones visibles y advertencias en la "
                   "interfaz."))
    story.append(PageBreak())
    return story


def section_conclusions() -> list:
    story = [H1("7. Conclusiones", "conclusiones")]
    story.append(P(
        "El proyecto cumplió el objetivo de construir un flujo completo de aprendizaje automático para "
        "un problema real de planificación logística en el Banco de Semillas de Chascomús. Se consolidó "
        "un dataset de 2.730 solicitudes, se auditó su calidad, se construyeron modelos de regresión y "
        "clasificación con pipelines reproducibles, se definieron reglas de alerta explícitas y se "
        "desplegó una aplicación web con visualización territorial."
    ))
    story.append(P(
        "La principal enseñanza metodológica es que el valor de un modelo no depende solo de su métrica "
        "individual, sino de la coherencia entre el problema, la unidad de decisión y el uso previsto. "
        "El modelo de regresión no es preciso para anticipar el pedido de una familia, pero sí aporta "
        "información útil cuando se lo utiliza para estimar totales agregados por barrio y temporada. "
        "La decisión de diseñar el sistema como apoyo a la planificación —y no como asignador "
        "automático— es parte central del aprendizaje."
    ))
    story.append(P(
        "La segunda enseñanza es la importancia de la transparencia. El informe documenta las métricas "
        "reales, las limitaciones de la muestra, los supuestos de proyección y los riesgos de fuga de "
        "información. Esa honestidad no debilita el trabajo: lo vuelve defendible, reproducible y "
        "mejorable. El sistema queda preparado para incorporar nuevas campañas, reentrenar los modelos "
        "y ampliar la cobertura territorial a medida que los formularios registren el barrio de manera "
        "sistemática."
    ))
    story.append(CALLOUT(
        "<b>Conclusión final.</b> El sistema transforma un conjunto disperso de formularios en "
        "información accionable para la planificación logística, presupuestaria y territorial, con un "
        "diseño metodológicamente riguroso y una interfaz pensada para usuarios no técnicos.",
        "key",
    ))
    story.append(PageBreak())
    return story


def section_future() -> list:
    story = [H1("8. Trabajo futuro", "futuro")]
    story.append(P("A partir de las limitaciones identificadas, se proponen las siguientes líneas de mejora:"))
    story.append(N("<b>Mejorar la captura de datos:</b> incorporar el barrio de manera obligatoria en "
                   "todos los formularios y estandarizar las opciones de respuesta.", 1))
    story.append(N("<b>Ampliar la serie histórica:</b> sumar nuevas campañas y evaluar modelos con "
                   "validación temporal más robusta (walk-forward).", 2))
    story.append(N("<b>Enriquecer variables:</b> incorporar datos climáticos reales por campaña, "
                   "disponibilidad de stock y características del catálogo provincial.", 3))
    story.append(N("<b>Modelos probabilísticos:</b> reemplazar la alerta binaria por una estimación de "
                   "probabilidad calibrada y intervalos de confianza.", 4))
    story.append(N("<b>Optimización logística:</b> conectar la proyección con un modelo de asignación de "
                   "inventario y de armado de kits.", 5))
    story.append(N("<b>Integración institucional:</b> evaluar una base de datos compartida con el "
                   "municipio y el INTA para actualizar los datos sin intervención manual.", 6))
    story.append(N("<b>Monitoreo en producción:</b> registrar predicciones y resultados reales para "
                   "medir deriva (drift) y reentrenar con evidencia.", 7))
    story.append(PageBreak())
    return story


def section_refs() -> list:
    story = [H1("9. Referencias", "refs")]
    refs = [
        "Documentación oficial de Flask. <i>Flask Documentation</i>. https://flask.palletsprojects.com/",
        "Documentación oficial de scikit-learn. <i>scikit-learn: Machine Learning in Python</i>. "
        "https://scikit-learn.org/stable/",
        "Documentación oficial de pandas. <i>pandas: Python Data Analysis Library</i>. "
        "https://pandas.pydata.org/docs/",
        "Documentación oficial de NumPy. <i>NumPy Reference</i>. https://numpy.org/doc/",
        "Documentación oficial de deck.gl. <i>deck.gl: WebGL-powered visualization</i>. "
        "https://deck.gl/docs",
        "Documentación oficial de Chart.js. <i>Chart.js Documentation</i>. https://www.chartjs.org/docs/",
        "Documentación oficial de Vercel. <i>Vercel Python Runtime</i>. https://vercel.com/docs",
        "INTA. <i>Programa ProHuerta</i>. https://www.argentina.gob.ar/inta/prohuerta",
        "Municipalidad de Chascomús. <i>Banco de Intercambio de Semillas</i>. "
        "https://www.chascomus.gob.ar/",
    ]
    for r in refs:
        story.append(B(r))
    story.append(PageBreak())
    return story


def section_annex() -> list:
    story = [H1("Anexos", "anexos")]
    story.append(H2("Anexo A. Estructura de archivos generados", "anexo-a"))
    rows = [
        ["Archivo", "Contenido"],
        ["datos/preparados/solicitudes_v2.csv", "Una fila por solicitud, con targets, categorías y flags de calidad."],
        ["datos/preparados/solicitud_especies.csv", "Una fila por solicitud y especie observada (2024–2026)."],
        ["datos/preparados/solicitud_especies_imputada.csv", "Canasta imputada para kits genéricos 2022–2023."],
        ["datos/preparados/solicitud_especies_completa.csv", "Unión de especies observadas e imputadas."],
        ["datos/preparados/canasta_oi_referencia.csv", "Ranking de especies OI y porcentaje de solicitudes."],
        ["datos/preparados/catalogo_temporada.csv", "Oferta de catálogo y valor del sobre por temporada."],
        ["datos/preparados/dim_barrios.csv", "Barrios, conteos, coordenadas y años con datos."],
        ["informe/auditoria_datos.md", "Auditoría de fuentes, reconciliación y calidad."],
        ["informe/diccionario_datos.md", "Diccionario completo de variables y fórmulas."],
        ["informe/comparacion_regresion.csv", "Comparación de algoritmos de regresión."],
        ["informe/comparacion_clasificacion.csv", "Comparación de configuraciones del clasificador."],
        ["informe/predicciones_test.csv", "Predicciones sobre el conjunto de prueba."],
    ]
    story.append(table(rows, [8.2 * cm, 8.4 * cm], aligns=["left", "left"], font_size=7.9, pad=3))
    story.append(CAPTION("Tabla A1. Archivos principales generados por el pipeline y el entrenamiento."))

    story.append(H2("Anexo B. Reproducibilidad", "anexo-b"))
    story.append(P("Los pasos para reproducir el proyecto desde cero son los siguientes:"))
    story.append(N("Crear un entorno virtual e instalar dependencias: <b>pip install -r requirements.txt</b>.", 1))
    story.append(N("Regenerar los datos preparados: <b>python preparar_datos.py</b>.", 2))
    story.append(N("Reentrenar los modelos de stock: <b>python entrenar_guardar_modelos.py</b>.", 3))
    story.append(N("Reentrenar el modelo climático purgado: <b>python act_lluvia.py</b>.", 4))
    story.append(N("Iniciar la aplicación: <b>python app.py</b> y abrir <b>http://localhost:5000</b>.", 5))
    story.append(P(
        "El proyecto también puede desplegarse en Vercel conectando el repositorio. El archivo "
        "<b>vercel.json</b> ya contiene la configuración necesaria."
    ))

    story.append(H2("Anexo C. Glosario", "anexo-c"))
    rows = [
        ["Término", "Definición"],
        ["Sobre equivalente", "Unidad que representa una variedad de semilla solicitada."],
        ["Cobertura del catálogo", "Porcentaje de variedades del catálogo que solicita una persona."],
        ["Alta demanda", "Cobertura igual o superior al 75 % del catálogo de la temporada."],
        ["Baseline", "Referencia histórica de demanda por barrio y temporada, ajustada por crecimiento."],
        ["Sobredemanda", "Proyección que supera el baseline en al menos 10 % y 10 sobres."],
        ["Muestra limitada", "Barrio con menos de 10 solicitudes o menos de 2 años de datos."],
        ["Data leakage", "Uso de información no disponible al momento de predecir, que infla el desempeño."],
        ["Pipeline", "Secuencia reproducible de preprocesamiento y modelo de scikit-learn."],
        ["Escenario base", "Proyección construida con supuestos explícitos, no un pronóstico validado."],
    ]
    story.append(table(rows, [4.6 * cm, 12.0 * cm], aligns=["left", "left"], font_size=7.9, pad=3))
    story.append(CAPTION("Tabla C1. Glosario de términos utilizados en el informe."))
    story.append(CALLOUT(
        "<b>Nota de entrega.</b> Este informe se complementa con el repositorio del proyecto, la "
        "aplicación desplegada y los archivos de auditoría y métricas citados. Los campos "
        "<b>Docente</b> y <b>Comisión</b> de la portada deben completarse antes de la entrega final.",
        "warn",
    ))
    return story


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build() -> None:
    story = []
    story += cover()
    story += executive_summary()
    story += toc()
    story += section_intro()
    story += section_data()
    story += section_method()
    story += section_models()
    story += section_app()
    story += section_results()
    story += section_conclusions()
    story += section_future()
    story += section_refs()
    story += section_annex()

    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=LM,
        rightMargin=RM,
        topMargin=TM,
        bottomMargin=BM,
        title="Informe Final de Entrega - ProHuerta Chascomús",
        author="Barreu, Quiroga, Pérez Cazal",
        subject="Modelos de Aprendizaje Automático - Trabajo Práctico Integrador",
        creator="ProHuerta Chascomús",
    )
    frame = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="normal")
    # La portada no lleva encabezado: se dibuja con un template aparte.
    cover_frame = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="cover")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=on_first_page),
        PageTemplate(id="main", frames=[frame], onPage=on_later_pages),
    ])

    doc.multiBuild(story, canvasmaker=NumberedCanvas)
    print("PDF generado:", OUTPUT)
    print("Páginas:", doc.page)


if __name__ == "__main__":
    build()
