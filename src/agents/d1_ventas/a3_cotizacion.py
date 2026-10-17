"""A3: cotización calculada por herramientas sobre selección explícita."""

from src.agents.base import BaseAgent
from src.schemas.agentes import EntradaCotizacion, SalidaAgente
from src.schemas.resultados import ResultadoCotizacion
from src.tools.catalogo import Catalogo
from src.tools.cotizacion import cotizar


class A3Cotizacion(BaseAgent):
    """No acepta totales sugeridos por un modelo."""

    id = "A3"
    accion = "cotizar"
    prompt = "Planifica solo cotizar. Devuelve accion, p y c; no inventes importes ni stock."

    def run(
        self, entrada: EntradaCotizacion, catalogo: Catalogo
    ) -> SalidaAgente[ResultadoCotizacion]:
        entrada = self._entrada(entrada, EntradaCotizacion)
        plan = self._plan({"tarea": "cotizar", "parametros": "seleccion_estructurada_del_llamador"})
        resultado = ResultadoCotizacion.model_validate(
            self._ejecutar(cotizar, catalogo, **entrada.solicitud.model_dump())
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoCotizacion)
