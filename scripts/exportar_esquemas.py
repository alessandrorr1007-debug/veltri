"""Exporta JSON Schema de los contratos sin generar una API ni datos de clientes."""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.schemas.consulta import ConsultaResponse, ErrorValidacion  # noqa: E402
from src.schemas.decision import ResultadoDecision, SolicitudDecision  # noqa: E402
from src.schemas.entradas import (  # noqa: E402
    ArmadoRequest,
    ComparacionPagoRequest,
    ConsultaRequest,
    CotizacionRequest,
    PedidoDemoRequest,
)
from src.schemas.hitl import (  # noqa: E402
    ResolucionRevision,
    ResultadoEncolado,
    Revision,
)
from src.schemas.resultados import (  # noqa: E402
    ResultadoArmado,
    ResultadoCotizacion,
    ResultadoPago,
    ResultadoPedido,
    ResultadoStock,
    ResultadoTecnico,
)


def main() -> None:
    """Escribe artefactos reproducibles en docs/contratos/."""
    destino = RAIZ / "docs" / "contratos"
    destino.mkdir(exist_ok=True)
    modelos = [ConsultaRequest, ConsultaResponse, CotizacionRequest, ArmadoRequest,
               ComparacionPagoRequest, PedidoDemoRequest, ResultadoCotizacion,
               ResultadoArmado, ResultadoStock, ResultadoTecnico, ResultadoPago,
               ResultadoPedido, ErrorValidacion, SolicitudDecision, ResultadoDecision,
               ResolucionRevision, Revision, ResultadoEncolado]
    for modelo in modelos:
        ruta = destino / f"{modelo.__name__}.schema.json"
        ruta.write_text(json.dumps(modelo.model_json_schema(), indent=2, ensure_ascii=False)
                        + "\n", encoding="utf-8")
    print(f"Exportados {len(modelos)} contratos JSON Schema en docs/contratos/")


if __name__ == "__main__":
    main()
