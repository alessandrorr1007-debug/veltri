"""Ejecuta demos locales sin trazas y exporta evidencia verificable, sin credenciales."""

import json
import os
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
for bandera in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2",
                "VELTRI_TRACING_ENABLED", "VELTRI_TRACING_ALLOW_EXTERNAL"):
    os.environ[bandera] = "false" if bandera.startswith("LANG") else "0"

from langgraph.types import Command  # noqa: E402
from langsmith import tracing_context  # noqa: E402

from src.academic.deep_agents import crear_agente, ejecutar  # noqa: E402
from src.academic.hitl import crear_grafo  # noqa: E402
from src.academic.lcel import crear_pipeline  # noqa: E402
from src.core.hitl import BandejaRevision  # noqa: E402
from src.graph.workflow import crear_grafo as grafo_comercial  # noqa: E402
from src.schemas.decision import SolicitudDecision  # noqa: E402
from src.schemas.hitl import ResolucionRevision  # noqa: E402


def main():
    """Exporta resultados reales; las decisiones humanas aquí son fixtures simulados."""
    carpeta = RAIZ / "docs/evidencias/semana10-entrega-final"
    carpeta.mkdir(parents=True, exist_ok=True)
    with tracing_context(enabled=False):
        lcel = crear_pipeline().invoke({}).model_dump()
        hitl = []
        for accion in ("aprobar", "rechazar", "corregir"):
            grafo = crear_grafo()
            config = {"configurable": {"thread_id": str(uuid4())}}
            pausa = grafo.invoke({"sintetico": True}, config)
            siguiente = list(grafo.get_state(config).next)
            salida = grafo.invoke(Command(resume={"accion": accion}), config)
            hitl.append({"decision_simulada": accion, "interrupcion": bool(pausa["__interrupt__"]),
                         "checkpoint_next": siguiente, "salida": salida})
        auditoria = []
        deep = ejecutar({}, auditoria)
        bandeja = BandejaRevision()
        solicitud = SolicitudDecision(
            opcion="informar", p=0.6, c=1.0, origen_puntuacion="prueba_no_calibrada",
            evidencia={"tipo": "informacion", "fuentes": ["data/politicas.md"]})
        revision = bandeja.encolar("demo_academico", solicitud).revision
        resuelta = bandeja.resolver("demo_academico", revision.id, ResolucionRevision(
            accion="solicitar_correccion", revisor="demo_operador", motivo="requiere_correccion"))
        mensajes = [m.model_dump(mode="json") for m in deep["messages"]]
        datos = {"fecha_utc": datetime.now(timezone.utc).isoformat(),
                 "fuente": "scripts/demo_academica.py", "modelo": "MockLLM programado",
                 "envio_externo": False, "lcel": lcel, "hitl": hitl,
                 "bandeja_existente": {"antes": revision.estado, "despues": resuelta.estado,
                                       "efecto_comercial": False},
                 "deepagents": {"todos": deep["todos"], "messages": mensajes,
                                "auditoria_modelo": auditoria},
                 "versiones": {p: version(p) for p in (
                     "deepagents", "langchain", "langchain-core", "langgraph", "langsmith")}}
        (carpeta / "ejecuciones.json").write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        for nombre, compilado in [("hitl-nativo", crear_grafo()),
                                   ("deep-agents", crear_agente()),
                                   ("grafo-comercial", grafo_comercial(None))]:
            (carpeta / f"{nombre}.mmd").write_text(
                compilado.get_graph().draw_mermaid(), encoding="utf-8")
        (carpeta / "grafo-comercial.json").write_text(
            json.dumps(grafo_comercial(None).get_graph().to_json(), indent=2), encoding="utf-8")
    print(json.dumps({"lcel": lcel, "hitl_caminos": len(hitl),
                      "deepagents_todos": deep["todos"], "envio_externo": False}, indent=2))


if __name__ == "__main__":
    main()
