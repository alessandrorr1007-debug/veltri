"""Clasificación determinista de la compuerta con umbrales protegidos."""

from typing import Literal

from src.core.umbrales import TAU_AUTO, TAU_REV

Destino = Literal["ejecutar", "revision_humana", "escalar"]


def clasificar(p: float, tiene_bloqueos: bool) -> Destino:
    """Invariantes por encima del puntaje; no realiza acciones de negocio."""
    if tiene_bloqueos:
        return "revision_humana"
    if p >= TAU_AUTO:
        return "ejecutar"
    if p >= TAU_REV:
        return "revision_humana"
    return "escalar"
