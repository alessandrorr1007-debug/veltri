"""A2: armado determinista de demostración con un plan validado por dominio."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import EntradaArmado, SalidaAgente
from src.schemas.resultados import ResultadoArmado
from src.tools.armador import armar
from src.tools.catalogo import Catalogo


class A2Armado(BaseAgent):
    """El modelo no elige precios ni componentes."""

    id = "A2"
    accion = "armar"
    prompt = prompt_plan(
        accion=accion,
        rol="A2 · D1. Planifica el armado dentro del rango solicitado.",
        contexto="El código recibe un rango explícito; el modelo recibe un marcador de rango.",
        herramientas="El código usa armar con el catálogo y el rango validados.",
        proceso="Identifica la tarea y emite armar; deja selección y validación al código.",
        limites="No propongas componentes, rendimiento ni un rango alternativo.",
        bloqueo="Sin solución, fuera de presupuesto o con evidencia insuficiente, exige revisión.",
    )

    def run(self, entrada: EntradaArmado, catalogo: Catalogo) -> SalidaAgente[ResultadoArmado]:
        entrada = self._entrada(entrada, EntradaArmado)
        plan = self._plan({"tarea": "armar", "parametros": "rango_estructurado_del_llamador"})
        resultado = ResultadoArmado.model_validate(
            self._ejecutar(armar, catalogo, **entrada.solicitud.model_dump())
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoArmado)
