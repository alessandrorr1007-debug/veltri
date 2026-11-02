"""Composición LCEL determinista sobre un fixture académico cerrado."""

from typing import Any

from langchain_core.runnables import RunnableLambda, RunnableParallel

from src.schemas.academico import EntradaAcademica, SalidaAcademica
from src.tools.catalogo import Catalogo
from src.tools.inventario import comprobar_stock


def crear_pipeline():
    """Validación -> ramas paralelas -> contrato de salida mediante operador LCEL."""
    return (
        RunnableLambda(EntradaAcademica.model_validate)
        | RunnableParallel(
            escenario=RunnableLambda(_escenario),
            revision=RunnableLambda(lambda _: comprobar_stock(
                Catalogo(), {"CPU-AMD-5500": 1})["hitl_requerido"]),
        )
        | RunnableLambda(_salida)
    )


def _escenario(entrada: EntradaAcademica) -> str:
    return entrada.escenario


def _salida(ramas: dict[str, Any]) -> SalidaAcademica:
    return SalidaAcademica(requiere_revision=ramas["revision"])
