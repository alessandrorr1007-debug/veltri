"""Ejecuta demos locales sin trazas y exporta evidencia verificable, sin credenciales."""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langsmith import tracing_context

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def validar_salida(carpeta: Path) -> Path:
    """Rechaza archivos existentes y ubicaciones protegidas antes de ejecutar."""
    protegidos = (RAIZ / "docs/evidencias", RAIZ / "docs/entrega-semana10")
    carpeta = carpeta.resolve()
    if any(carpeta == p or p in carpeta.parents for p in protegidos):
        raise ValueError("La salida no puede estar dentro de las evidencias protegidas")
    if carpeta.exists():
        raise FileExistsError("La salida debe ser un directorio nuevo")
    return carpeta


def ejecutar_demo(carpeta: Path) -> dict[str, Any]:
    """Exporta a un directorio nuevo; nunca reemplaza evidencias ni usa claves."""
    carpeta = validar_salida(carpeta)
    carpeta.mkdir(parents=True, exist_ok=False)
    for bandera in (
        "LANGSMITH_TRACING",
        "LANGCHAIN_TRACING_V2",
        "VELTRI_TRACING_ENABLED",
        "VELTRI_TRACING_ALLOW_EXTERNAL",
    ):
        os.environ[bandera] = "false" if bandera.startswith("LANG") else "0"

    from src.academic.deep_agents import crear_agente, ejecutar
    from src.academic.hitl import crear_grafo
    from src.academic.lcel import crear_pipeline
    from src.config import Configuracion
    from src.core.hitl import BandejaRevision
    from src.graph.nodes import Servicios
    from src.graph.workflow import crear_grafo as grafo_comercial
    from src.schemas.decision import EvidenciaInformacion, SolicitudDecision
    from src.schemas.hitl import ResolucionRevision
    from src.tools.catalogo import Catalogo
    from src.tools.registro import RegistroPorTenant

    with tracing_context(enabled=False):
        lcel = crear_pipeline().invoke({}).model_dump()
        hitl = []
        for accion in ("aprobar", "rechazar", "corregir"):
            grafo = crear_grafo()
            config: RunnableConfig = {"configurable": {"thread_id": str(uuid4())}}
            pausa = grafo.invoke({"sintetico": True}, config)
            siguiente = list(grafo.get_state(config).next)
            salida = grafo.invoke(Command(resume={"accion": accion}), config)
            hitl.append(
                {
                    "decision_simulada": accion,
                    "interrupcion": bool(pausa["__interrupt__"]),
                    "checkpoint_next": siguiente,
                    "salida": salida,
                }
            )
        auditoria = []
        deep = ejecutar({}, auditoria)
        bandeja = BandejaRevision()
        solicitud = SolicitudDecision(
            opcion="informar",
            p=0.6,
            c=1.0,
            origen_puntuacion="prueba_no_calibrada",
            evidencia=EvidenciaInformacion(tipo="informacion", fuentes=["data/politicas.md"]),
        )
        revision = bandeja.encolar("demo_academico", solicitud).revision
        resuelta = bandeja.resolver(
            "demo_academico",
            revision.id,
            ResolucionRevision(
                accion="solicitar_correccion", revisor="demo_operador", motivo="requiere_correccion"
            ),
        )
        mensajes = [m.model_dump(mode="json") for m in deep["messages"]]
        datos = {
            "fecha_utc": datetime.now(timezone.utc).isoformat(),
            "fuente": "scripts/demo_academica.py",
            "modelo": "MockLLM programado",
            "envio_externo": False,
            "lcel": lcel,
            "hitl": hitl,
            "bandeja_existente": {
                "antes": revision.estado,
                "despues": resuelta.estado,
                "efecto_comercial": False,
            },
            "deepagents": {
                "todos": deep["todos"],
                "messages": mensajes,
                "auditoria_modelo": auditoria,
            },
            "versiones": {
                p: version(p)
                for p in ("deepagents", "langchain", "langchain-core", "langgraph", "langsmith")
            },
        }
        (carpeta / "ejecuciones.json").write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        comercial = grafo_comercial(
            Servicios(
                configuracion=Configuracion(),
                guiones={},
                catalogo=Catalogo(),
                registro=RegistroPorTenant(),
                bandeja=BandejaRevision(),
                almacen=None,
            )
        )
        for nombre, compilado in [
            ("hitl-nativo", crear_grafo()),
            ("deep-agents", crear_agente()),
            ("grafo-comercial", comercial),
        ]:
            (carpeta / f"{nombre}.mmd").write_text(
                compilado.get_graph().draw_mermaid(), encoding="utf-8"
            )
        (carpeta / "grafo-comercial.json").write_text(
            json.dumps(comercial.get_graph().to_json(), indent=2), encoding="utf-8"
        )
    return {
        "lcel": lcel,
        "hitl_caminos": len(hitl),
        "deepagents_todos": deep["todos"],
        "envio_externo": False,
        "salida": str(carpeta),
    }


def main() -> int:
    """CLI local; --help no ejecuta demos ni escribe resultados."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, help="Directorio nuevo para resultados de esta demo")
    args = parser.parse_args()
    # TemporaryDirectory no se usa: la evidencia nueva debe sobrevivir al proceso.
    carpeta = args.salida or Path(tempfile.gettempdir()) / ("veltri-demo-" + uuid4().hex)
    try:
        carpeta = validar_salida(carpeta)
    except (FileExistsError, ValueError) as error:
        parser.error(str(error))
    resultado = ejecutar_demo(carpeta)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
