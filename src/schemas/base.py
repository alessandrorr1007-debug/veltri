"""Tipos comunes estrictos para contratos de demostración, sin acceso al modelo."""

from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def booleano(valor: object) -> bool:
    """Literal bool también debe rechazar enteros 0 y 1."""
    if type(valor) is not bool:
        raise ValueError("Se requiere booleano JSON")
    return valor


class Contrato(BaseModel):
    """Rechaza campos desconocidos y coerciones; no muestra entradas en errores."""

    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True,
                              validate_default=True, frozen=True)


SKU = Annotated[str, Field(pattern=r"^[A-Z0-9]+(?:-[A-Z0-9]+)+$", max_length=80)]
Centimos = Annotated[int, Field(ge=0)]
Positivo = Annotated[int, Field(gt=0)]
Texto = Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
Motivo = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*(?::[A-Za-z0-9_-]+)?$",
                              max_length=160)]
HashPedido = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Canal = Literal["web", "whatsapp"]
Fuente = Literal["data/catalogo.json", "data/compatibilidad.json", "data/politicas.md"]
Verdadero = Annotated[Literal[True], BeforeValidator(booleano)]
Falso = Annotated[Literal[False], BeforeValidator(booleano)]
Seleccion = Annotated[dict[SKU, Positivo], Field(min_length=1, max_length=90)]
