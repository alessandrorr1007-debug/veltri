"""Contratos de agentes de dominio; planes sin cifras de negocio ni texto de ruta."""

from typing import Generic, Literal, Self, TypeVar

from pydantic import model_validator

from src.schemas.base import SKU, Contrato, HashPedido, Seleccion, Verdadero
from src.schemas.decision import Puntaje
from src.schemas.entradas import (
    ArmadoRequest,
    ComparacionPagoRequest,
    CotizacionRequest,
    PedidoDemoRequest,
)
from src.schemas.hitl import Tenant
from src.schemas.resultados import BorradorPedido, ResultadoStock

Accion = Literal[
    "armar",
    "cotizar",
    "compatibilidad",
    "stock",
    "pago",
    "pedido",
    "seguimiento",
    "informacion",
    "desconocida",
]
T = TypeVar("T")


class PlanModelo(Contrato):
    """Solo intención y puntuaciones no calibradas; nunca montos ni autorizaciones."""

    accion: Accion
    p: Puntaje
    c: Puntaje


class SalidaAgente(Contrato, Generic[T]):
    """Sobre interno; no sustituye ConsultaResponse ni ejecuta el grafo."""

    agente: Literal["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]
    tenant_id: Tenant
    plan: PlanModelo
    origen_puntuacion: Literal["prueba_no_calibrada", "modelo_no_calibrado"]
    resultado: T

    @model_validator(mode="after")
    def dominio_coherente(self) -> Self:
        acciones = {
            "A2": "armar",
            "A3": "cotizar",
            "A4": "compatibilidad",
            "A5": "stock",
            "A6": "pago",
            "A7": "pedido",
            "A8": "seguimiento",
        }
        if self.agente in acciones and self.plan.accion != acciones[self.agente]:
            raise ValueError("El plan de salida no corresponde al agente")
        return self


class EntradaSeleccion(Contrato):
    """Selección explícita con tenant del contexto confiable."""

    tenant_id: Tenant
    seleccion: Seleccion


class EntradaArmado(Contrato):
    """Rango sin extracción aritmética por el modelo."""

    tenant_id: Tenant
    solicitud: ArmadoRequest


class EntradaCotizacion(Contrato):
    """Cotización de selección ya validada por el llamador."""

    tenant_id: Tenant
    solicitud: CotizacionRequest


class EntradaPago(Contrato):
    """Importes explícitos, no comprobantes ni texto de un cliente."""

    tenant_id: Tenant
    solicitud: ComparacionPagoRequest


class EntradaPedido(Contrato):
    """Consentimiento explícito solo para crear un borrador sintético."""

    tenant_id: Tenant
    solicitud: PedidoDemoRequest
    confirmar_borrador: Verdadero


class EntradaSeguimiento(Contrato):
    """Una clave de borrador no permite cambiar tenant."""

    tenant_id: Tenant
    clave: HashPedido


class EstadoBorrador(Contrato):
    """Consulta local: no implica pago, despacho ni confirmación."""

    encontrado: bool
    borrador: BorradorPedido | None

    @model_validator(mode="after")
    def estado_coherente(self) -> Self:
        if self.encontrado != (self.borrador is not None):
            raise ValueError("Estado de borrador inconsistente")
        return self


class ResultadoInventario(Contrato):
    """Stock y sugerencias, sin reemplazar productos ni aprobar una PC."""

    stock: ResultadoStock
    alternativas: dict[SKU, list[SKU]]

    @model_validator(mode="after")
    def alternativas_corresponden(self) -> Self:
        faltantes = {f.sku for f in self.stock.faltantes}
        if set(self.alternativas) != faltantes:
            raise ValueError("Las alternativas deben corresponder a los SKUs faltantes")
        for sku, opciones in self.alternativas.items():
            if sku in opciones or len(opciones) != len(set(opciones)):
                raise ValueError("Alternativas duplicadas o iguales al SKU faltante")
        return self
