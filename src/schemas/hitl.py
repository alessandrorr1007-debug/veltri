"""Contratos de una bandeja de revisión de demo, sin autorización productiva."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.core.decision import decide
from src.schemas.base import Contrato, Falso, HashPedido
from src.schemas.decision import ResultadoDecision, SolicitudDecision

Tenant = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class ResolucionRevision(Contrato):
    """Operador sintético y motivos enumerados; no admite comentarios con PII."""

    accion: Literal["aprobar_demo", "rechazar", "solicitar_correccion"]
    revisor: Annotated[str, Field(pattern=r"^demo_[a-z]{1,32}$")] = Field(repr=False)
    motivo: Literal["informacion_verificada", "revision_rechazada", "requiere_correccion"]

    @model_validator(mode="after")
    def motivo_corresponde(self) -> Self:
        motivos = {"aprobar_demo": "informacion_verificada", "rechazar": "revision_rechazada",
                   "solicitar_correccion": "requiere_correccion"}
        if self.motivo != motivos[self.accion]:
            raise ValueError("Motivo incompatible con la resolución")
        return self


class Revision(Contrato):
    """Solicitud y evidencia conservadas como instantánea para revisión local."""

    id: HashPedido
    tenant_id: Tenant
    solicitud: SolicitudDecision
    decision: ResultadoDecision
    estado: Literal["pendiente", "escalada", "aprobada_demo", "rechazada", "correccion_solicitada"]
    resolucion: ResolucionRevision | None = None
    accion_ejecutada: Falso = False

    @model_validator(mode="after")
    def estado_coherente(self) -> Self:
        if self.decision != decide(self.solicitud):
            raise ValueError("La decisión no corresponde a la instantánea de evidencia")
        if self.decision.destino == "ejecutar":
            raise ValueError("Una ruta automática no se encola como revisión")
        if self.resolucion is None:
            esperado = "escalada" if self.decision.destino == "escalar" else "pendiente"
        else:
            esperado = {"aprobar_demo": "aprobada_demo", "rechazar": "rechazada",
                        "solicitar_correccion": "correccion_solicitada"}[self.resolucion.accion]
            if self.resolucion.accion == "aprobar_demo" and (
                    self.decision.bloqueos or self.decision.destino == "escalar"):
                raise ValueError("No se pueden aprobar bloqueos ni escalados sin nueva evidencia")
        if self.estado != esperado:
            raise ValueError("Estado de revisión incompatible")
        return self


class ResultadoEncolado(Contrato):
    """La misma evidencia produce una única revisión por tenant."""

    duplicado: bool
    revision: Revision
