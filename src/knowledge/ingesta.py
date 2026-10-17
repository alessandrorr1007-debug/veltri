"""CLI de ingesta local: requiere tenant explícito; no lee conversaciones."""

import argparse
from pathlib import Path

from src.knowledge.almacen import Almacen
from src.knowledge.documentos import construir_documentos
from src.knowledge.vectorizacion import validar_tenant

RAIZ = Path(__file__).resolve().parents[2]


def main() -> int:
    """Indexa solo las fuentes permitidas, con errores sin valores privados."""
    parser = argparse.ArgumentParser(description="Indexar corpus sintético de Veltri")
    parser.add_argument("--tenant", required=True, help="Identificador técnico explícito")
    parser.add_argument("--ruta", type=Path, default=RAIZ / "chroma_db")
    args = parser.parse_args()
    try:
        validar_tenant(args.tenant)
        documentos = construir_documentos(args.tenant)
        resultado = Almacen(args.ruta).reemplazar(args.tenant, documentos)
    except (ValueError, OSError):
        print("Ingesta rechazada: revisa fuentes, privacidad y configuración local.")
        return 1
    print(f"Ingesta de demostración completada: {resultado['fragmentos']} fragmentos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
