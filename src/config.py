"""Configuración local: mock por defecto, secretos excluidos de representaciones."""

import os
from pathlib import Path
from typing import Mapping, Self

from dotenv import dotenv_values
from pydantic import Field, SecretStr, model_validator

from src.schemas.base import Contrato

RAIZ = Path(__file__).resolve().parent.parent


class Configuracion(Contrato):
    """Sin modelo fijo ni activación de red por defecto."""

    usar_mock: bool = True
    proveedor: str = "gemini"
    modelo: str = Field(default="", pattern=r"^[A-Za-z0-9._-]*$")
    clave: SecretStr = Field(default_factory=lambda: SecretStr(""), repr=False, exclude=True)

    @model_validator(mode="after")
    def proveedor_valido(self) -> Self:
        if self.proveedor != "gemini":
            raise ValueError("Proveedor no admitido")
        if not self.usar_mock and (not self.modelo or not self.clave.get_secret_value()):
            raise ValueError("El modo real requiere modelo y clave configurados")
        return self


def cargar_configuracion(
    ruta: Path = RAIZ / ".env", entorno: Mapping[str, str] | None = None
) -> Configuracion:
    """Entorno del proceso prevalece sobre .env; no imprime valores de configuración."""
    valores = dict(dotenv_values(ruta, interpolate=False)) if ruta.is_file() else {}
    valores.update(os.environ if entorno is None else entorno)
    modo = valores.get("USE_MOCK_LLM", "1")
    if modo not in ("0", "1"):
        raise ValueError("USE_MOCK_LLM debe ser 0 o 1")
    return Configuracion(
        usar_mock=modo == "1",
        proveedor=valores.get("LLM_PROVIDER", "gemini"),
        modelo=valores.get("LLM_MODEL", "") or "",
        clave=SecretStr(valores.get("GOOGLE_API_KEY", "") or ""),
    )
