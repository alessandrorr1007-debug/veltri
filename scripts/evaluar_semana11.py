"""Ejecuta las evaluaciones deterministas de semana 11 y publica resultados JSON."""

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
MATRIZ = RAIZ / "evals/semana11.json"
TOLERANCIA_PP = 2
DISTRIBUCION = {"representativo": 24, "limite": 10, "adversario": 6}
CAMPOS = {
    "id", "categoria", "requisitos", "pruebas", "entrada", "esperado", "aceptacion", "instancias",
}


def cargar_casos() -> list[dict]:
    casos = json.loads(MATRIZ.read_text(encoding="utf-8"))
    distribucion = Counter(c["categoria"] for c in casos)
    if len({c["id"] for c in casos}) != 40 or distribucion != DISTRIBUCION:
        raise ValueError("La matriz debe contener 40 casos únicos, distribuidos en 24/10/6")
    pruebas = set()
    for caso in casos:
        if (
            caso.keys() != CAMPOS or any(not caso[campo] for campo in CAMPOS)
            or any(not re.fullmatch(r"[A-Z][A-Z0-9-]*", r) for r in caso["requisitos"])
        ):
            raise ValueError(f"Campos de evaluación inválidos: {caso['id']}")
        for nodo in caso["pruebas"]:
            valido = re.fullmatch(r"tests/test_\w+\.py::test_\w+(?:\[.+\])?", nodo)
            if nodo in pruebas or not valido:
                raise ValueError(f"Prueba repetida o inválida: {nodo}")
            pruebas.add(nodo)
    return casos


def _resultado(caso: dict, indice: dict[str, str]) -> tuple[str, str | None]:
    estados = []
    for prueba in caso["pruebas"]:
        resultados = [estado for nodo, estado in indice.items() if
                      nodo == prueba or nodo.startswith(prueba + "[")]
        estados.extend(resultados or ["ausente"])
    if len(estados) != caso["instancias"] or "error" in estados or "ausente" in estados:
        return "fallido", "infraestructura"
    if "failure" in estados:
        seguridad = caso["categoria"] == "adversario" or any(
            r.startswith(("SEC-", "AUT-")) or r in {"RAG", "DA-CTRL", "HITL"}
            for r in caso["requisitos"]
        )
        return "fallido", "seguridad_o_invariante" if seguridad else "funcional"
    if "skipped" in estados:
        return "omitido", "evidencia_incompleta"
    return "aprobado", None


def leer_resultados(casos: list[dict], informe: Path) -> list[dict]:
    indice = {}
    if informe.is_file():
        for elemento in ET.parse(informe).iter("testcase"):
            modulo = elemento.attrib["classname"].replace(".", "/")
            nodo = f"{modulo}.py::{elemento.attrib['name']}"
            indice[nodo] = next(
                (estado for estado in ("error", "failure", "skipped")
                 if elemento.find(estado) is not None), "passed",
            )
    resultados = []
    for caso in casos:
        estado, fallo = _resultado(caso, indice)
        resultados.append({**caso, "resultado": estado, "clasificacion_fallo": fallo})
    return resultados


def evaluar(raiz: Path) -> dict:
    casos = cargar_casos()
    entorno = {
        **os.environ, "USE_MOCK_LLM": "1", "VELTRI_TRACING_ENABLED": "0",
        "VELTRI_TRACING_ALLOW_EXTERNAL": "0", "LANGSMITH_TRACING": "false",
        "LANGCHAIN_TRACING_V2": "false", "PYTHONUTF8": "1", "PYTEST_ADDOPTS": "",
    }
    nodos = [nodo for caso in casos for nodo in caso["pruebas"]]
    with TemporaryDirectory() as carpeta:
        informe = Path(carpeta) / "casos.xml"
        proceso = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-o", "xfail_strict=true",
             "--junitxml", str(informe), *nodos],
            cwd=raiz, env=entorno, capture_output=True, encoding="utf-8", timeout=180,
        )
        resultados = leer_resultados(casos, informe)
    conteos = Counter(c["resultado"] for c in resultados)
    if proceso.returncode:
        print(proceso.stdout, proceso.stderr, file=sys.stderr)
    return {
        "pytest_codigo": proceso.returncode,
        "conteos": {estado: conteos[estado] for estado in ("aprobado", "fallido", "omitido")},
        "casos": resultados,
    }


def comparar_resultados(referencia: list[dict], actual: list[dict]) -> dict:
    """Compara tasas de aceptación y detecta cada regresión de seguridad."""
    base = {c["id"]: c for c in referencia}
    nuevos = {c["id"]: c for c in actual}
    if base.keys() != nuevos.keys() or any(
        any(base[id_][campo] != nuevos[id_][campo] for campo in CAMPOS) for id_ in base
    ):
        raise ValueError("La comparación exige la misma matriz de casos")
    regresiones = [
        c for id_, c in nuevos.items()
        if base[id_]["resultado"] == "aprobado" and c["resultado"] != "aprobado"
    ]
    variacion = {}
    for grupo in (*DISTRIBUCION, "total"):
        filas = [c for c in actual if grupo == "total" or c["categoria"] == grupo]
        antes = sum(base[c["id"]]["resultado"] == "aprobado" for c in filas)
        despues = sum(c["resultado"] == "aprobado" for c in filas)
        variacion[grupo] = round(100 * (despues - antes) / len(filas), 4)
    seguridad = [
        c["id"] for c in regresiones if c["categoria"] == "adversario"
        or c["clasificacion_fallo"] == "seguridad_o_invariante"
    ]
    return {
        "variacion_pp": variacion, "tolerancia_pp": TOLERANCIA_PP,
        "regresiones": [c["id"] for c in regresiones], "regresiones_seguridad": seguridad,
        "aceptada": not seguridad and all(v >= -TOLERANCIA_PP for v in variacion.values()),
    }



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=RAIZ, help="Copia local del código a evaluar")
    parser.add_argument("--referencia", type=Path, help="Copia local para la comparación SDD")
    args = parser.parse_args()
    resultado = evaluar(args.raiz.resolve())
    aprobada = True
    if args.referencia is not None:
        referencia = evaluar(args.referencia.resolve())
        comparacion = comparar_resultados(referencia["casos"], resultado["casos"])
        resultado["comparacion"] = {**comparacion, "referencia": referencia["conteos"]}
        aprobada = comparacion["aceptada"] and referencia["pytest_codigo"] == 0
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return int(
        not aprobada or resultado["pytest_codigo"] != 0 or resultado["conteos"]["aprobado"] != 40
    )


if __name__ == "__main__":
    raise SystemExit(main())
