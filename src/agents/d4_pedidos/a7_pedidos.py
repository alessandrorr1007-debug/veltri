"""A7: registro idempotente únicamente de borradores de demostración."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import EntradaPedido, SalidaAgente
from src.schemas.resultados import ResultadoPedido
from src.tools.catalogo import Catalogo
from src.tools.registro import RegistroPorTenant


class A7Pedidos(BaseAgent):
    """Un plan fuera de dominio o inválido falla antes de escribir el borrador."""

    id = "A7"
    accion = "pedido"
    prompt = prompt_plan(
        accion=accion,
        rol="A7 · D4. Planifica el registro idempotente de un borrador sintético.",
        contexto="El llamador aporta tenant, selección y confirmar_borrador tipados.",
        herramientas="El código usa RegistroPorTenant.registrar tras validar la entrada.",
        proceso="Emite pedido. El código usa los mismos datos para deduplicar por SHA-256.",
        limites="No suplas consentimiento ni generes claves; no confirmes, cobres ni despaches.",
        bloqueo="Si falta confirmación o hay bloqueos de negocio, conserva el control humano.",
    )

    def run(
        self, entrada: EntradaPedido, catalogo: Catalogo, registro: RegistroPorTenant
    ) -> SalidaAgente[ResultadoPedido]:
        entrada = self._entrada(entrada, EntradaPedido)
        plan = self._plan({"tarea": "pedido", "alcance": "borrador_sintetico"})
        resultado = ResultadoPedido.model_validate(
            self._ejecutar(
                registro.registrar,
                entrada.tenant_id,
                **entrada.solicitud.model_dump(),
                catalogo=catalogo,
            )
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoPedido)
