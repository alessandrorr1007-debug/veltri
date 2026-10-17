"""Contratos de decisión sobre evidencia tipada, sin interpretar texto libre."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.core.criterios import Destino, clasificar
from src.schemas.base import Contrato, Falso, Fuente, HashPedido, Motivo
from src.schemas.resultados import (
    ResultadoCotizacion,
    ResultadoPago,
    ResultadoPedido,
    ResultadoStock,
    ResultadoTecnico,
)

Opcion = Literal["informar", "consultar_stock", "cotizar", "validar_compatibilidad",
                 "comparar_pago", "registrar_borrador"]
Puntaje = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


class EvidenciaInformacion(Contrato):
    """Fuentes permitidas para una consulta informativa, sin autorización comercial."""

    tipo: Literal["informacion"]
    fuentes: Annotated[list[Fuente], Field(min_length=1)]

    @model_validator(mode="after")
    def fuentes_unicas(self) -> Self:
        if len(set(self.fuentes)) != len(self.fuentes):
            raise ValueError("Fuentes duplicadas")
        return self


class EvidenciaStock(Contrato):
    """Stock comprobado por la herramienta, no una estimación del modelo."""

    tipo: Literal["stock"]
    resultado: ResultadoStock


class EvidenciaCotizacion(Contrato):
    """Simulación de cotización y sus impedimentos técnicos y de stock."""

    tipo: Literal["cotizacion"]
    resultado: ResultadoCotizacion


class EvidenciaTecnica(Contrato):
    """Restricciones técnicas y evidencia de fabricante pendiente."""

    tipo: Literal["tecnico"]
    resultado: ResultadoTecnico


class EvidenciaPago(Contrato):
    """Comparación de importes que no acredita un pago bancario."""

    tipo: Literal["pago"]
    resultado: ResultadoPago


class EvidenciaPedido(Contrato):
    """Un borrador nunca equivale a un pedido confirmado."""

    tipo: Literal["pedido"]
    resultado: ResultadoPedido


Evidencia = Annotated[EvidenciaInformacion | EvidenciaStock | EvidenciaCotizacion
                      | EvidenciaTecnica | EvidenciaPago | EvidenciaPedido,
                      Field(discriminator="tipo")]


class SolicitudDecision(Contrato):
    """Puntajes explícitamente no calibrados y evidencia acorde a la opción."""

    opcion: Opcion
    p: Puntaje
    c: Puntaje
    origen_puntuacion: Literal["prueba_no_calibrada"]
    evidencia: Evidencia

    @model_validator(mode="after")
    def evidencia_corresponde(self) -> Self:
        tipos = {"informar": "informacion", "consultar_stock": "stock",
                 "cotizar": "cotizacion", "validar_compatibilidad": "tecnico",
                 "comparar_pago": "pago", "registrar_borrador": "pedido"}
        if self.evidencia.tipo != tipos[self.opcion]:
            raise ValueError("Evidencia incompatible con la opción")
        return self


class ResultadoDecision(Contrato):
    """Destino verificable: una ruta ejecutar todavía no ejecuta herramientas."""

    opcion: Opcion
    p: Puntaje
    c: Puntaje
    origen_puntuacion: Literal["prueba_no_calibrada"]
    destino: Destino
    hitl_requerido: bool
    bloqueos: list[Motivo]
    motivos: Annotated[list[Motivo], Field(min_length=1)]
    fuentes: Annotated[list[Fuente], Field(min_length=1)]
    hash_evidencia: HashPedido
    accion_ejecutada: Falso = False

    @model_validator(mode="after")
    def ruta_coherente(self) -> Self:
        if self.destino != clasificar(self.p, bool(self.bloqueos)):
            raise ValueError("Destino incompatible con puntaje y bloqueos")
        if self.hitl_requerido != (self.destino != "ejecutar"):
            raise ValueError("Revisión incompatible con el destino")
        for valores in (self.bloqueos, self.motivos, self.fuentes):
            if len(valores) != len(set(valores)):
                raise ValueError("Valores duplicados en el resultado")
        if not set(self.bloqueos) <= set(self.motivos):
            raise ValueError("La decisión omite un bloqueo")
        return self
