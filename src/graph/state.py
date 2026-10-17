"""Estado interno sin mensaje libre, historial conversacional ni checkpoints."""

from typing import Literal

from pydantic import Field

from src.schemas.agentes import Accion, EstadoBorrador, PlanModelo, ResultadoInventario
from src.schemas.base import SKU, Centimos, Contrato, HashPedido
from src.schemas.consulta import ConsultaResponse
from src.schemas.decision import ResultadoDecision, SolicitudDecision
from src.schemas.flujo import CitaRecuperada, Parametros, ResultadoFlujo
from src.schemas.hitl import Tenant
from src.schemas.resultados import (
    ResultadoCotizacion,
    ResultadoPago,
    ResultadoPedido,
    ResultadoTecnico,
)


class EstadoFlujo(Contrato):
    """Datos de demo y rutas tipadas; no acepta claves de texto arbitrarias."""

    tenant_id: Tenant
    plan: PlanModelo
    parametros: Parametros | None
    ruta: Accion | Literal["decidir"] = "informacion"
    solicitud_decision: SolicitudDecision | None = None
    decision: ResultadoDecision | None = None
    payload: (
        ResultadoCotizacion
        | ResultadoTecnico
        | ResultadoInventario
        | ResultadoPago
        | ResultadoPedido
        | None
    ) = None
    respuesta: ConsultaResponse | None = None
    revision_id: HashPedido | None = None
    alternativas: dict[SKU, list[SKU]] = Field(default_factory=dict)
    minimo_catalogo_centimos: Centimos | None = None
    seguimiento: EstadoBorrador | None = None
    citas: list[CitaRecuperada] = Field(default_factory=list)
    salida: ResultadoFlujo | None = None
