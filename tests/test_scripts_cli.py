"""Regresión de los puntos de entrada, no solo de sus componentes internos."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.demo_academica import ejecutar_demo

RAIZ = Path(__file__).resolve().parents[1]


def entorno_local() -> dict[str, str]:
    """No hereda credenciales; conserva la guarda de red de la verificación padre."""
    entorno = {k: v for k, v in os.environ.items() if not any(
        palabra in k.upper() for palabra in ("KEY", "TOKEN", "SECRET", "PASSWORD", "PROXY"))}
    entorno.update({"LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false",
                    "VELTRI_TRACING_ENABLED": "0", "VELTRI_TRACING_ALLOW_EXTERNAL": "0",
                    "USE_MOCK_LLM": "1", "PYTHONUTF8": "1"})
    return entorno


@pytest.mark.parametrize("modo", ["archivo_raiz", "archivo_otra_carpeta", "modulo"])
def test_demo_cli_real_sin_alterar_evidencia(tmp_path, modo):
    originales = [RAIZ / "docs/evidencias/semana10-entrega-final/ejecuciones.json",
                  RAIZ / "docs/evidencias/semana10-fase43/ejecucion-unica.json",
                  RAIZ / "docs/entrega-semana10/Veltri_Semana10_Informe_Academico.docx"]
    antes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in originales]
    destino = tmp_path / "ejecucion"
    comando = [sys.executable]
    comando += (["-m", "scripts.demo_academica"] if modo == "modulo" else
                [str(RAIZ / "scripts/demo_academica.py")])
    resultado = subprocess.run(comando + ["--salida", str(destino)],
                               cwd=tmp_path if modo == "archivo_otra_carpeta" else RAIZ,
                               env=entorno_local(), capture_output=True, text=True,
                               encoding="utf-8", timeout=90)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    resumen = json.loads(resultado.stdout)
    assert resumen["envio_externo"] is False
    assert resumen["lcel"]["requiere_revision"] is True
    evidencia = json.loads((destino / "ejecuciones.json").read_text(encoding="utf-8"))
    assert {h["salida"]["resultado"] for h in evidencia["hitl"]} == {
        "aprobar", "rechazar", "corregir"}
    assert all(t["status"] == "completed" for t in evidencia["deepagents"]["todos"])
    grafo = json.loads((destino / "grafo-comercial.json").read_text(encoding="utf-8"))
    assert len(grafo["nodes"]) == 13
    assert len(grafo["edges"]) == 20
    assert antes == [hashlib.sha256(p.read_bytes()).hexdigest() for p in originales]


def test_demo_no_sobrescribe_destino_existente(tmp_path):
    existente = tmp_path / "evidencia.json"
    existente.write_text("conservar", encoding="utf-8")
    with pytest.raises(FileExistsError):
        ejecutar_demo(tmp_path)
    assert existente.read_text(encoding="utf-8") == "conservar"


def test_demo_rechaza_directorio_original(monkeypatch, tmp_path):
    from scripts import demo_academica

    monkeypatch.setattr(demo_academica, "RAIZ", tmp_path)
    destino = tmp_path / "docs/evidencias/nueva"
    with pytest.raises(ValueError, match="protegidas"):
        ejecutar_demo(destino)
    assert not destino.exists()


def test_ayuda_demo_no_ejecuta_modelos(tmp_path):
    resultado = subprocess.run([sys.executable, str(RAIZ / "scripts/demo_academica.py"),
                                "--help"], cwd=tmp_path, env=entorno_local(),
                               capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert resultado.returncode == 0
    assert "--salida" in resultado.stdout
    assert not list(tmp_path.iterdir())
