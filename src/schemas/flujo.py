"""Entrada tipada del flujo y detalles internos sin alterar ConsultaResponse."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.schemas.agentes import EstadoBorrador
from src.schemas.base import (
    SKU,
    Canal,
    Centimos,
    Contrato,
    Fuente,
    HashPedido,
    Seleccion,
    Texto,
    Verdadero,
)
from src.schemas.consulta import ConsultaResponse
from src.schemas.decision import ResultadoDecision
from src.schemas.entradas import (
    ArmadoRequest,
    ComparacionPagoRequest,
    ConsultaRequest,
    CotizacionRequest,
    PedidoDemoRequest,
)
from src.schemas.hitl import Tenant


class ParametrosArmado(Contrato):
    """Rango explícito en céntimos."""

    tipo: Literal["armar"]
    solicitud: ArmadoRequest


class ParametrosCotizacion(Contrato):
    """Selección explícita del llamador."""

    tipo: Literal["cotizar"]
    solicitud: CotizacionRequest


class ParametrosSeleccion(Contrato):
    """Selección para stock o validación técnica."""

    tipo: Literal["stock", "compatibilidad"]
    seleccion: Seleccion


class ParametrosPago(Contrato):
    """Importes estructurados, sin comprobantes privados."""

    tipo: Literal["pago"]
    solicitud: ComparacionPagoRequest


class ParametrosPedido(Contrato):
    """Consentimiento solo para un borrador sintético."""

    tipo: Literal["pedido"]
    solicitud: PedidoDemoRequest
    confirmar_borrador: Verdadero


class ParametrosSeguimiento(Contrato):
    """Clave de borrador; tenant viene del contexto de consulta."""

    tipo: Literal["seguimiento"]
    clave: HashPedido


class ParametrosInformacion(Contrato):
    """Temas públicos enumerados: no se guarda la consulta libre en el grafo."""

    tipo: Literal["informacion"]
    tema: Literal["politicas", "pagos", "stock", "compatibilidad"]


Parametros = Annotated[
    ParametrosArmado
    | ParametrosCotizacion
    | ParametrosSeleccion
    | ParametrosPago
    | ParametrosPedido
    | ParametrosSeguimiento
    | ParametrosInformacion,
    Field(discriminator="tipo"),
]


class SolicitudFlujo(Contrato):
    """El mensaje queda fuera del estado de LangGraph y de las colas."""

    consulta: ConsultaRequest = Field(repr=False)
    parametros: Parametros | None = None


class SolicitudAPI(Contrato):
    """Petición pública admitida por /consulta.

    Acepta formato plano (mensaje, canal, tenant_id) con parámetros opcionales,
    o formato anidado con objeto consulta.
    """

    mensaje: Texto | None = Field(default=None, repr=False)
    canal: Canal | None = None
    tenant_id: Tenant | None = None
    consulta: ConsultaRequest | None = Field(default=None, repr=False)
    parametros: Parametros | None = None

    @model_validator(mode="after")
    def validar_campos(self) -> Self:
        if self.consulta is None:
            if self.mensaje is None or self.canal is None or self.tenant_id is None:
                raise ValueError("Se requiere 'consulta' o bien ('mensaje', 'canal', 'tenant_id')")
        return self

    def a_solicitud_flujo(self) -> SolicitudFlujo:
        if self.consulta is not None:
            return SolicitudFlujo(consulta=self.consulta, parametros=self.parametros)
        assert self.mensaje is not None and self.canal is not None and self.tenant_id is not None
        return SolicitudFlujo(
            consulta=ConsultaRequest(
                mensaje=self.mensaje,
                canal=self.canal,
                tenant_id=self.tenant_id,
            ),
            parametros=self.parametros,
        )


class CitaRecuperada(Contrato):
    """Solo procedencia, sin fragmentos libres ni mediciones inventadas."""

    fuente: Fuente
    referencia: str
    hash_fuente: HashPedido
    snapshot: HashPedido

    @model_validator(mode="after")
    def referencia_valida(self) -> Self:
        if not self.referencia.startswith(self.fuente + "#"):
            raise ValueError("La referencia no corresponde a la fuente")
        return self


class ResultadoFlujo(Contrato):
    """Respuesta pública y detalles locales para una integración futura."""

    respuesta: ConsultaResponse
    decision: ResultadoDecision | None = None
    revision_id: HashPedido | None = None
    evento_dlq_id: HashPedido | None = None
    alternativas: dict[SKU, list[SKU]] = Field(default_factory=dict)
    minimo_catalogo_centimos: Centimos | None = None
    seguimiento: EstadoBorrador | None = None
    citas: list[CitaRecuperada] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        if self.respuesta.archivado_en_dlq and self.evento_dlq_id is None:
            raise ValueError("No se puede declarar archivo en DLQ sin evento")
        if self.revision_id is not None and (
            self.decision is None or not self.decision.hitl_requerido
        ):
            raise ValueError("Una revisión debe corresponder a una decisión pendiente")
        if (
            self.decision is not None
            and self.decision.hitl_requerido
            and not self.respuesta.hitl_requerido
        ):
            raise ValueError("La respuesta no puede ocultar la decisión de revisión")
        if any(c.fuente not in self.respuesta.fuentes for c in self.citas):
            raise ValueError("Falta una fuente citada en la respuesta")
        return self
