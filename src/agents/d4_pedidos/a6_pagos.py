"""A6: comparación de importes; ninguna respuesta del modelo acredita dinero."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import EntradaPago, SalidaAgente
from src.schemas.resultados import ResultadoPago
from src.tools.pagos import comparar_pago


class A6Pagos(BaseAgent):
    """Mantiene estado no_conciliado mientras no haya evidencia bancaria."""

    id = "A6"
    accion = "pago"
    prompt = prompt_plan(
        accion=accion,
        rol="A6 · D4. Planifica la comparación de importes.",
        contexto="Importes tipados del llamador y evidencia bancaria no disponible.",
        herramientas="El código usa comparar_pago; ningún acceso bancario.",
        proceso=(
            "Emite pago y deja la comparación al código. Ejemplos de límites: "
            "importes iguales → no conciliado; importes distintos → no conciliado."
        ),
        limites="No acredites transferencias ni conviertas monedas; omite comprobantes.",
        bloqueo="Pago discrepante o ausencia de evidencia bancaria exigen revisión.",
    )

    def run(self, entrada: EntradaPago) -> SalidaAgente[ResultadoPago]:
        entrada = self._entrada(entrada, EntradaPago)
        plan = self._plan({"tarea": "pago", "evidencia_bancaria": "no_disponible"})
        resultado = ResultadoPago.model_validate(
            self._ejecutar(comparar_pago, **entrada.solicitud.model_dump())
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoPago)
