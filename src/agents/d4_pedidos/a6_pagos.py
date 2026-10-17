"""A6: comparación de importes; ninguna respuesta del modelo acredita dinero."""

from src.agents.base import BaseAgent
from src.schemas.agentes import EntradaPago, SalidaAgente
from src.schemas.resultados import ResultadoPago
from src.tools.pagos import comparar_pago


class A6Pagos(BaseAgent):
    """Mantiene estado no_conciliado mientras no haya evidencia bancaria."""

    id = "A6"
    accion = "pago"
    prompt = "Planifica solo pago. Devuelve accion, p y c; nunca confirmes una transferencia."

    def run(self, entrada: EntradaPago) -> SalidaAgente[ResultadoPago]:
        entrada = self._entrada(entrada, EntradaPago)
        plan = self._plan({"tarea": "pago", "evidencia_bancaria": "no_disponible"})
        resultado = ResultadoPago.model_validate(
            self._ejecutar(comparar_pago, **entrada.solicitud.model_dump())
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoPago)
