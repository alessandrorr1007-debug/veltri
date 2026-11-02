"""Verificación local: estructura, dependencias, Ruff, pytest y secretos.

Uso:
    python scripts/verificar.py            # verificación estándar
    python scripts/verificar.py --mypy     # agrega tipado estricto con mypy
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAIZ = BASE / "plantilla" if (BASE / "plantilla").is_dir() else BASE


def comprobar_estructura(raiz: Path = RAIZ) -> int:
    """Compila sin escribir pyc ni ejecutar módulos y comprueba imports internos."""
    archivos = [
        p
        for carpeta in ("src", "scripts", "tests", "evals", "docs/entrega-semana10")
        for p in (raiz / carpeta).rglob("*.py")
        if "__pycache__" not in p.parts
    ]
    errores = []
    for archivo in archivos:
        try:
            texto = archivo.read_text(encoding="utf-8-sig")
            compile(texto, str(archivo), "exec")
            arbol = ast.parse(texto)
        except (SyntaxError, UnicodeError, OSError):
            errores.append(str(archivo.relative_to(raiz)))
            continue
        for nodo in ast.walk(arbol):
            nombres = (
                [nodo.module]
                if isinstance(nodo, ast.ImportFrom) and nodo.module
                else [a.name for a in nodo.names]
                if isinstance(nodo, ast.Import)
                else []
            )
            for nombre in nombres:
                if nombre.startswith(("src.", "scripts.")):
                    ruta = raiz.joinpath(*nombre.split("."))
                    if (
                        not ruta.with_suffix(".py").is_file()
                        and not (ruta / "__init__.py").is_file()
                    ):
                        errores.append(f"{archivo.relative_to(raiz)}: {nombre}")
    for nombre in (
        "frontend/index.html",
        "data/catalogo.json",
        "data/compatibilidad.json",
        "data/politicas.md",
        "docs/bpmn_as_is.bpmn",
        "docs/bpmn_to_be.bpmn",
        "docs/entrega-semana10/generar_informe.py",
        "docs/entrega-semana10/Veltri_Semana10_Informe_Academico.docx",
        "docs/evidencias/semana10-fase43/ejecucion-unica.json",
    ):
        if not (raiz / nombre).is_file():
            errores.append(nombre)
    print(f"\n[estructura]\n{len(archivos)} archivos Python revisados sin ejecutar imports.")
    for error in errores:
        print("Referencia o sintaxis inválida:", error)
    return 1 if errores else 0


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
        ("dependencias", [py, "-m", "pip", "check"]),
        ("ruff", [py, "-m", "ruff", "check", "."]),
        ("pytest", [py, "-m", "pytest", "-q"]),
        ("secretos", [py, str(Path(__file__).with_name("escanear_secretos.py"))]),
    ]
    if "--mypy" in sys.argv:
        pasos.insert(1, ("mypy", [py, "-m", "mypy", "src"]))

    resultados = [("estructura", "OK" if comprobar_estructura() == 0 else "FALLA")]
    resultados.extend(_ejecutar(nombre, comando) for nombre, comando in pasos)

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
