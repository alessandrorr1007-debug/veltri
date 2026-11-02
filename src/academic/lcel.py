"""Composición LCEL determinista sobre un fixture académico cerrado."""

from langchain_core.runnables import RunnableLambda, RunnableParallel

from src.schemas.academico import EntradaAcademica, SalidaAcademica
from src.tools.catalogo import Catalogo
from src.tools.inventario import comprobar_stock


def crear_pipeline():
    """Validación -> ramas paralelas -> contrato de salida mediante operador LCEL."""
    return (
        RunnableLambda(EntradaAcademica.model_validate)
        | RunnableParallel(
            escenario=RunnableLambda(lambda entrada: entrada.escenario),
            revision=RunnableLambda(lambda _: comprobar_stock(
                Catalogo(), {"CPU-AMD-5500": 1})["hitl_requerido"]),
        )
        | RunnableLambda(lambda ramas: SalidaAcademica(requiere_revision=ramas["revision"]))
    )
