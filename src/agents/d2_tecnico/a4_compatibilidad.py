"""A4: validación técnica sin porcentajes de cuello de botella inventados."""

from src.agents.base import BaseAgent
from src.schemas.agentes import EntradaSeleccion, SalidaAgente
from src.schemas.resultados import ResultadoTecnico
from src.tools.catalogo import Catalogo
from src.tools.hardware import validar_configuracion


class A4Compatibilidad(BaseAgent):
    """La compatibilidad y potencia se verifican exclusivamente en código."""

    id = "A4"
    accion = "compatibilidad"
    prompt = "Planifica solo compatibilidad. Devuelve accion, p y c; no certifiques hardware real."

    def run(self, entrada: EntradaSeleccion, catalogo: Catalogo) -> SalidaAgente[ResultadoTecnico]:
        entrada = self._entrada(entrada, EntradaSeleccion)
        plan = self._plan({"tarea": "compatibilidad"})
        resultado = ResultadoTecnico.model_validate(
            self._ejecutar(validar_configuracion, catalogo, entrada.seleccion)
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoTecnico)
