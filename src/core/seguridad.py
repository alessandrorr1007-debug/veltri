"""Guardas locales antes del modelo; no equivalen a un detector exhaustivo."""

import re
import unicodedata

from src.knowledge.vectorizacion import validar_texto_publico


class EntradaBloqueada(ValueError):
    """Error público sin repetir el mensaje rechazado."""


def validar_entrada_modelo(texto: str) -> None:
    """Rechaza patrones de PII e instrucciones de evasión conocidas."""
    try:
        validar_texto_publico(texto)
    except ValueError:
        raise EntradaBloqueada("entrada_no_admitida") from None
    normal = "".join(
        c for c in unicodedata.normalize("NFD", texto.casefold()) if unicodedata.category(c) != "Mn"
    )
    patrones = (
        r"ignore.{0,40}(previous|instructions)",
        r"ignora.{0,40}(instrucciones|reglas)",
        r"reveal.{0,40}(prompt|keys)",
        r"revela.{0,40}(prompt|claves)",
    )
    if any(re.search(p, normal, re.DOTALL) for p in patrones):
        raise EntradaBloqueada("instruccion_sospechosa")
