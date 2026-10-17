"""Pruebas de estructura e invariantes del proyecto (corren desde el primer día)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"

CONSTRUCTORES_DE_MODELO = [
    "ChatGoogleGenerativeAI",
    "ChatOpenAI",
    "ChatOllama",
    "ChatBedrock",
    "google.generativeai",
]


def test_solo_core_llm_instancia_modelos() -> None:
    """Invariante 1: ningún módulo, salvo core/llm.py, instancia un modelo directamente."""
    permitido = SRC / "core" / "llm.py"
    infractores = []
    for archivo in SRC.rglob("*.py"):
        if archivo == permitido:
            continue
        texto = archivo.read_text(encoding="utf-8")
        if any(nombre in texto for nombre in CONSTRUCTORES_DE_MODELO):
            infractores.append(archivo.relative_to(RAIZ).as_posix())
    assert not infractores, f"Instancian modelos fuera de get_llm(): {infractores}"


def test_umbrales_son_coherentes() -> None:
    """Los umbrales HITL cumplen 0 < TAU_REV < TAU_AUTO <= 1."""
    from src.core.umbrales import TAU_AUTO, TAU_REV

    assert 0 < TAU_REV < TAU_AUTO <= 1


def test_casos_dorados_estan_completos() -> None:
    """Existen los 7 casos CP-1 a CP-7 con entrada y resultado esperado."""
    datos = json.loads((RAIZ / "evals" / "casos_dorados.json").read_text(encoding="utf-8"))
    ids = [caso["id"] for caso in datos["casos"]]
    assert ids == [f"CP-{n}" for n in range(1, 8)]
    for caso in datos["casos"]:
        assert "entrada" in caso and "esperado" in caso


def test_existe_linea_base() -> None:
    assert (RAIZ / "evals" / "linea_base.json").is_file()


def test_no_hay_secretos_en_el_repositorio() -> None:
    resultado = subprocess.run(
        [sys.executable, "scripts/escanear_secretos.py"],
        cwd=RAIZ, capture_output=True, text=True, check=False,
    )
    assert resultado.returncode == 0, resultado.stdout


def test_gitignore_protege_env() -> None:
    contenido = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in contenido


def test_agents_md_apunta_a_gemini_md() -> None:
    """AGENTS.md es solo un puntero: las reglas viven en GEMINI.md (una sola fuente)."""
    assert "GEMINI.md" in (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
    assert (RAIZ / "GEMINI.md").is_file()
