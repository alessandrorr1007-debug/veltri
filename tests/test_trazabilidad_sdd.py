"""Comprueba la especificación versionada y las garantías pendientes de una prueba directa."""

import ast
import os
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

import pytest
from langgraph.graph import END, START

from src.config import Configuracion
from src.core import observabilidad
from src.graph.workflow import Orquestador

RAIZ = Path(__file__).resolve().parents[1]
REQUISITOS = frozenset("""
    A1 A2 A3 A4 A5 A6 A7 A8 DA-COORD DA-CAT DA-REV DA-MEM DA-CTRL DA-LEG
    GRAFO PROMPTS AUT-LIM AUT-TOK AUT-TIME AUT-HITL RAG SEC-INPUT SEC-DATOS
    HITL API CAT REC LOCAL SDD
""".split())
ENCABEZADO = (
    "| ID | Requisito | Especificación de aceptación | Componente | Código | Pruebas | Resultado |"
)


def _filas(documento):
    seccion = documento.split("## Especificaciones y trazabilidad SDD\n", 1)
    assert len(seccion) == 2, "Falta la sección SDD"
    _, _, tabla = seccion[1].partition(ENCABEZADO + "\n|---|---|---|---|---|---|---|\n")
    assert tabla, "Falta la tabla de trazabilidad o cambió su formato"
    lineas, _, _ = tabla.partition("\n\n")
    for linea in lineas.splitlines():
        assert linea.startswith("| ") and linea.endswith(" |"), linea
        celdas = [celda.strip() for celda in linea.strip("|").split("|")]
        assert len(celdas) == 7 and all(celdas), f"Fila incompleta: {linea}"
        yield celdas


def _referencias(celda, prefijo):
    for referencia in celda.split(", "):
        match = re.fullmatch(r"`([a-zA-Z0-9_/]+\.py)::(\w+(?:\.\w+)*)`", referencia)
        assert match, f"Referencia inválida: {referencia}"
        archivo, simbolo = match.groups()
        assert archivo.startswith(prefijo), f"Referencia fuera del ámbito: {referencia}"
        yield archivo, simbolo


def _existe_simbolo(archivo, simbolo):
    ruta = RAIZ / archivo
    assert ruta.is_file(), f"Código inexistente: {archivo}"
    nodo = ast.parse(ruta.read_text(encoding="utf-8"), filename=archivo)
    for nombre in simbolo.split("."):
        definiciones = [
            hijo for hijo in nodo.body
            if isinstance(hijo, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and hijo.name == nombre
        ]
        assert definiciones, f"Símbolo inexistente: {archivo}::{simbolo}"
        nodo = definiciones[-1]


def _recolectar():
    entorno = {**os.environ, "USE_MOCK_LLM": "1", "PYTEST_ADDOPTS": "", "PYTHONUTF8": "1"}
    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        cwd=RAIZ, env=entorno, capture_output=True, encoding="utf-8", timeout=60,
    )
    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    casos = set()
    for linea in proceso.stdout.splitlines():
        if linea.startswith(("tests/", "tests\\")) and "::" in linea:
            archivo, caso = linea.split("::", 1)
            casos.add((archivo.replace("\\", "/"), caso.split("[", 1)[0]))
    assert casos, "Pytest no informó casos recolectados"
    return casos


def _validar_matriz(documento, recolectados, requeridos=REQUISITOS):
    vistos = set()
    modulos = set()
    for requisito, _, _, _, codigo, pruebas, resultado in _filas(documento):
        assert requisito not in vistos, f"Requisito duplicado: {requisito}"
        vistos.add(requisito)
        assert resultado == "pytest", f"{requisito}: resultado sin verificación automática"
        for archivo, simbolo in _referencias(codigo, ("src/", "scripts/")):
            _existe_simbolo(archivo, simbolo)
        for archivo, caso in _referencias(pruebas, "tests/"):
            assert (archivo, caso) in recolectados, f"{requisito}: {archivo}::{caso} sin recolectar"
            modulos.add(archivo)
    assert requeridos <= vistos, f"Faltan requisitos obligatorios: {sorted(requeridos - vistos)}"
    huerfanos = {archivo for archivo, _ in recolectados} - modulos
    assert not huerfanos, f"Suites sin propósito en la matriz: {sorted(huerfanos)}"


def test_matriz_cubre_requisitos_componentes_y_pruebas():
    _validar_matriz(
        (RAIZ / "docs/arquitectura.md").read_text(encoding="utf-8"),
        _recolectar(),
    )


@pytest.mark.parametrize(("cambio", "mensaje"), [
    ("A1", "Faltan requisitos obligatorios"),
    ("caso", "sin recolectar"),
    ("simbolo", "Símbolo inexistente"),
    ("suite", "Suites sin propósito"),
])
def test_matriz_detecta_perdidas_de_trazabilidad(cambio, mensaje):
    id_ = "A2" if cambio == "A1" else "A1"
    prueba = "test_ausente" if cambio == "caso" else "test_existente"
    simbolo = "ausente" if cambio == "simbolo" else "crear_grafo"
    texto = (
        f"## Especificaciones y trazabilidad SDD\n{ENCABEZADO}\n|---|---|---|---|---|---|---|\n"
        f"| {id_} | Requisito | Criterio | Componente | `src/graph/workflow.py::{simbolo}` "
        f"| `tests/test_a.py::{prueba}` | pytest |\n"
    )
    recolectados = {("tests/test_a.py", "test_existente")}
    if cambio == "suite":
        recolectados.add(("tests/test_b.py", "test_aislado"))
    with pytest.raises(AssertionError, match=mensaje):
        _validar_matriz(texto, recolectados, {"A1"})


def test_grafo_comercial_conserva_la_topologia_especificada():
    orquestador = Orquestador(guiones={}, configuracion=Configuracion(usar_mock=True))
    grafo = orquestador._grafo.get_graph()
    dominios = {
        "a2_armado", "a3_cotizacion", "a4_compatibilidad", "a5_inventario",
        "a6_pagos", "a7_pedidos", "a8_seguimiento", "recuperar",
    }
    aristas = {
        (START, "validar_plan"), ("validar_plan", "decidir"),
        ("decidir", "responder"), ("responder", END),
        *(("validar_plan", nodo) for nodo in dominios),
        *((nodo, "decidir") for nodo in dominios),
    }
    assert {(e.source, e.target) for e in grafo.edges} == aristas
    assert set(grafo.nodes) == {nodo for arista in aristas for nodo in arista}


def test_ventana_de_recursos_acotada_y_aislada(monkeypatch):
    ventana = deque(maxlen=observabilidad._recursos_recientes.maxlen)
    monkeypatch.setattr(observabilidad, "_recursos_recientes", ventana)
    evento = {"pasos": {"total": 0}}
    for numero in range(257):
        evento["pasos"]["total"] = numero
        observabilidad.registrar_recursos("sdd", evento)
    conservados = observabilidad.recursos_recientes()
    assert len(conservados) == 256
    assert conservados[0] == ("sdd", {"pasos": {"total": 1}})
    assert conservados[-1] == ("sdd", {"pasos": {"total": 256}})
    conservados[-1][1]["pasos"]["total"] = -1
    assert observabilidad.recursos_recientes()[-1][1]["pasos"]["total"] == 256
