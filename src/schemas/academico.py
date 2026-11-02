"""Contratos cerrados de las demostraciones académicas, sin datos de clientes."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EntradaAcademica(BaseModel):
    """Solo un fixture conocido; no acepta mensajes ni credenciales."""

    model_config = ConfigDict(extra="forbid")
    escenario: Literal["revision_sintetica"] = "revision_sintetica"


class SalidaAcademica(BaseModel):
    """Resultado sin efectos comerciales."""

    sintetico: Literal[True] = True
    requiere_revision: Literal[True] = True
    efecto_comercial: Literal[False] = False


class PasoMock(BaseModel):
    """Respuesta estructurada consumida por el adaptador local."""

    herramienta: str = ""
    argumentos: dict = Field(default_factory=dict)
    contenido: str = ""
