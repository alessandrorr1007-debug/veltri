"""Base común de los ocho agentes, con planes y errores estructurados."""

import json
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ValidationError

from src.config import Configuracion
from src.core.llm import get_llm
from src.core.seguridad import EntradaBloqueada, validar_entrada_modelo
from src.schemas.agentes import Accion, PlanModelo, SalidaAgente

T = TypeVar("T")


class ErrorAgente(RuntimeError):
    """Expone un código fijo; nunca una excepción cruda del modelo o solicitud."""


class BaseAgent:
    """Cada instancia obtiene su modelo exclusivamente por la fábrica."""

    id: str
    accion: Accion | None = None
    prompt: str

    def __init__(
        self,
        *,
        configuracion: Configuracion | None = None,
        respuestas: list[dict[str, Any]] | None = None,
    ) -> None:
        self._llm = get_llm(configuracion=configuracion, respuestas=respuestas)

    def _entrada(self, entrada: BaseModel, esquema: type[BaseModel]) -> BaseModel:
        try:
            return esquema.model_validate(entrada.model_dump())
        except (ValidationError, AttributeError):
            raise ErrorAgente("entrada_agente_invalida") from None

    def _plan(self, datos: dict[str, Any]) -> PlanModelo:
        try:
            validar_entrada_modelo(json.dumps(datos, ensure_ascii=False))
            plan = self._llm.generar(self.prompt, datos, PlanModelo)
        except EntradaBloqueada:
            raise ErrorAgente("entrada_bloqueada") from None
        if self.accion is not None and plan.accion != self.accion:
            raise ErrorAgente("plan_fuera_de_dominio")
        return plan

    def _ejecutar(self, herramienta: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Mantiene errores de parámetros fuera de las salidas públicas del agente."""
        try:
            return herramienta(*args, **kwargs)
        except (ValueError, ValidationError):
            raise ErrorAgente("parametros_negocio_invalidos") from None

    def _salida(
        self, tenant: str, plan: PlanModelo, resultado: T, esquema: type[T]
    ) -> SalidaAgente[T]:
        return SalidaAgente[esquema](
            agente=self.id,
            tenant_id=tenant,
            plan=plan,
            origen_puntuacion=self._llm.origen_puntuacion,
            resultado=resultado,
        )
