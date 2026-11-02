"""Pruebas locales de composición, pausa nativa y delegación real."""

import pytest
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableSequence
from langgraph.types import Command
from pydantic import ValidationError

from src.academic.deep_agents import ejecutar
from src.academic.hitl import crear_grafo
from src.academic.lcel import crear_pipeline
from src.schemas.academico import SalidaAcademica


def test_lcel_composicion_real():
    pipeline = crear_pipeline()
    assert isinstance(pipeline, RunnableSequence)
    assert pipeline.invoke({}) == SalidaAcademica()


@pytest.mark.parametrize("entrada", [{"mensaje": "no_admitido"}, {"escenario": "otro"}])
def test_entrada_cerrada(entrada):
    with pytest.raises(ValidationError):
        crear_pipeline().invoke(entrada)
    with pytest.raises(ValidationError):
        ejecutar(entrada)


@pytest.mark.parametrize("accion", ["aprobar", "rechazar", "corregir"])
def test_hitl_interrupcion_y_reanudacion(accion):
    grafo = crear_grafo()
    config = {"configurable": {"thread_id": accion}}
    pausa = grafo.invoke({"sintetico": True}, config)
    assert pausa["__interrupt__"]
    assert grafo.get_state(config).next == ("revision_humana",)
    resultado = grafo.invoke(Command(resume={"accion": accion}), config)
    assert resultado["resultado"] == accion
    assert not grafo.get_state(config).next


def test_hitl_decision_invalida():
    grafo = crear_grafo()
    config = {"configurable": {"thread_id": "invalida"}}
    grafo.invoke({"sintetico": True}, config)
    with pytest.raises(ValidationError):
        grafo.invoke(Command(resume={"accion": "despachar"}), config)


def test_deepagents_plan_y_delegacion():
    auditoria = []
    resultado = ejecutar({}, auditoria)
    mensajes = resultado["messages"]
    llamadas = [c for m in mensajes for c in getattr(m, "tool_calls", [])]
    delegaciones = [c["args"]["subagent_type"] for c in llamadas if c["name"] == "task"]
    assert delegaciones == ["DA-Catalogo", "DA-Revision"]
    assert all(t["status"] == "completed" for t in resultado["todos"])
    respuestas = [m for m in mensajes if isinstance(m, ToolMessage)]
    assert len(respuestas) == 4
    assert all(m.status != "error" for m in respuestas)
    assert SalidaAcademica.model_validate_json(mensajes[-1].content) == SalidaAcademica()
    for rol in ("DA-Catalogo", "DA-Revision"):
        assert any(a["rol"] == rol and any(
            h["nombre"] == "revisar_fixture_sintetico" and h["estado"] == "success"
            for h in a["respuestas_herramientas"]) for a in auditoria)
