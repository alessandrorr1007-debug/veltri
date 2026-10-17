"""Vectores léxicos locales y guardas de privacidad para el corpus de demo."""

import hashlib
import math
import re
import unicodedata

VERSION_VECTOR = "hash_lexico_256_v1"
DIMENSION = 256
STOP = {"de", "la", "el", "los", "las", "en", "un", "una", "y", "o", "a", "por", "para"}
PATRONES_PRIVADOS = [
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?<!\d)\d{8,11}(?!\d)"),
    re.compile(r"(?i)\b(?:dni|ruc|telefono|teléfono|celular|correo|nombre_cliente)\s*[:=]"),
    re.compile(r"(?<!\d)(?:\+51[ -]?)?9\d{2}[ -]\d{3}[ -]\d{3}(?!\d)"),
]


def validar_tenant(tenant: str) -> str:
    """Sin valor por defecto y sin normalizaciones que mezclen tenants."""
    if not isinstance(tenant, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", tenant):
        raise ValueError("Tenant explícito inválido")
    return tenant


def validar_texto_publico(texto: str, maximo: int = 12000) -> None:
    """Rechaza patrones comunes de PII sin incluir el contenido en el error."""
    if not isinstance(texto, str) or not texto.strip() or len(texto) > maximo:
        raise ValueError("Contenido de conocimiento inválido")
    if any(p.search(texto) for p in PATRONES_PRIVADOS):
        raise ValueError("Contenido rechazado por posible dato personal")


def tokens(texto: str) -> set[str]:
    """Normaliza acentos; no contiene reglas ni cálculos de negocio."""
    normal = "".join(c for c in unicodedata.normalize("NFD", texto.casefold())
                     if unicodedata.category(c) != "Mn")
    return set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", normal)) - STOP


def vector(texto: str) -> list[float]:
    """Hash estable de tokens; no es embedding semántico ni medida de confianza."""
    valores = [0.0] * DIMENSION
    for token in sorted(tokens(texto)):
        digest = hashlib.sha256(token.encode()).digest()
        indice = int.from_bytes(digest[:4], "big") % DIMENSION
        valores[indice] += 1.0 if digest[4] % 2 else -1.0
    norma = math.sqrt(sum(v * v for v in valores))
    if not norma:
        raise ValueError("El texto no tiene términos recuperables")
    return [v / norma for v in valores]
