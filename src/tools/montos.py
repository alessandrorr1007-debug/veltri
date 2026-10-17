"""Primitivas de importes para validar contratos sin aritmética en el modelo."""

from src.tools.catalogo import entero


def subtotal_centimos(precio: int, cantidad: int) -> int:
    """Multiplica importes enteros y cantidades positivas."""
    return entero(precio, "precio", 1) * entero(cantidad, "cantidad", 1)


def total_centimos(subtotales: list[int]) -> int:
    """Suma subtotales no negativos sin conversiones ni floats."""
    return sum(entero(valor, "subtotal") for valor in subtotales)
