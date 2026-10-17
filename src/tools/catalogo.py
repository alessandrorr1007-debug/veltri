"""Lectura aislada del catálogo de demostración y validación de entradas."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DATOS = Path(__file__).resolve().parents[2] / "data"


def entero(valor: int, nombre: str, minimo: int = 0) -> int:
    """Rechaza bool, floats y valores fuera del dominio."""
    if type(valor) is not int or valor < minimo:
        raise ValueError(f"{nombre}: se requiere entero >= {minimo}")
    return valor


class Catalogo:
    """Instantánea local; consultar no modifica archivos ni reserva inventario."""

    def __init__(self, ruta: Path = DATOS) -> None:
        datos = json.loads((ruta / "catalogo.json").read_text(encoding="utf-8"))
        self.reglas = json.loads((ruta / "compatibilidad.json").read_text(encoding="utf-8"))
        self._productos = {}
        if datos["moneda"] != "PEN":
            raise ValueError("Moneda de catálogo no admitida")
        for producto in datos["productos"]:
            sku = producto["sku"]
            if not isinstance(sku, str) or not sku or sku in self._productos:
                raise ValueError("SKU vacío o duplicado")
            entero(producto["precio_centimos"], "precio", 1)
            entero(producto["stock"], "stock")
            self._productos[sku] = producto

    def obtener(self, sku: str) -> dict[str, Any]:
        """Obtiene copia del producto o rechaza un identificador desconocido."""
        if sku not in self._productos:
            raise ValueError(f"SKU desconocido: {sku}")
        return deepcopy(self._productos[sku])

    def listar(self, categoria: str | None = None) -> list[dict[str, Any]]:
        """Devuelve productos en orden estable de SKU."""
        return [self.obtener(sku) for sku in sorted(self._productos)
                if categoria is None or self._productos[sku]["categoria"] == categoria]

    def lineas(self, cantidades: dict[str, int]) -> list[dict[str, Any]]:
        """Valida cantidades positivas y conserva fuente por cada línea."""
        if not cantidades:
            raise ValueError("La selección no puede estar vacía")
        resultado = []
        for sku, cantidad in sorted(cantidades.items()):
            entero(cantidad, "cantidad", 1)
            producto = self.obtener(sku)
            resultado.append({"sku": sku, "cantidad": cantidad,
                              "precio_unitario_centimos": producto["precio_centimos"],
                              "subtotal_centimos": producto["precio_centimos"] * cantidad,
                              "fuente": "data/catalogo.json#" + sku})
        return resultado
