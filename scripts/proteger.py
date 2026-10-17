"""Bloquea commits que modifiquen archivos protegidos sin autorización explícita.

Archivos protegidos: umbrales de decisión y línea base de evaluación.
Para autorizar un cambio a propósito, ejecuta el commit con la variable
VELTRI_AUTORIZO_CAMBIO_PROTEGIDO=1 (por ejemplo, en PowerShell:
    $env:VELTRI_AUTORIZO_CAMBIO_PROTEGIDO="1"; git commit -m "mensaje"
).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAIZ = BASE / "plantilla" if (BASE / "plantilla").is_dir() else BASE

PROTEGIDOS = {
    "src/core/umbrales.py",
    "evals/linea_base.json",
}


def archivos_modificados_en_stage() -> set[str]:
    """Archivos en stage que fueron modificados, renombrados o eliminados (no los nuevos)."""
    resultado = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=MDT", "--no-renames"],
        cwd=RAIZ, capture_output=True, text=True, check=True,
    )
    return {linea.strip() for linea in resultado.stdout.splitlines() if linea.strip()}


def main() -> int:
    tocados = archivos_modificados_en_stage() & PROTEGIDOS
    if not tocados:
        return 0
    if os.environ.get("VELTRI_AUTORIZO_CAMBIO_PROTEGIDO") == "1":
        print("Cambio a archivos protegidos AUTORIZADO:", ", ".join(sorted(tocados)))
        return 0
    print("COMMIT BLOQUEADO: modificaste archivos protegidos:")
    for ruta in sorted(tocados):
        print(" -", ruta)
    print("Los umbrales y la línea base no se cambian sin autorización explícita.")
    print("Si fue a propósito, define VELTRI_AUTORIZO_CAMBIO_PROTEGIDO=1 y repite el commit.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
