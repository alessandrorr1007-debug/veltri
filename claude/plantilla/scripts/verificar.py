"""Verificación completa: ruff + pytest + escaneo de secretos.

Uso:
    python scripts/verificar.py            # verificación estándar
    python scripts/verificar.py --mypy     # agrega tipado estricto con mypy
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAIZ = BASE / "plantilla" if (BASE / "plantilla").is_dir() else BASE


def _ejecutar(nombre: str, comando: list[str]) -> tuple[str, str]:
    """Ejecuta un comando y devuelve (nombre, estado) con estado OK, FALLA u OMITIDO."""
    resultado = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True, check=False)
    salida = (resultado.stdout + resultado.stderr).strip()
    if "No module named" in salida and resultado.returncode != 0:
        print(f"\n[{nombre}] OMITIDO: {salida.splitlines()[-1]}")
        print("  Instala las dependencias: pip install -r requirements-dev.txt")
        return nombre, "OMITIDO"
    print(f"\n[{nombre}]\n{salida}")
    return nombre, "OK" if resultado.returncode == 0 else "FALLA"


def main() -> int:
    py = sys.executable
    pasos = [
        ("ruff", [py, "-m", "ruff", "check", "."]),
        ("pytest", [py, "-m", "pytest", "-q"]),
        ("secretos", [py, str(Path(__file__).with_name("escanear_secretos.py"))]),
    ]
    if "--mypy" in sys.argv:
        pasos.insert(1, ("mypy", [py, "-m", "mypy", "src"]))

    resultados = [_ejecutar(nombre, comando) for nombre, comando in pasos]

    print("\n" + "=" * 40)
    print("RESUMEN DE VERIFICACIÓN")
    for nombre, estado in resultados:
        print(f"  {nombre:<10} {estado}")
    print("=" * 40)

    if any(estado == "FALLA" for _, estado in resultados):
        print("Hay fallas: corrígelas antes de dar el trabajo por terminado.")
        return 1
    if any(estado == "OMITIDO" for _, estado in resultados):
        print("Hay pasos omitidos: no se puede afirmar que todo pasa.")
        return 2
    print("Todo en verde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
