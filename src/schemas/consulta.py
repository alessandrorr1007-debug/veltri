"""Contrato único de respuesta para la futura API; no implementa endpoints."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.schemas.base import Contrato, Falso, Fuente, Motivo, Texto
from src.schemas.resultados import (
    ResultadoCotizacion,
    ResultadoPago,
    ResultadoPedido,
    ResultadoStock,
    ResultadoTecnico,
)


class ConsultaResponse(Contrato):
    """Sobre JSON de demostración con estados explícitos y bloqueos coherentes."""

    version_contrato: Literal["1.0-demo"] = "1.0-demo"
    naturaleza: Literal["demostracion_sintetica"] = "demostracion_sintetica"
    status: Literal["completado", "revision_humana", "bloqueado", "error"]
    intencion: Literal["cotizacion", "compatibilidad", "stock", "pago", "pedido",
                       "informacion", "desconocida"]
    mensaje: Texto = Field(repr=False)
    hitl_requerido: bool
    motivos: list[Motivo] = Field(default_factory=list)
    fuentes: list[Fuente] = Field(default_factory=list)
    genera_proforma: Falso = False
    aprobado_tecnicamente: Falso = False
    archivado_en_dlq: bool = False
    cotizacion: ResultadoCotizacion | None = None
    tecnico: ResultadoTecnico | None = None
    stock: ResultadoStock | None = None
    pago: ResultadoPago | None = None
    pedido: ResultadoPedido | None = None

    @model_validator(mode="after")
    def estados_coherentes(self) -> Self:
        payloads = [self.cotizacion, self.tecnico, self.stock, self.pago, self.pedido]
        if self.status == "completado" and (self.hitl_requerido or self.motivos):
            raise ValueError("Un resultado pendiente no puede declararse completado")
        if self.status == "revision_humana" and (not self.hitl_requerido or not self.motivos):
            raise ValueError("La revisión debe tener flag y motivos")
        if self.status in ("error", "bloqueado"):
            if any(p is not None for p in payloads) or not self.motivos:
                raise ValueError("Error o bloqueo no admite resultados y requiere motivo")
        if self.archivado_en_dlq and self.status != "bloqueado":
            raise ValueError("DLQ solo puede declararse en estado bloqueado")
        if len(self.fuentes) != len(set(self.fuentes)):
            raise ValueError("Fuentes duplicadas")
        if len(self.motivos) != len(set(self.motivos)):
            raise ValueError("Motivos duplicados")
        if self.status not in ("error", "bloqueado"):
            if not self.fuentes:
                raise ValueError("Una respuesta requiere fuentes de datos")
            for campo, intencion in [("cotizacion", "cotizacion"),
                                      ("tecnico", "compatibilidad"), ("stock", "stock"),
                                      ("pago", "pago"), ("pedido", "pedido")]:
                if getattr(self, campo) is not None and self.intencion != intencion:
                    raise ValueError("El resultado no corresponde a la intención")
            requerido = {"cotizacion": self.cotizacion, "compatibilidad": self.tecnico,
                         "stock": self.stock, "pago": self.pago, "pedido": self.pedido}
            if self.intencion in requerido and requerido[self.intencion] is None:
                raise ValueError("Falta resultado para la intención declarada")
            if self.intencion == "desconocida" and self.status == "completado":
                raise ValueError("Una intención desconocida no puede estar completada")
        for payload in payloads:
            if payload is None:
                continue
            requiere = (payload.pedido.hitl_requerido if isinstance(payload, ResultadoPedido)
                        else payload.hitl_requerido)
            if requiere and not self.hitl_requerido:
                raise ValueError("La respuesta no puede ocultar la revisión de su resultado")
        necesarias = set()
        if self.cotizacion is not None:
            necesarias.update(["data/catalogo.json", "data/compatibilidad.json"])
            razones = set(self.cotizacion.bloqueos) | set(self.cotizacion.tecnico.pendientes)
            if not razones <= set(self.motivos):
                raise ValueError("La respuesta omite bloqueos o pendientes de cotización")
        if self.tecnico is not None:
            necesarias.add("data/compatibilidad.json")
            if not set(self.tecnico.conflictos + self.tecnico.pendientes) <= set(self.motivos):
                raise ValueError("La respuesta omite motivos técnicos")
        if self.stock is not None:
            necesarias.add("data/catalogo.json")
            if self.stock.faltantes and "stock_insuficiente" not in self.motivos:
                raise ValueError("La respuesta omite el bloqueo de stock")
        if self.pago is not None:
            necesarias.add("data/politicas.md")
            if not set(self.pago.motivos) <= set(self.motivos):
                raise ValueError("La respuesta omite motivos del pago")
        if self.pedido is not None:
            necesarias.update(["data/catalogo.json", "data/politicas.md"])
            if "borrador_demo" not in self.motivos:
                raise ValueError("La respuesta debe identificar el borrador")
        if not necesarias <= set(self.fuentes):
            raise ValueError("La respuesta omite las fuentes de su resultado")
        return self


class ErrorValidacion(Contrato):
    """Error publicable sin texto de entrada, valores rechazados ni trazas."""

    codigo: Literal["entrada_invalida"] = "entrada_invalida"
    mensaje: Literal["Revisa los campos de la solicitud."] = "Revisa los campos de la solicitud."
    campos: Annotated[list[Literal["mensaje", "canal", "tenant_id", "seleccion",
                                   "maximo_centimos", "minimo_centimos", "solo_rtx",
                                   "total_centimos", "pagado_centimos", "moneda",
                                   "cliente"]], Field(max_length=11)] = Field(default_factory=list)
