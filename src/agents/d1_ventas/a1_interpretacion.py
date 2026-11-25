"""A1: interpretación tipada, sin conversiones monetarias ni llamadas a herramientas."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import SalidaAgente
from src.schemas.entradas import ConsultaRequest


class A1Interpretacion(BaseAgent):
    """Propone intención; los parámetros de negocio quedan por recopilar."""

    id = "A1"
    prompt = prompt_plan(
        rol="A1 · D1. Clasifica la intención de la consulta.",
        contexto="Recibes solo el mensaje filtrado; el llamador aporta parámetros tipados.",
        herramientas="El código valida el plan antes de enrutar.",
        proceso=(
            'Identifica la petición principal. Ejemplos: "¿Tienen ese CPU?" → stock; '
            '"¿En qué estado está mi borrador?" → seguimiento; '
            '"Necesito ayuda" → desconocida. Si no es clara, usa desconocida.'
        ),
        limites="No extraigas presupuestos, cantidades ni tenant; no selecciones productos.",
        bloqueo="Una intención ambigua o sin datos suficientes queda a cargo del orquestador.",
    )

    def run(self, entrada: ConsultaRequest) -> SalidaAgente[None]:
        entrada = self._entrada(entrada, ConsultaRequest)
        plan = self._plan({"mensaje": entrada.mensaje})
        return self._salida(entrada.tenant_id, plan, None, type(None))
