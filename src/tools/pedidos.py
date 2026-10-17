"""Idempotencia de borradores locales; no confirma pedidos ni despacha."""

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from src.tools.catalogo import Catalogo


def clave_pedido(cliente: str, seleccion: dict[str, int], canal: str,
                 catalogo: Catalogo) -> str:
    """SHA-256 de cliente|productos|cantidad|canal, con listas ordenadas."""
    # Solo alias opaco, nunca DNI, correo, teléfono o nombre real.
    if not isinstance(cliente, str) or not re.fullmatch(r"demo_[a-z]{1,32}", cliente):
        raise ValueError("Usar un alias sintético demo_ seguido de letras minúsculas")
    if canal not in ("web", "whatsapp"):
        raise ValueError("Canal no admitido")
    lineas = catalogo.lineas(seleccion)
    productos = json.dumps([linea["sku"] for linea in lineas], separators=(",", ":"))
    cantidades = json.dumps([linea["cantidad"] for linea in lineas], separators=(",", ":"))
    return hashlib.sha256(f"{cliente}|{productos}|{cantidades}|{canal}".encode()).hexdigest()


class RegistroDemo:
    """Borradores en memoria, sin persistencia ni garantías entre procesos."""

    def __init__(self) -> None:
        self._registros: dict[str, dict[str, Any]] = {}

    def registrar(self, cliente: str, seleccion: dict[str, int], canal: str,
                  catalogo: Catalogo) -> dict[str, Any]:
        """Repetir una solicitud devuelve el mismo borrador sin otra inserción."""
        clave = clave_pedido(cliente, seleccion, canal, catalogo)
        duplicado = clave in self._registros
        if not duplicado:
            self._registros[clave] = {"clave": clave, "estado": "borrador_demo",
                                      "seleccion": dict(sorted(seleccion.items())),
                                      "hitl_requerido": True}
        return {"duplicado": duplicado, "registros_creados": 0 if duplicado else 1,
                "pedido": deepcopy(self._registros[clave])}

    def consultar(self, clave: str) -> dict[str, Any] | None:
        """Devuelve copia del borrador o ausencia, sin alterar su estado."""
        if not isinstance(clave, str) or not re.fullmatch(r"[a-f0-9]{64}", clave):
            raise ValueError("Clave de borrador inválida")
        return deepcopy(self._registros.get(clave))
