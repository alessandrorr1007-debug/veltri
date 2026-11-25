"""Regresiones de la demo de cuatro pilares con el framework real y MockLLM."""

import pytest
from langchain_core.messages import SystemMessage, ToolMessage
from pydantic import ValidationError

from src.academic.deep_agents import AdaptadorMock
from src.academic.deep_agents_semana11 import (
    PROMPT_CATALOGO,
    PROMPT_COORDINADOR,
    PROMPT_REVISION,
    ejecutar_semana11,
)
from src.academic.memoria_semana11 import RUTA_HALLAZGOS, evidencia_canonica, verificar_archivo
from src.schemas.academico import SalidaAcademica


def test_cuatro_pilares_en_framework_real(monkeypatch):
    instrucciones = {
        "coordinador": PROMPT_COORDINADOR,
        "DA-Catalogo": PROMPT_CATALOGO,
        "DA-Revision": PROMPT_REVISION,
    }
    roles_verificados = set()
    generar = AdaptadorMock._generate

    def verificar_instrucciones(self, messages, *args, **kwargs):
        assert any(
            isinstance(mensaje, SystemMessage)
            and instrucciones[self._rol] in mensaje.text
            for mensaje in messages
        )
        roles_verificados.add(self._rol)
        return generar(self, messages, *args, **kwargs)

    monkeypatch.setattr(AdaptadorMock, "_generate", verificar_instrucciones)
    auditoria = []
    resultado = ejecutar_semana11({}, auditoria)
    assert roles_verificados == set(instrucciones)
    mensajes = resultado["messages"]
    llamadas = [c for m in mensajes for c in getattr(m, "tool_calls", [])]
    assert [c["name"] for c in llamadas] == [
        "write_todos", "task", "write_file", "read_file", "write_todos", "task", "write_todos",
    ]
    delegaciones = [c for c in llamadas if c["name"] == "task"]
    assert [c["args"]["subagent_type"] for c in delegaciones] == ["DA-Catalogo", "DA-Revision"]
    hallazgo = evidencia_canonica(llamadas[2]["args"]["content"])
    assert llamadas[2]["args"]["file_path"] == RUTA_HALLAZGOS
    assert hallazgo in delegaciones[1]["args"]["description"]
    assert verificar_archivo(resultado["files"], hallazgo) == hallazgo
    assert all(t["status"] == "completed" for t in resultado["todos"])
    assert all(m.status == "success" for m in mensajes if isinstance(m, ToolMessage))
    assert SalidaAcademica.model_validate_json(mensajes[-1].content) == SalidaAcademica()
    for rol in ("DA-Catalogo", "DA-Revision"):
        assert any(a["rol"] == rol and any(
            h["nombre"] == "revisar_fixture_sintetico" and h["estado"] == "success"
            for h in a["respuestas_herramientas"]
        ) for a in auditoria)


def test_dos_ejecuciones_sin_colision_de_archivos():
    for _ in range(2):
        resultado = ejecutar_semana11({})
        assert RUTA_HALLAZGOS in resultado["files"]


@pytest.mark.parametrize("entrada", [{"mensaje": "no admitido"}, {"escenario": "otro"}])
def test_entrada_cerrada_semana11(entrada):
    with pytest.raises(ValidationError):
        ejecutar_semana11(entrada)
