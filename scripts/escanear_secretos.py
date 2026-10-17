"""Busca claves y secretos en el repositorio. Sale con código 1 si encuentra alguno."""

from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAIZ = BASE / "plantilla" if (BASE / "plantilla").is_dir() else BASE

CARPETAS_IGNORADAS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "chroma_db",
}
ARCHIVOS_IGNORADOS = {".env", ".env.example"}
EXTENSIONES_BINARIAS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2",
    ".ttf", ".otf", ".zip", ".pdf", ".sqlite3", ".pyc",
}

PATRONES = {
    "Clave de Google (AIza...)": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "Token de GitHub": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "Clave de AWS": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Clave estilo sk-": re.compile(r"sk-[A-Za-z0-9]{32,}"),
    "Clave privada": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Asignación sospechosa": re.compile(
        r"""(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['"][A-Za-z0-9_\-/+=]{16,}['"]"""
    ),
}


def _enmascarar(texto: str) -> str:
    texto = texto.strip()
    return texto[:6] + "..." + texto[-2:] if len(texto) > 10 else "***"


def escanear(raiz: Path = RAIZ) -> list[str]:
    """Devuelve una lista de hallazgos con formato 'ruta:línea [tipo] vista previa'."""
    hallazgos: list[str] = []
    for ruta in raiz.rglob("*"):
        if not ruta.is_file():
            continue
        partes = set(ruta.relative_to(raiz).parts)
        if partes & CARPETAS_IGNORADAS:
            continue
        if ruta.name in ARCHIVOS_IGNORADOS or ruta.suffix.lower() in EXTENSIONES_BINARIAS:
            continue
        if ruta.stat().st_size > 1_000_000:
            continue
        try:
            contenido = ruta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for numero, linea in enumerate(contenido.splitlines(), start=1):
            for tipo, patron in PATRONES.items():
                coincidencia = patron.search(linea)
                if coincidencia:
                    rel = ruta.relative_to(raiz).as_posix()
                    vista = _enmascarar(coincidencia.group(0))
                    hallazgos.append(f"{rel}:{numero} [{tipo}] {vista}")
    return hallazgos


def main() -> int:
    hallazgos = escanear()
    if hallazgos:
        print("POSIBLES SECRETOS ENCONTRADOS:")
        for h in hallazgos:
            print(" -", h)
        print("\nDetente: no subas nada. Si la clave es real, revócala y genera otra.")
        return 1
    print("Escaneo de secretos: sin hallazgos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
