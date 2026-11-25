"""Reglas compartidas del único paso de planificación comercial."""

from typing import get_args

from src.core.prompts import componer_prompt
from src.schemas.agentes import Accion


def prompt_plan(
    *,
    rol: str,
    contexto: str,
    herramientas: str,
    proceso: str,
    limites: str,
    bloqueo: str,
    accion: Accion | None = None,
) -> str:
    opciones = "Usa accion=" + accion + "." if accion else (
        "Acciones: " + ", ".join(get_args(Accion)) + "."
    )
    return componer_prompt(
        rol=rol,
        contexto=contexto,
        herramientas="El modelo no invoca herramientas. " + herramientas,
        proceso=proceso,
        limites=limites + " No inventes cifras, evidencia ni estados; no autorices operaciones.",
        parada="Emite un solo plan. Evita reintentos, pasos extra y texto explicativo.",
        hitl=bloqueo + " La compuerta aplica la revisión; p y c no autorizan.",
        salida="Solo JSON PlanModelo con accion, p y c. " + opciones
        + " p y c son estimaciones no calibradas en [0,1].",
    )
