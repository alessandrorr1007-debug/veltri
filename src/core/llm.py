"""Fábrica única de modelos, con mock programado y conector Gemini estructurado."""

import json
from collections import deque
from copy import deepcopy
from threading import Lock
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from src.config import Configuracion, cargar_configuracion
from src.core.autonomia import (
    LIMITES_COMERCIALES,
    controlar_ejecucion,
    estimar_tokens,
    presupuesto_actual,
)
from src.core.prompts import datos_no_confiables
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
        presupuesto = presupuesto_actual.get()
        entrada = estimar_tokens(prompt + datos_no_confiables(datos)) if presupuesto else 0
        reserva = presupuesto.reservar_modelo(entrada) if presupuesto else 0
        with self._lock:
            self.llamadas += 1
            respuesta = self._respuestas.popleft() if self._respuestas else None
        if presupuesto:
            salida = estimar_tokens(json.dumps(respuesta, ensure_ascii=False)) if respuesta else 0
            presupuesto.liquidar_modelo(entrada, reserva, entrada, salida, "simulados")
        if respuesta is None:
            raise ErrorModelo("mock_sin_respuestas")
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
            # Interactions traduce attempts directamente al número de reintentos.
            http_options={"timeout": 20000, "retry_options": {"attempts": 0}},
        )

    def generar(self, prompt: str, datos: dict[str, Any], esquema: type[T]) -> T:
        """Solicita JSON estricto sin historial remoto y valida antes de usarlo."""
        presupuesto = presupuesto_actual.get()
        if presupuesto is None:
            with controlar_ejecucion(LIMITES_COMERCIALES):
                return self.generar(prompt, datos, esquema)

        validar_entrada_modelo(json.dumps(datos, ensure_ascii=False))
        contenido = datos_no_confiables(datos)
        respuesta = {
            "type": "text", "mime_type": "application/json", "schema": esquema.model_json_schema(),
        }
        # Incluye el esquema y deja margen para el sobre del proveedor.
        entrada = len((prompt + contenido + json.dumps(respuesta)).encode()) + 64
        plazo = presupuesto.segundos_restantes()
        reserva = presupuesto.reservar_modelo(entrada)
        try:
            interaccion = self._cliente.interactions.create(
                model=self._modelo,
                system_instruction=prompt,
                input=contenido,
                response_format=respuesta,
                generation_config={"max_output_tokens": reserva},
                timeout=plazo,
                store=False,
                stream=False,
            )
        except Exception:
            presupuesto.liquidar_modelo(entrada, reserva, entrada, reserva, "estimados")
            raise ErrorModelo("proveedor_no_disponible_o_respuesta_invalida") from None

        texto = getattr(interaccion, "output_text", None)
        uso = getattr(interaccion, "usage", None)
        entrada_real = getattr(uso, "total_input_tokens", None)
        salida_real = getattr(uso, "total_output_tokens", None)
        total_real = getattr(uso, "total_tokens", None)
        entrada_medida = type(entrada_real) is int and entrada_real >= 0
        salida_medida = type(salida_real) is int and salida_real >= 0
        entrada_usada = entrada_real if entrada_medida else entrada
        salida_usada = salida_real if salida_medida else reserva
        otros = 0
        if type(total_real) is int:
            otros = max(0, total_real - entrada_usada - salida_usada)
        presupuesto.liquidar_modelo(
            entrada, reserva, entrada_usada, salida_usada,
            "reales" if entrada_medida else "estimados",
            naturaleza_salida="reales" if salida_medida else "estimados", otros=otros,
        )
        try:
            return esquema.model_validate_json(texto)
        except ValidationError:
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
