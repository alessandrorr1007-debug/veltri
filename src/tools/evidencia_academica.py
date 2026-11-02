"""Herramienta académica de solo lectura; nunca autoriza una operación comercial."""

from src.tools.catalogo import Catalogo
from src.tools.inventario import comprobar_stock


def revisar_fixture_sintetico() -> dict:
    """Reduce evidencia local a atributos permitidos, sin exponer identificadores."""
    stock = comprobar_stock(Catalogo(), {"CPU-AMD-5500": 1})
    return {"sintetico": True, "requiere_revision": stock["hitl_requerido"],
            "efecto_comercial": False}
