"""Cotización exacta en céntimos con bloqueos explícitos y fuentes locales."""

from typing import Any

from src.tools.catalogo import Catalogo, entero
from src.tools.hardware import validar_configuracion
from src.tools.inventario import comprobar_stock


def cotizar(catalogo: Catalogo, seleccion: dict[str, int],
            maximo_centimos: int | None = None) -> dict[str, Any]:
    """Calcula subtotal de demo sin añadir IGV, envío ni servicios implícitos."""
    if maximo_centimos is not None:
        entero(maximo_centimos, "presupuesto")
    lineas = catalogo.lineas(seleccion)
    total = sum(linea["subtotal_centimos"] for linea in lineas)
    stock = comprobar_stock(catalogo, seleccion)
    tecnico = validar_configuracion(catalogo, seleccion)
    sobre = maximo_centimos is not None and total > maximo_centimos
    return {"moneda": "PEN", "naturaleza": "demostracion_sintetica", "lineas": lineas,
            "total_centimos": total, "sobre_presupuesto": sobre, "stock": stock,
            "tecnico": tecnico, "hitl_requerido": True, "genera_proforma": False,
            "bloqueos": (["sobre_presupuesto"] if sobre else [])
                        + (["stock_insuficiente"] if not stock["disponible"] else [])
                        + tecnico["conflictos"],
            "aviso": "Simulación pendiente de revisión; no es una proforma aprobada."}
