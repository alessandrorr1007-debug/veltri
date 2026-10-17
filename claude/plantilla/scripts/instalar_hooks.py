"""Instala el pre-commit en la raíz exacta del proyecto; conserva hooks ajenos."""
import shlex
import stat
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAIZ = BASE / "plantilla" if (BASE / "plantilla").is_dir() else BASE

def main():
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=RAIZ,
                            capture_output=True, text=True)
    if result.returncode or Path(result.stdout.strip()).resolve() != RAIZ.resolve():
        print("Inicializa Git en la raíz del proyecto antes de instalar el hook.")
        return 1
    result = subprocess.run(["git", "rev-parse", "--git-path", "hooks/pre-commit"],
                            cwd=RAIZ, capture_output=True, text=True, check=True)
    target = Path(result.stdout.strip())
    if not target.is_absolute():
        target = RAIZ / target
    marker = "# Hook Veltri administrado"
    if target.exists() and marker not in target.read_text(encoding="utf-8"):
        print("Existe un pre-commit ajeno; se conserva. Integra los controles manualmente.")
        return 1
    folder = Path(__file__).resolve().parent
    lines = ["#!/bin/sh", marker]
    for script in ("proteger.py", "escanear_secretos.py"):
        lines.append(shlex.quote(sys.executable.replace("\\", "/")) + " " +
                     shlex.quote((folder / script).as_posix()) + " || exit 1")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    target.chmod(target.stat().st_mode | stat.S_IXUSR)
    print(f"Hook instalado: {target}. Reinstálalo si mueves el proyecto o Python.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
