"""A3: cotización calculada por herramientas sobre selección explícita."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import EntradaCotizacion, SalidaAgente
from src.schemas.resultados import ResultadoCotizacion
from src.tools.catalogo import Catalogo
from src.tools.cotizacion import cotizar


class A3Cotizacion(BaseAgent):
    """No acepta totales sugeridos por un modelo."""

    id = "A3"
    accion = "cotizar"
    prompt = prompt_plan(
        accion=accion,
        rol="A3 · D1. Planifica una cotización sobre una selección explícita.",
        contexto="La selección y cantidades vienen del llamador; el catálogo es sintético.",
        herramientas="El código usa cotizar para importes, stock y validación técnica.",
        proceso="Emite cotizar; el cálculo de líneas y la revisión de bloqueos quedan en código.",
        limites="No fijes precios, descuentos, IGV, cantidades ni ajustes a la selección.",
        bloqueo="Precio no respaldado, stock insuficiente o incompatibilidad exigen revisión.",
    )

    def run(
        self, entrada: EntradaCotizacion, catalogo: Catalogo
    ) -> SalidaAgente[ResultadoCotizacion]:
        entrada = self._entrada(entrada, EntradaCotizacion)
        plan = self._plan({"tarea": "cotizar", "parametros": "seleccion_estructurada_del_llamador"})
        resultado = ResultadoCotizacion.model_validate(
            self._ejecutar(cotizar, catalogo, **entrada.solicitud.model_dump())
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoCotizacion)
