"""Comparación de importes: no consulta bancos ni acredita transferencias."""

from typing import Any

from src.tools.catalogo import entero


def comparar_pago(total_centimos: int, pagado_centimos: int,
                  moneda: str = "PEN") -> dict[str, Any]:
    """Todo pago sigue no conciliado hasta contar con evidencia autorizada."""
    entero(total_centimos, "total", 1)
    entero(pagado_centimos, "pagado")
    coincide = moneda == "PEN" and total_centimos == pagado_centimos
    return {"montos_coinciden": coincide,
            "diferencia_centimos": pagado_centimos - total_centimos if moneda == "PEN" else None,
            "estado": "no_conciliado", "hitl_requerido": True,
            "motivos": (["pago_discrepante"] if not coincide else [])
                       + ["falta_evidencia_bancaria_autorizada"]}
