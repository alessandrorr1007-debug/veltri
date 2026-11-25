"""A4: validación técnica sin porcentajes de cuello de botella inventados."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import EntradaSeleccion, SalidaAgente
from src.schemas.resultados import ResultadoTecnico
from src.tools.catalogo import Catalogo
from src.tools.hardware import validar_configuracion


class A4Compatibilidad(BaseAgent):
    """La compatibilidad y potencia se verifican exclusivamente en código."""

    id = "A4"
    accion = "compatibilidad"
    prompt = prompt_plan(
        accion=accion,
        rol="A4 · D2. Planifica la validación técnica de una configuración.",
        contexto="El código valida la selección explícita frente a reglas de hardware sintético.",
        herramientas="El código usa validar_configuracion con el catálogo.",
        proceso="Emite compatibilidad; deja socket, montaje, conectores y potencia al validador.",
        limites="No certifiques hardware real ni inventes FPS o porcentajes de cuello de botella.",
        bloqueo="Socket incompatible o comprobación inconclusa exigen revisión.",
    )

    def run(self, entrada: EntradaSeleccion, catalogo: Catalogo) -> SalidaAgente[ResultadoTecnico]:
        entrada = self._entrada(entrada, EntradaSeleccion)
        plan = self._plan({"tarea": "compatibilidad"})
        resultado = ResultadoTecnico.model_validate(
            self._ejecutar(validar_configuracion, catalogo, entrada.seleccion)
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoTecnico)
