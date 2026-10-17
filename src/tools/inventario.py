"""Consulta de stock y alternativas; nunca reserva ni altera inventario."""

from typing import Any

from src.tools.catalogo import Catalogo


def comprobar_stock(catalogo: Catalogo, cantidades: dict[str, int]) -> dict[str, Any]:
    """Agrega faltantes por SKU y cantidad; stock cero siempre bloquea."""
    lineas = catalogo.lineas(cantidades)
    faltantes = [{"sku": linea["sku"], "solicitado": linea["cantidad"],
                  "disponible": catalogo.obtener(linea["sku"])["stock"],
                  "motivo": "stock_insuficiente"}
                 for linea in lineas
                 if catalogo.obtener(linea["sku"])["stock"] < linea["cantidad"]]
    return {"disponible": not faltantes, "hitl_requerido": bool(faltantes),
            "faltantes": faltantes, "fuente": "data/catalogo.json"}


def alternativas(catalogo: Catalogo, sku: str) -> list[str]:
    """Sugiere misma categoría y socket/RAM; no aprueba una sustitución."""
    original = catalogo.obtener(sku)
    spec = original["especificaciones"]
    return [p["sku"] for p in catalogo.listar(original["categoria"])
            if p["sku"] != sku and p["stock"] > 0
            and all(p["especificaciones"].get(k) == spec[k]
                    for k in ("socket", "ram_tipo") if k in spec)]
