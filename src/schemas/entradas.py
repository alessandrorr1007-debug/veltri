"""Entradas estructuradas; validar texto no reemplaza el filtro de seguridad futuro."""

from typing import Annotated, Self

from pydantic import Field, model_validator

from src.schemas.base import Canal, Centimos, Contrato, Positivo, Seleccion, Texto


class ConsultaRequest(Contrato):
    """Consulta con tenant explícito; mensaje excluido de repr."""

    mensaje: Texto = Field(repr=False)
    canal: Canal
    tenant_id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class CotizacionRequest(Contrato):
    """Selección explícita con máximo opcional en céntimos de PEN."""

    seleccion: Seleccion
    maximo_centimos: Centimos | None = None


class ArmadoRequest(Contrato):
    """Rango numérico, sin interpretar frases ni asumir un máximo abierto."""

    minimo_centimos: Centimos = 0
    maximo_centimos: Centimos | None = None
    solo_rtx: bool = False

    @model_validator(mode="after")
    def rango_valido(self) -> Self:
        if self.maximo_centimos is not None and self.minimo_centimos > self.maximo_centimos:
            raise ValueError("Rango de presupuesto invertido")
        return self


class ComparacionPagoRequest(Contrato):
    """Importes declarados; no incluye comprobantes ni credenciales bancarias."""

    total_centimos: Positivo
    pagado_centimos: Centimos
    moneda: Annotated[str, Field(pattern=r"^[A-Z]{3}$")] = "PEN"


class PedidoDemoRequest(Contrato):
    """Solo alias sintético, nunca identidad personal real."""

    cliente: Annotated[str, Field(pattern=r"^demo_[a-z]{1,32}$")] = Field(repr=False)
    seleccion: Seleccion
    canal: Canal
