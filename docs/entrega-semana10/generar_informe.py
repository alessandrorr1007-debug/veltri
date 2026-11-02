"""Compone el informe desde evidencias guardadas; no ejecuta modelos ni usa red."""

import hashlib
import json
import math
import textwrap
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from docx.styles.style import ParagraphStyle
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
E = ROOT / "docs/evidencias/semana10-entrega-final"
F = OUT / "figuras"
F.mkdir(exist_ok=True)
ej = json.loads((E / "ejecuciones.json").read_text(encoding="utf-8"))
remote = json.loads((ROOT / "docs/evidencias/semana10-fase43/ejecucion-unica.json").read_text())
FONT = "C:/Windows/Fonts/arial.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"
INK = "#183047"


def canvas(w, h, title):
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    d.text((30, 18), title, font=ImageFont.truetype(BOLD, 30), fill=INK)
    return im, d


def box(d, xy, text, size=36):
    d.rounded_rectangle(xy, radius=14, fill="#eef3f7", outline="#9aabb9", width=2)
    font = ImageFont.truetype(FONT, size)
    lines = text.split("\n")
    y = (xy[1] + xy[3]) / 2 - len(lines) * (size + 7) / 2
    for line in lines:
        length = d.textlength(line, font=font)
        d.text(((xy[0] + xy[2] - length) / 2, y), line, font=font, fill=INK)
        y += size + 7


def arrow(d, a, b):
    d.line([a, b], fill="#677e92", width=3)
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    pts = [b] + [
        (b[0] - 14 * math.cos(angle + t), b[1] - 14 * math.sin(angle + t)) for t in (-0.4, 0.4)
    ]
    d.polygon(pts, fill="#677e92")


im, d = canvas(1600, 460, "LCEL académico · composición real")
nodes = [(30, 150, 350, 310), (430, 150, 800, 310), (880, 150, 1240, 310), (1310, 150, 1570, 310)]
for xy, text in zip(
    nodes,
    [
        "Validar entrada\nRunnableLambda",
        "Dos ramas\nRunnableParallel",
        "Stock sintético\ny escenario",
        "Salida\nPydantic",
    ],
    strict=False,
):
    box(d, xy, text, 32)
for a, b in zip(nodes, nodes[1:], strict=False):
    arrow(d, (a[2], 230), (b[0], 230))
d.text(
    (30, 375),
    "Fuente: src/academic/lcel.py · RunnableSequence mediante | · sin envío externo",
    font=ImageFont.truetype(FONT, 25),
    fill=INK,
)
im.save(F / "lcel.png")

graph = json.loads((E / "grafo-comercial.json").read_text())
node_ids = [node["id"] for node in graph["nodes"]]
incoming = Counter(edge["target"] for edge in graph["edges"])
outgoing = Counter(edge["source"] for edge in graph["edges"])
degrees = [(node, incoming[node], outgoing[node], incoming[node] + outgoing[node])
           for node in node_ids]
operational_nodes = sum(node not in {"__start__", "__end__"} for node in node_ids)
degree_sums = tuple(sum(row[i] for row in degrees) for i in (1, 2, 3))
degree_maxima = tuple(max(row[i] for row in degrees) for i in (1, 2, 3))
assert len(node_ids) == len(set(node_ids)) == 13 and operational_nodes == 11
assert len(graph["edges"]) == 20
assert set(incoming) | set(outgoing) == set(node_ids)
assert degree_sums == (20, 20, 40), "Las sumas de grados no coinciden con las aristas"
assert degree_maxima == (9, 9, 10), "Los grados máximos no coinciden con el grafo"
im, d = canvas(
    1800, 1160,
    f"StateGraph comercial compilado · {len(node_ids)} vértices "
    f"y {len(graph['edges'])} aristas",
)
branches = [
    "a2_armado",
    "a3_cotizacion",
    "a4_compatibilidad",
    "a5_inventario",
    "a6_pagos",
    "a7_pedidos",
    "a8_seguimiento",
    "recuperar",
]
coords = {
    "__start__": (30, 150, 330, 240),
    "validar_plan": (30, 490, 330, 590),
    "decidir": (1330, 490, 1630, 590),
    "responder": (1330, 800, 1630, 890),
    "__end__": (1330, 990, 1630, 1080),
}
for i, n in enumerate(branches):
    coords[n] = (660, 100 + i * 125, 1080, 190 + i * 125)
for edge in graph["edges"]:
    a, b = coords[edge["source"]], coords[edge["target"]]
    if edge["source"] == "validar_plan" and edge["target"] == "decidir":
        d.line([(330, 540), (480, 1110), (1210, 1110), (1330, 540)], fill="#677e92", width=3)
        arrow(d, (1210, 1110), (1330, 540))
    elif edge["source"] in ("__start__", "decidir", "responder"):
        arrow(d, ((a[0] + a[2]) / 2, a[3]), ((b[0] + b[2]) / 2, b[1]))
    else:
        arrow(d, (a[2], (a[1] + a[3]) / 2), (b[0], (b[1] + b[3]) / 2))
for n, xy in coords.items():
    box(d, xy, n)
im.save(F / "langgraph.png")

im, d = canvas(1500, 680, "HITL nativo académico · pausa y reanudación")
for xy, label in [
    ((40, 140, 420, 280), "invoke: fixture\nthread_id"),
    ((560, 140, 980, 280), "interrupt\nInMemorySaver"),
    ((560, 440, 980, 580), "Command(resume)\ndecisión tipada"),
    ((1110, 440, 1460, 580), "Estado final\nsin efecto comercial"),
]:
    box(d, xy, label)
arrow(d, (420, 210), (560, 210))
arrow(d, (770, 280), (770, 440))
arrow(d, (980, 510), (1110, 510))
d.text((1030, 155), "aprobar\nrechazar\ncorregir", font=ImageFont.truetype(FONT, 29), fill=INK)
im.save(F / "hitl.png")

ns = {"b": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
xml = ET.parse(ROOT / "docs/bpmn_to_be.bpmn").getroot()
elements = {x.get("id"): x for x in xml.iter() if x.get("id")}
ids = [
    "Task_A2_Armador_Presupuesto",
    "Task_A4_Compatibilidad_TDP",
    "Task_A5_Stock_Inventario",
    "Task_A3_Cotizacion_Formal",
]
im, d = canvas(1600, 650, "BPMN TO-BE · extracto del tramo de cotización")
for i, n in enumerate(ids):
    x = 30 + i * 400
    label = elements[n].get("name", n)
    lines = textwrap.wrap(label, 20)
    box(d, (x, 160, x + 340, 440), "\n".join(lines), 30)
    if i < 3:
        arrow(d, (x + 340, 300), (x + 400, 300))
d.text(
    (30, 500),
    "Síntesis visual de actividades y secuencia del XML original, sin modificar el BPMN.",
    font=ImageFont.truetype(FONT, 25),
    fill=INK,
)
d.text(
    (30, 545),
    "El StateGraph comercial selecciona una rama: esta secuencia no se ejecuta como tal.",
    font=ImageFont.truetype(FONT, 25),
    fill=INK,
)
im.save(F / "bpmn-extracto.png")

im, d = canvas(1600, 720, "Deep Agents · coordinación y delegación reales con MockLLM")
box(d, (420, 100, 1180, 230), "DA-CoordinadorAcademico\nwrite_todos + task", 30)
for xy, name in [
    ((70, 390, 700, 550), "DA-Catalogo · D3"),
    ((900, 390, 1530, 550), "DA-Revision · D4"),
]:
    box(d, xy, name + "\nrevisar_fixture_sintetico", 32)
    arrow(d, (800, 230), ((xy[0] + xy[2]) / 2, xy[1]))
d.text(
    (60, 615),
    ("Plan y respuestas programados; herramientas y delegación ejecutadas por el framework."),
    font=ImageFont.truetype(FONT, 26),
    fill=INK,
)
im.save(F / "deepagents.png")

im, d = canvas(1600, 840, "Ecosistema LangChain aplicado a Veltri")
for i, (title, subtitulo) in enumerate(
    [
        ("Deep Agents", "Coordinación y subagentes académicos"),
        ("LangChain", "LCEL, BaseChatModel y herramientas"),
        ("LangGraph", "Runtime, estado e interrupciones"),
    ]
):
    y = 120 + i * 220
    box(d, (40, y, 1000, y + 160), title + "\n" + subtitulo, 31)
    if i < 2:
        arrow(d, (520, y + 160), (520, y + 220))
box(
    d,
    (1090, 120, 1560, 720),
    "LangSmith\nObservabilidad\ntransversal\n\nOpt-in apagado\nTraza pendiente",
    31,
)
for y in (200, 420, 640):
    d.line([(1000, y), (1090, y)], fill="#677e92", width=3)
im.save(F / "ecosistema.png")

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21)
sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.8)
sec.left_margin = sec.right_margin = Cm(2)
normal = doc.styles["Normal"]
if not isinstance(normal, ParagraphStyle):
    raise TypeError("Normal debe ser un estilo de párrafo")
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(7)
normal.paragraph_format.line_spacing = 1.12
for name, size in [("Title", 30), ("Heading 1", 20), ("Heading 2", 14)]:
    estilo = doc.styles[name]
    if not isinstance(estilo, ParagraphStyle):
        raise TypeError("El encabezado debe ser un estilo de párrafo")
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(size)
    estilo.font.color.rgb = RGBColor.from_string(
        "000000" if name == "Title" else "183047"
    )
doc.core_properties.title = "Veltri Tecnologic Semana 10"
doc.core_properties.author = "Equipo del proyecto Veltri"
doc.core_properties.subject = "Cinco actividades del ecosistema LangChain"
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = footer.add_run("Veltri · Semana 10  |  ")
run.font.size = Pt(9)
fld = OxmlElement("w:fldSimple")
fld.set(qn("w:instr"), "PAGE")
footer._p.append(fld)
fig = 0
tab = 0


def p(text="", style=None):
    return doc.add_paragraph(text, style)


def h(text):
    doc.add_heading(text, 1)


def sub(text):
    doc.add_heading(text, 2)


def page(title):
    doc.add_page_break()
    h(title)


def code(path, start, end):
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    end = min(end, len(lines))
    p(f"Código · {path}, líneas {start}–{end}", "Caption")
    for i in range(start - 1, min(end, len(lines))):
        para = p()
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = 1
        para.paragraph_format.keep_with_next = i < min(end, len(lines)) - 1
        run = para.add_run(f"{i + 1:>3}  {lines[i]}")
        run.font.name = "Consolas"
        run.font.size = Pt(8)


def figure(name, title, source, width=6.6):
    global fig
    fig += 1
    para = p()
    para.paragraph_format.keep_with_next = True
    para.add_run().add_picture(str(F / name), width=Inches(width))
    cap = p(
        f"Figura {fig}. {title}. Fuente: {source}. "
        "Diagrama elaborado desde evidencia; no es captura de pantalla.",
        "Caption",
    )
    cap.paragraph_format.space_after = Pt(8)


def table(headers, rows, title):
    global tab
    tab += 1
    p(f"Tabla {tab}. {title}", "Caption")
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Shading Accent 1"
    for cell, text in zip(t.rows[0].cells, headers, strict=False):
        cell.text = text
    trpr = t.rows[0]._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:tblHeader"))
    for row in rows:
        cells = t.add_row().cells
        for c, text in zip(cells, row, strict=False):
            c.text = str(text)
            for para in c.paragraphs:
                para.paragraph_format.space_after = Pt(4)
                for run in para.runs:
                    run.font.size = Pt(9)
    for row in t.rows:
        pr = row._tr.get_or_add_trPr()
        pr.append(OxmlElement("w:cantSplit"))
    p("")


p("VELTRI TECNOLOGIC", "Subtitle")
p("Automatización inteligente\nde procesos", "Title")
p("Semana 10", "Subtitle")
p("Informe académico de las cinco actividades del ecosistema LangChain")
p("Ingeniería de Sistemas")
p("31 de octubre de 2026 · Lima, Perú")
p("\n")
sub("Estado de la entrega")
p(
    (
        "Las demostraciones locales de LCEL, HITL nativo y Deep Agents cuentan "
        "con resultados verificables. La suite registrada aprobó 464 pruebas. La "
        "ejecución remota de LangSmith permanece pendiente de acreditación "
        "visual; este informe no la presenta como completada."
    )
)
p(
    (
        "Las capturas auténticas de pantalla siguen pendientes de incorporación. "
        "Se incluyen diagramas derivados del código, extractos exactos y "
        "registros originales, identificados según su naturaleza."
    )
)
p(
    (
        "El flujo comercial principal y las demostraciones académicas se "
        "describen por separado. Los precios, existencias y casos utilizados son "
        "ejemplos sintéticos."
    )
)

page("2 Introducción")
p(
    (
        "Veltri Tecnologic aborda la atención de consultas de hardware mediante "
        "agentes por dominio, herramientas deterministas y un orquestador "
        "LangGraph. La propuesta combina interpretación estructurada, validación "
        "técnica, consulta de inventario y preparación de borradores, con "
        "revisión humana cuando la evidencia impide continuar."
    )
)
p(
    (
        "Este informe desarrolla exactamente las cinco actividades indicadas por "
        "el profesor: identificación de LCEL; grafo e HITL frente al BPMN TO-BE; "
        "monitoreo LangSmith; Deep Agents; y cuatro componentes del ecosistema. "
        "El análisis se apoya en el código y las ejecuciones conservadas el 31 de"
        " octubre de 2026."
    )
)
sub("3 Objetivos")
for text in [
    "Identificar componentes LCEL con archivo, línea y aplicación comprobable.",
    ("Explicar el grafo real, demostrar HITL y comparar su comportamiento con el proceso BPMN."),
    (
        "Delimitar el estado de la traza LangSmith sin confundir aceptación HTTP "
        "con verificación remota."
    ),
    "Demostrar Deep Agents reales con planificación y delegación bajo MockLLM.",
    (
        "Relacionar Deep Agents, LangChain y LangGraph con LangSmith como "
        "observabilidad transversal."
    ),
]:
    p(text, "List Bullet")
sub("Criterio de evidencia")
p(
    (
        "Se distinguen cuatro categorías: código implementado, ejecución local "
        "registrada, diagrama derivado y captura de pantalla. Una categoría no "
        "sustituye a otra. Los registros HTTP 202 no prueban por sí solos que el "
        "árbol remoto esté completo."
    )
)

page("4 Descripción de Veltri")
p(
    (
        "La aplicación comercial utiliza FastAPI, una interfaz web local, agentes"
        " personalizados A1–A8, herramientas en src/tools y recuperación "
        "documental con tenant explícito. Las cantidades, precios, compatibilidad"
        " y stock se calculan mediante código, no mediante el modelo de lenguaje."
    )
)
table(
    ["Agentes", "Dominio y responsabilidad", "Alcance real"],
    [
        (
            "A1–A3",
            "D1: interpretar, armar y cotizar",
            "Interpretación estructurada y herramientas locales",
        ),
        ("A4", "D2: compatibilidad", "Validación técnica determinista"),
        ("A5", "D3: inventario", "Lectura de stock sintético"),
        (
            "A6–A8",
            "D4: pagos, borradores y seguimiento",
            "Comparación local; sin proveedor de pagos",
        ),
    ],
    "Agentes del flujo comercial",
)
sub("Separación de las demostraciones")
p(
    (
        "src/academic contiene LCEL, HITL nativo y Deep Agents académicos. Estos "
        "módulos no están expuestos por la API ni reemplazan los agentes "
        "comerciales. El script demo_academica.py desactiva las trazas de su "
        "proceso y registra resultados sintéticos locales."
    )
)
table(
    ["Componente", "Flujo comercial", "Demo académica"],
    [
        ("Agentes", "Clases BaseAgent A1–A8", "create_deep_agent y dos especialistas"),
        ("HITL", "Bandeja local sin pausa nativa", "interrupt + InMemorySaver + Command"),
        ("Modelo", "Fábrica get_llm", "MockLLM programado con adaptador"),
        ("Efectos", "Comparaciones y borradores locales", "Ninguna autorización comercial"),
    ],
    "Límites entre aplicación y demostración",
)
p(
    (
        "El inventario conserva 84 SKUs de ejemplo en soles. CPU-AMD-5500 tiene "
        "stock cero y se usa para evidenciar un bloqueo de inventario. Ningún "
        "dato se presenta como precio o disponibilidad real de una tienda."
    )
)

page("5 Actividad 1 LCEL")
p(
    (
        "LCEL permite componer objetos Runnable. En Veltri se implementó una "
        "cadena determinista que valida una entrada cerrada, ejecuta ramas "
        "paralelas y proyecta una salida tipada. La composición con | construye "
        "un RunnableSequence real, comprobado en tests/test_academico.py."
    )
)
code("src/academic/lcel.py", 3, 21)
table(
    ["Término", "Aplicación y ubicación"],
    [
        (
            "RunnableLambda",
            "Envuelve validación, selección de escenario, stock y salida; lcel.py:13–19.",
        ),
        ("RunnableParallel", "Produce un diccionario con escenario y revisión; lcel.py:14–18."),
        ("RunnableSequence y |", "Encadena las etapas; lcel.py:12–20; test_academico.py:15–18."),
        ("invoke", "Ejecuta la cadena con una entrada; scripts/demo_academica.py."),
        ("Pydantic", "Valida contratos; no se identifica como parser LCEL independiente."),
        ("ChatPromptTemplate", "No utilizado: la operación determinista no necesita un prompt."),
    ],
    "Identificación de términos LCEL",
)

page("Actividad 1 Ejecución y evidencia")
figure("lcel.png", "Pipeline académico de revisión de stock", "src/academic/lcel.py")
p(
    (
        "La rama de revisión llama a comprobar_stock en src/tools/inventario.py "
        "sobre el catálogo local. El cálculo queda en la herramienta "
        "determinista. La otra rama conserva el escenario. La etapa final "
        "construye SalidaAcademica; no redacta una cotización ni modifica el "
        "inventario."
    )
)
sub("Entrada y salida registradas")
p(("Entrada: {}. Se aplica el escenario predeterminado revision_sintetica, sin mensajes libres."))
p(json.dumps(ej["lcel"], ensure_ascii=False, indent=2))
p(
    (
        "Fuente: ejecuciones.json, campo lcel. La salida confirma revisión "
        "requerida y ausencia de efecto comercial. Las pruebas rechazan campos "
        "adicionales y escenarios distintos; también comprueban el tipo "
        "RunnableSequence y el contrato resultante."
    )
)
sub("Límite de la evidencia")
p(
    (
        "El pipeline tiene dos ramas paralelas reales, aunque la proyección final"
        " utiliza solo el resultado de revisión. No demuestra una composición "
        "prompt | model | parser ni una llamada de inferencia. Falta la captura "
        "auténtica del código y de su salida en un editor o terminal del usuario."
    )
)

page("6 Actividad 2 LangGraph")
p(
    (
        f"El grafo compilado comercial contiene {operational_nodes} nodos operativos, "
        f"{len(node_ids)} vértices al contar START y END, y {len(graph['edges'])} aristas. "
        "La seguridad y A1 se ejecutan antes"
        " del grafo. validar_plan selecciona una sola ruta tipada; las ramas "
        "convergen en decidir, responder y END."
    )
)
figure(
    "langgraph.png",
    "Grafo comercial con 11 nodos operativos, 13 vértices y 20 aristas",
    "grafo-comercial.json; src/graph/workflow.py:28–53",
)
p(
    (
        "La rama recuperar representa la consulta documental con tenant. El "
        "selector también puede pasar directamente a decidir. Las aristas "
        "condicionales provienen del grafo compilado; la presencia de una ruta no"
        " implica que cada consulta la recorra."
    )
)
p(
    (
        "El diagrama se generó a partir de los nodos y aristas almacenados por "
        "get_graph(). No se modificó el StateGraph para acercarlo artificialmente"
        " al BPMN."
    )
)

page("Actividad 2 Grados de los nodos")
p(
    "En este grafo dirigido, el grado de entrada cuenta las aristas que llegan a "
    "cada vértice; el de salida cuenta las que parten de él. El grado total es "
    "la suma de ambos. Se incluyen START, END y todas las alternativas condicionales "
    "del JSON compilado, no solo las aristas recorridas por una consulta."
)
table(
    ["Nodo", "Grado de entrada", "Grado de salida", "Grado total"],
    degrees,
    "Grados individuales del grafo comercial dirigido",
)
sub("Comprobación de sumas y máximos")
p(
    f"La suma de entradas es {degree_sums[0]} y la suma de salidas es {degree_sums[1]}; "
    f"ambas coinciden con las {len(graph['edges'])} aristas. La suma de grados totales "
    f"es {degree_sums[2]}, el doble del número de aristas."
)
p(
    f"El máximo de entrada es {degree_maxima[0]} (decidir); el máximo de salida es "
    f"{degree_maxima[1]} (validar_plan). El máximo de grado total es {degree_maxima[2]}, "
    "compartido por validar_plan y decidir. Estos valores describen la estructura, "
    "no el número de agentes ejecutados simultáneamente."
)
p(
    "Fuente: docs/evidencias/semana10-entrega-final/grafo-comercial.json, listas "
    "nodes y edges; contraste con src/graph/workflow.py:28–53. El generador calcula "
    "los grados desde ese JSON y comprueba sus sumas y máximos antes de guardar el informe."
)

page("Actividad 2 HITL nativo y bandeja")
code("src/academic/hitl.py", 25, 36)
figure(
    "hitl.png",
    "Interrupción y reanudación de la demo aislada",
    "src/academic/hitl.py y ejecuciones.json",
    6.3,
)
table(
    ["Decisión simulada", "Checkpoint pendiente", "Resultado"],
    [
        (x["decision_simulada"], ", ".join(x["checkpoint_next"]), x["salida"]["resultado"])
        for x in ej["hitl"]
    ],
    "Tres caminos ejecutados de HITL nativo",
)
p(
    (
        "Command(resume=...) reanuda el mismo thread_id. Las pruebas comprueban "
        "la interrupción, el nodo pendiente y la finalización, y rechazan una "
        "acción inválida. InMemorySaver conserva el estado solo dentro del "
        "proceso; no hay persistencia duradera ni revisor autenticado."
    )
)
p(
    "La bandeja comercial permanece separada. La ejecución guardada cambió de "
    + ej["bandeja_existente"]["antes"]
    + " a "
    + ej["bandeja_existente"]["despues"]
    + ". Resolver esa bandeja no reanuda el StateGraph comercial ni ejecuta una venta."
)

page("Actividad 2 Comparación con BPMN TO BE")
figure(
    "bpmn-extracto.png",
    "Secuencia de cotización representada por el BPMN original",
    "docs/bpmn_to_be.bpmn",
    6.5,
)
table(
    ["Aspecto", "BPMN TO-BE", "Implementación y compatibilidad"],
    [
        ("Cotización", "A2 → A4 → A5 → A3", "Parcial: el grafo selecciona una rama por solicitud."),
        ("Enrutamiento", "Gateway inclusivo", "Diferencia: selector tipado de una rama."),
        ("Seguridad/A1", "Actividades del proceso", "Previas al StateGraph en el código."),
        ("Revisión", "Intervención humana", "Bandeja local; HITL nativo solo académico."),
        (
            "Pagos/pedidos",
            "Conciliación y registro",
            "Comparación y borradores; sin proveedor externo.",
        ),
        ("Seguimiento", "A8 no representado", "A8 sí existe en el sistema."),
        (
            "IGV y tiempos",
            "IGV 18 % y objetivo <1,5 s",
            "No usar el BPMN como prueba del cálculo ni del rendimiento.",
        ),
    ],
    "Compatibilidades y discrepancias verificadas",
)
p(
    (
        "La compatibilidad es parcial. Las políticas de garantía, el cálculo de "
        "IGV y las diferencias de tiempos siguen fuera del alcance de esta fase. "
        "El XML original se conserva íntegro; la figura es un extracto "
        "explicativo, no una captura de un modelador BPMN."
    )
)

page("7 Actividad 3 Monitoreo con LangSmith")
p(
    (
        "Estado: evidencia remota pendiente de acreditación. El segundo intento "
        "autorizado registró nueve creaciones y nueve cierres aceptados por HTTP "
        "202. La lectura posterior recibió HTTP 403 y se detuvo sin reintentos. "
        "No se verificó un run_id ni el árbol remoto."
    )
)
table(
    ["Etapa", "Resultado observado", "Qué acredita"],
    [
        ("POST /runs", "9 respuestas 202", "Aceptación de solicitudes de creación"),
        ("PATCH /runs/{run_id}", "9 respuestas 202", "Aceptación de cierres"),
        ("GET /runs/{run_id}", "403; categoría permisos", "Verificación remota bloqueada"),
        (
            "run_id / duración / árbol",
            "No verificados",
            "No disponibles para acreditar la actividad",
        ),
    ],
    "Resultado real del intento remoto",
)
p(
    (
        "Fuente: docs/evidencias/semana10-fase43/ejecucion-unica.json. Ventana "
        "del procedimiento: 09:39:46–09:40:03, America/Lima, 31/10/2026. Ese "
        "intervalo no es la duración remota de la traza. El identificador de "
        "correlación HTTP no es el run_id."
    )
)
sub("Instrumentación y privacidad")
code("src/core/observabilidad.py", 43, 55)
p(
    (
        "La sesión exige doble opt-in y modo mock. Inputs y outputs se mantienen "
        "vacíos y los metadatos se restringen a constantes sintéticas. Los dos "
        "controles quedaron apagados. No se realizaron nuevos envíos para "
        "elaborar este informe."
    )
)
sub("Evidencia que debe incorporarse")
p(
    (
        "Desde el panel autenticado: proyecto veltri-semana10-demo, ejecución "
        "seleccionada, run_id, duración, árbol de nueve spans, metadata y "
        "entradas/salidas vacías. Las capturas no están disponibles. Una clave "
        "Tracing Only puede explicar falta de lectura, pero la causa del 403 no "
        "está confirmada."
    )
)

page("8 Actividad 4 Deep Agents generados")
p(
    (
        "El módulo académico importa y utiliza create_deep_agent del paquete "
        "deepagents 0.4.11. El coordinador y sus dos especialistas son distintos "
        "de A1–A8. El adaptador BaseChatModel obtiene MockLLM desde get_llm y "
        "traduce fixtures tipados a llamadas de herramientas."
    )
)
figure(
    "deepagents.png",
    "Coordinador y especialistas del framework",
    "src/academic/deep_agents.py",
    6.5,
)
table(
    ["Nombre", "Responsabilidad", "Herramientas"],
    [
        ("DA-CoordinadorAcademico", "Organizar la revisión sintética", "write_todos y task"),
        ("DA-Catalogo", "D3: revisar evidencia sintética", "revisar_fixture_sintetico"),
        ("DA-Revision", "D4: explicar revisión requerida", "revisar_fixture_sintetico"),
    ],
    "Deep Agents implementados",
)
p(
    (
        "Los nombres y responsabilidades fueron aprobados por el usuario. No "
        "aprueban ventas ni pagos. La herramienta lee el fixture de inventario y "
        "devuelve únicamente atributos sintéticos reducidos; no reserva ni "
        "modifica stock."
    )
)

code("src/academic/deep_agents.py", 86, 89)
page("Actividad 4 Planificación y delegación verificadas")
code("src/academic/deep_agents.py", 62, 83)
sub("Secuencia registrada")
p(
    (
        "El coordinador emitió write_todos con dos tareas, delegó mediante task "
        "en DA-Catalogo y DA-Revision, marcó ambas tareas como completed y "
        "devolvió la salida académica. Cada especialista ejecutó la herramienta y"
        " recibió una respuesta con estado success."
    )
)
table(
    ["Evidencia", "Resultado real"],
    [
        ("Llamadas task", "DA-Catalogo y DA-Revision"),
        ("Plan final", "Dos tareas completed"),
        ("Auditoría de especialistas", "revisar_fixture_sintetico: success en ambos"),
        ("Salida final", "sintetico=true; requiere_revision=true; efecto_comercial=false"),
    ],
    "Plan, delegación y herramientas en ejecuciones.json",
)
p(
    (
        "La delegación la ejecuta el framework; el modelo y el plan son "
        "programados. Se verifica integración funcional sin pagar inferencia. No "
        "se demuestra planificación autónoma, memoria persistente ni utilización "
        "del filesystem virtual. Los mensajes y todos son contexto de esta "
        "ejecución."
    )
)
p(
    (
        "Las pruebas verifican las delegaciones, los cuatro ToolMessage del "
        "coordinador, la ausencia de errores, el plan completado y la auditoría "
        "exitosa de cada especialista. La captura de pantalla del código y de la "
        "ejecución permanece pendiente."
    )
)

page("9 Actividad 5 Cuatro componentes del ecosistema")
figure(
    "ecosistema.png",
    "Tres capas de agentes y observabilidad transversal",
    "src/academic y src/core/observabilidad.py",
    6.5,
)
table(
    ["Componente", "Función y aplicación real"],
    [
        (
            "Deep Agents",
            "Coordinación de alto nivel con planificación y especialistas; deep_agents.py.",
        ),
        (
            "LangChain",
            "Primitivas de modelos y herramientas; BaseChatModel y cadena LCEL; lcel.py.",
        ),
        ("LangGraph", "Runtime del grafo comercial y del agente; interrupciones en hitl.py."),
        (
            "LangSmith",
            (
                "Observabilidad transversal mediante instrumentación opt-in; verificación"
                " remota pendiente."
            ),
        ),
    ],
    "Relación del ecosistema con Veltri",
)
p(
    (
        "Deep Agents se apoya en LangChain y LangGraph. LCEL organiza una "
        "operación determinista; LangGraph coordina estado y ejecución. LangSmith"
        " puede observar los componentes, pero no es una cuarta capa de ejecución"
        " en serie. Build, Test, Deploy y Monitor no sustituyen esta "
        "clasificación."
    )
)

code("src/academic/deep_agents.py", 6, 9)
page("10 Resultados y pruebas")
p(
    (
        "Se utiliza la verificación conservada, sin repetir fases ni ejecutar "
        "otra demostración remota. El registro corresponde a python "
        "scripts/verificar.py bajo aislamiento de red externa y sin credenciales "
        "reales en las pruebas."
    )
)
table(
    ["Comprobación", "Resultado registrado"],
    [
        ("Pytest", "464 aprobadas; 0 fallos, 0 errores, 0 omitidas"),
        ("Ruff", "All checks passed!"),
        ("Secretos", "Sin hallazgos"),
        ("Tiempo pytest", "48,51 segundos"),
        ("Advertencias", "2 deprecaciones: ChromaDB y Google SDK"),
        ("Regresión", "456 pruebas previas más 8 casos académicos"),
        ("Suite completa", "Código de salida 0; 58,552 segundos con verificaciones"),
    ],
    "Resultados de verificar.log y suite-summary.json",
)
sub("Salida textual original")
for line in [
    "[ruff] All checks passed!",
    "464 passed, 2 warnings in 48.51s",
    "[secretos] Escaneo de secretos: sin hallazgos.",
    "ruff OK | pytest OK | secretos OK",
]:
    pp = p(line)
    pp.runs[0].font.name = "Consolas"
    pp.runs[0].font.size = Pt(10)
p(
    (
        "Los ocho casos nuevos comprenden una composición LCEL, dos entradas "
        "inválidas parametrizadas, tres decisiones HITL, una decisión no admitida"
        " y una ejecución de Deep Agents. La línea base protegida no se "
        "actualizó."
    )
)
sub("Versiones ejecutadas")
p("; ".join(f"{k} {v}" for k, v in ej["versiones"].items()) + ".")
p(
    (
        "Los resultados son evidencia de las pruebas ejecutadas en esa fecha, no "
        "una garantía de exactitud comercial completa. La discrepancia BPMN y la "
        "acreditación LangSmith pendiente siguen explícitas."
    )
)

page("11 Conclusiones")
p(
    (
        "La implementación demuestra una cadena LCEL auténtica y una operación "
        "determinista de revisión de inventario. El contrato tipado impide "
        "introducir mensajes arbitrarios en la demo y mantiene el cálculo en "
        "herramientas de código."
    )
)
p(
    (
        "LangGraph dispone de 11 nodos operativos, 13 vértices incluyendo START y END, "
        "y 20 aristas. Los grados suman 20 entradas y 20 salidas; sus máximos son "
        "9 de entrada, 9 de salida y 10 de grado total. Existe además una demostración "
        "académica de pausa y reanudación. La bandeja comercial y el mecanismo "
        "nativo son distintos. El BPMN TO-BE conserva diferencias relevantes de "
        "secuencia, compuertas y alcance operativo."
    )
)
p(
    (
        "Los Deep Agents se ejecutan mediante el framework real con planificación"
        " y delegación programadas por MockLLM. Esta evidencia valida la "
        "integración y las herramientas, sin acreditar autonomía del modelo ni "
        "memoria persistente."
    )
)
p(
    (
        "Las cuatro partes del ecosistema tienen una correspondencia concreta con"
        " el proyecto. LangSmith permanece como observabilidad transversal con "
        "instrumentación segura; la actividad de monitoreo no puede declararse "
        "acreditada hasta verificar la traza remota existente."
    )
)
table(
    ["Requisito", "Conclusión de cumplimiento"],
    [
        ("1 LCEL", "Implementado y ejecutado; capturas pendientes"),
        (
            "2 LangGraph/HITL/BPMN",
            "Recuento y grados verificados; HITL local; "
            "compatibilidad parcial; capturas pendientes",
        ),
        ("3 LangSmith", "Pendiente de acreditación remota"),
        ("4 Deep Agents", "Framework ejecutado con MockLLM; capturas pendientes"),
        ("5 Cuatro componentes", "Documentados y relacionados con archivos reales"),
    ],
    "Matriz final sin exceder la evidencia",
)
p(
    (
        "La incorporación de capturas auténticas y la comprobación de la traza "
        "son las acciones restantes para una entrega íntegramente acreditada. No "
        "se requiere otra demostración externa para elaborar este documento."
    )
)

page("12 Referencias")
refs = [
    (
        "LangChain",
        "RunnableSequence y composición LCEL",
        "https://reference.langchain.com/python/langchain_core/runnables/",
    ),
    (
        "LangChain",
        "Interrupciones de LangGraph",
        "https://docs.langchain.com/oss/python/langgraph/interrupts",
    ),
    (
        "LangChain",
        "Deep Agents y su arquitectura",
        "https://docs.langchain.com/oss/python/deepagents/overview",
    ),
    (
        "LangChain",
        "Subagentes de Deep Agents",
        "https://docs.langchain.com/oss/python/deepagents/subagents",
    ),
    ("LangChain", "Observabilidad LangSmith", "https://docs.langchain.com/langsmith/observability"),
    ("Object Management Group", "BPMN 2.0.2", "https://www.omg.org/spec/BPMN/2.0.2/"),
]
for author, title, url in refs:
    p(
        f"{author}. (s. f.). {title}. Documentación técnica oficial. "
        "Consulta: 31 de octubre de 2026."
    )
    p(url)
sub("Fuentes primarias del proyecto")
p(
    (
        "Veltri Tecnologic. (2026). Código fuente local, BPMN TO-BE y expediente "
        "técnico de Semana 10. Repositorio: D:/Proyectos/veltri-orquestador."
    )
)
p(
    (
        "Se utilizaron ejecuciones.json, verificar.log, pytest-suite.xml, "
        "suite-summary.json, grafo-comercial.json y el registro remoto de fase "
        "4.3. Los identificadores de archivos y líneas se relacionan en el anexo "
        "siguiente."
    )
)
p(
    (
        "Las referencias describen las tecnologías; las afirmaciones sobre "
        "resultados de Veltri se sustentan en sus registros locales. Las "
        "capacidades generales del framework no se atribuyen automáticamente a "
        "esta implementación."
    )
)

page("13 Anexos técnicos y evidencia pendiente")
table(
    ["Archivo", "Contenido utilizado"],
    [
        ("src/academic/lcel.py:10–20", "Composición LCEL"),
        ("src/academic/hitl.py:23–33", "interrupt y checkpointer"),
        ("src/academic/deep_agents.py:17–101", "Adaptador, subagentes y creación"),
        ("scripts/demo_academica.py", "Ejecución local y exportación"),
        ("src/graph/workflow.py:28–53", "Grafo comercial"),
        ("src/core/hitl.py:27,62", "Registro y resolución de bandeja"),
        ("docs/bpmn_to_be.bpmn", "Proceso TO-BE original conservado"),
        ("tests/test_academico.py", "Ocho casos académicos"),
        ("docs/evidencias/semana10-entrega-final/", "Resultados y procedencia"),
        (
            "docs/evidencias/semana10-fase43/ejecucion-unica.json",
            "HTTP 202/403; sin traza verificada",
        ),
    ],
    "Localización de evidencias",
)
sub("Capturas pendientes de incorporación")
p(
    (
        "C01: código y salida LCEL; C02: grafo real; C03: BPMN en modelador; "
        "C04–C05: pausa, decisión y reanudación; C06: aplicación local; C07: "
        "A1–A8 y Deep Agents; C08: pruebas; C09: traza LangSmith; C10–C13: "
        "componentes del ecosistema. Los originales no se sustituyen por los "
        "diagramas del informe."
    )
)
p(
    (
        "No se aportaron capturas manuales ni se eludieron las restricciones de "
        "Computer Use. Para completar C09 se necesita una captura auténtica del "
        "proyecto y del detalle remoto con run_id, duración, spans y metadatos, "
        "sin mostrar credenciales."
    )
)
p(
    (
        "Las figuras PNG del informe son diagramas documentales generados desde "
        "fuentes locales, no capturas de pantallas ni ejecuciones simuladas. Los "
        "registros originales permanecen en su carpeta de evidencia y no fueron "
        "alterados."
    )
)

target = OUT / "Veltri_Semana10_Informe_Academico.docx"
for root in (doc.styles.element, doc.element):
    for border in root.findall(".//" + qn("w:pBdr")):
        border.getparent().remove(border)
doc.save(str(target))
manifest = {
    "fecha": "2026-10-31",
    "documento": target.name,
    "langsmith_acreditado": False,
    "capturas_autenticas_incorporadas": 0,
    "figuras_derivadas": 6,
    "fuentes": {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            E / "ejecuciones.json",
            E / "verificar.log",
            E / "grafo-comercial.json",
            ROOT / "docs/bpmn_to_be.bpmn",
            ROOT / "docs/evidencias/semana10-fase43/ejecucion-unica.json",
        ]
    },
}
(OUT / "procedencia.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(target)
