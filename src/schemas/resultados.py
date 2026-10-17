"""Contratos de salida para herramientas de demo, con coherencia entre campos."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.schemas.base import (
    SKU,
    Centimos,
    Contrato,
    Falso,
    HashPedido,
    Motivo,
    Positivo,
    Seleccion,
    Texto,
    Verdadero,
)
from src.tools.montos import subtotal_centimos, total_centimos


class LineaCotizacion(Contrato):
    """Una línea con importes calculados y referencia al SKU de origen."""

    sku: SKU
    cantidad: Positivo
    precio_unitario_centimos: Positivo
    subtotal_centimos: Positivo
    fuente: Annotated[str, Field(pattern=r"^data/catalogo\.json#[A-Z0-9-]+$")]

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        if self.fuente != "data/catalogo.json#" + self.sku:
            raise ValueError("La fuente no corresponde al SKU")
        if self.subtotal_centimos != subtotal_centimos(
                self.precio_unitario_centimos, self.cantidad):
            raise ValueError("Subtotal inconsistente")
        return self


class FaltanteStock(Contrato):
    """Faltante comprobado para una cantidad explícita."""

    sku: SKU
    solicitado: Positivo
    disponible: Centimos
    motivo: Literal["stock_insuficiente"]

    @model_validator(mode="after")
    def faltante_real(self) -> Self:
        if self.solicitado <= self.disponible:
            raise ValueError("El faltante debe exceder el stock")
        return self


class ResultadoStock(Contrato):
    """Stock disponible y revisión obligatoria cuando hay faltantes."""

    disponible: bool
    hitl_requerido: bool
    faltantes: list[FaltanteStock]
    fuente: Literal["data/catalogo.json"]

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        if self.disponible != (not self.faltantes) or self.hitl_requerido != bool(self.faltantes):
            raise ValueError("Estado de stock inconsistente")
        skus = [f.sku for f in self.faltantes]
        if len(skus) != len(set(skus)):
            raise ValueError("Faltantes duplicados")
        return self


class ResultadoTecnico(Contrato):
    """Compatibilidad de datos separada de aprobación técnica real."""

    sin_conflictos_datos: bool
    aprobado_tecnicamente: Falso
    hitl_requerido: Verdadero
    conflictos: list[Motivo]
    pendientes: list[Motivo]
    potencia_estimada_w: Positivo | None
    fuente: Literal["data/compatibilidad.json"]

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        if self.sin_conflictos_datos != (not self.conflictos):
            raise ValueError("Estado técnico inconsistente")
        if self.sin_conflictos_datos and (not self.pendientes or self.potencia_estimada_w is None):
            raise ValueError("La demo compatible requiere pendientes y estimación")
        return self


class ResultadoCotizacion(Contrato):
    """Simulación de cotización; nunca concede autorización comercial."""

    moneda: Literal["PEN"]
    naturaleza: Literal["demostracion_sintetica"]
    lineas: Annotated[list[LineaCotizacion], Field(min_length=1, max_length=90)]
    total_centimos: Positivo
    sobre_presupuesto: bool
    stock: ResultadoStock
    tecnico: ResultadoTecnico
    hitl_requerido: Verdadero
    genera_proforma: Falso
    bloqueos: list[Motivo]
    aviso: Texto

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        skus = [linea.sku for linea in self.lineas]
        if len(skus) != len(set(skus)):
            raise ValueError("Líneas duplicadas")
        if self.total_centimos != total_centimos(
                [linea.subtotal_centimos for linea in self.lineas]):
            raise ValueError("Total inconsistente")
        esperados = set(self.tecnico.conflictos)
        if self.sobre_presupuesto:
            esperados.add("sobre_presupuesto")
        if not self.stock.disponible:
            esperados.add("stock_insuficiente")
        if set(self.bloqueos) != esperados or len(set(self.bloqueos)) != len(self.bloqueos):
            raise ValueError("Bloqueos no corresponden a los resultados")
        cantidades = {linea.sku: linea.cantidad for linea in self.lineas}
        if any(cantidades.get(f.sku) != f.solicitado for f in self.stock.faltantes):
            raise ValueError("Faltante ajeno a la cotización")
        return self


class ResultadoArmado(Contrato):
    """Propuesta dentro de rango o ausencia explícita de solución."""

    estado: Literal["propuesta_demo", "sin_configuracion_en_rango"]
    cotizacion: ResultadoCotizacion | None
    minimo_catalogo_centimos: Positivo | None
    hitl_requerido: Verdadero
    criterio: Literal["menor_total", "mayor_total_en_rango"] | None = None

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        if self.estado == "propuesta_demo":
            if (self.cotizacion is None or self.criterio is None
                    or self.minimo_catalogo_centimos is None):
                raise ValueError("Propuesta incompleta")
            if self.cotizacion.bloqueos:
                raise ValueError("El armador no puede proponer una configuración bloqueada")
            if self.cotizacion.total_centimos < self.minimo_catalogo_centimos:
                raise ValueError("Propuesta por debajo del mínimo del catálogo")
        elif self.cotizacion is not None or self.criterio is not None:
            raise ValueError("Ausencia de solución no puede incluir cotización ni criterio")
        return self


class ResultadoPago(Contrato):
    """Comparación de importes, aún sin conciliación bancaria."""

    montos_coinciden: bool
    diferencia_centimos: int | None
    estado: Literal["no_conciliado"]
    hitl_requerido: Verdadero
    motivos: Annotated[list[Motivo], Field(min_length=1)]

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        if self.montos_coinciden != (self.diferencia_centimos == 0):
            raise ValueError("Coincidencia de pago inconsistente")
        esperados = {"falta_evidencia_bancaria_autorizada"}
        if not self.montos_coinciden:
            esperados.add("pago_discrepante")
        if set(self.motivos) != esperados or len(self.motivos) != len(esperados):
            raise ValueError("Motivos de pago inconsistentes")
        return self


class BorradorPedido(Contrato):
    """El contrato impide representar un borrador como pedido confirmado."""

    clave: HashPedido
    estado: Literal["borrador_demo"]
    seleccion: Seleccion
    hitl_requerido: Verdadero


class ResultadoPedido(Contrato):
    """Resultado idempotente del registro en memoria."""

    duplicado: bool
    registros_creados: Annotated[int, Field(ge=0, le=1)]
    pedido: BorradorPedido

    @model_validator(mode="after")
    def coherencia(self) -> Self:
        if self.registros_creados != (0 if self.duplicado else 1):
            raise ValueError("Cantidad de registros incompatible con duplicado")
        return self
