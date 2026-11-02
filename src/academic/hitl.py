"""HITL nativo académico con checkpoint en memoria y decisión validada."""

from typing import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, ConfigDict


class Decision(BaseModel):
    """Decisión simulada, sin aprobar pedidos ni pagos."""

    model_config = ConfigDict(extra="forbid")
    accion: Literal["aprobar", "rechazar", "corregir"]


class Estado(TypedDict, total=False):
    sintetico: bool
    resultado: str


def crear_grafo():
    """Cada instancia mantiene sus propios checkpoints; no persisten entre procesos."""
    def revisar(estado: Estado):
        decision = Decision.model_validate(interrupt({"tipo": "revision_sintetica"}))
        return {"resultado": decision.accion}

    grafo = StateGraph(Estado)
    grafo.add_node("revision_humana", revisar)
    grafo.add_edge(START, "revision_humana")
    grafo.add_edge("revision_humana", END)
    return grafo.compile(checkpointer=InMemorySaver())
