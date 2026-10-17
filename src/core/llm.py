"""Fábrica única de modelos, con mock programado y conector Gemini estructurado."""

from collections import deque
from copy import deepcopy
from threading import Lock
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from src.config import Configuracion, cargar_configuracion
from src.core.seguridad import validar_entrada_modelo

T = TypeVar("T", bound=BaseModel)


class ErrorModelo(RuntimeError):
    """Fallo controlado que no contiene prompt, entrada ni credenciales."""


class Modelo(Protocol):
    """Interfaz mínima común, sin acceso a herramientas o estados de negocio."""

    origen_puntuacion: str

    def generar(self, prompt: str, datos: dict[str, Any], esquema: type[T]) -> T: ...


class MockLLM:
    """Consume fixtures explícitos; no simula comprensión ni usa red."""

    origen_puntuacion = "prueba_no_calibrada"

    def __init__(self, respuestas: list[dict[str, Any]]) -> None:
        self._respuestas = deque(deepcopy(respuestas))
        self._lock = Lock()
        self.llamadas = 0

    def generar(self, prompt: str, datos: dict[str, Any], esquema: type[T]) -> T:
        """Valida cada respuesta como el contrato solicitado, sin guardar entradas."""
        with self._lock:
            self.llamadas += 1
            if not self._respuestas:
                raise ErrorModelo("mock_sin_respuestas")
            respuesta = self._respuestas.popleft()
        try:
            return esquema.model_validate(respuesta)
        except ValidationError:
            raise ErrorModelo("respuesta_modelo_invalida") from None


class GeminiLLM:
    """Conector sin herramientas remotas; el nombre de modelo proviene de .env."""

    origen_puntuacion = "modelo_no_calibrado"

    def __init__(self, configuracion: Configuracion) -> None:
        from google import genai

        self._modelo = configuracion.modelo
        self._cliente = genai.Client(
            api_key=configuracion.clave.get_secret_value(),
            vertexai=False,
            http_options={"timeout": 20000},
        )

    def generar(self, prompt: str, datos: dict[str, Any], esquema: type[T]) -> T:
        """Solicita JSON estricto sin historial remoto y valida antes de usarlo."""
        import json

        validar_entrada_modelo(json.dumps(datos, ensure_ascii=False))
        try:
            interaccion = self._cliente.interactions.create(
                model=self._modelo,
                input=prompt + "\nDATOS_NO_CONFIABLES:\n" + json.dumps(datos, ensure_ascii=False),
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": esquema.model_json_schema(),
                },
                store=False,
            )
            return esquema.model_validate_json(interaccion.output_text)
        except Exception:
            raise ErrorModelo("proveedor_no_disponible_o_respuesta_invalida") from None


def get_llm(
    *, configuracion: Configuracion | None = None, respuestas: list[dict[str, Any]] | None = None
) -> Modelo:
    """Único punto de construcción; crear un cliente no realiza una consulta."""
    config = configuracion if configuracion is not None else cargar_configuracion()
    if config.usar_mock:
        return MockLLM(respuestas if respuestas is not None else [])
    if respuestas is not None:
        raise ValueError("Los fixtures solo se permiten en modo mock")
    return GeminiLLM(config)
