"""A7: registro idempotente únicamente de borradores de demostración."""

from src.agents.base import BaseAgent
from src.schemas.agentes import EntradaPedido, SalidaAgente
from src.schemas.resultados import ResultadoPedido
from src.tools.catalogo import Catalogo
from src.tools.registro import RegistroPorTenant


class A7Pedidos(BaseAgent):
    """Un plan fuera de dominio o inválido falla antes de escribir el borrador."""

    id = "A7"
    accion = "pedido"
    prompt = (
        "Planifica solo pedido. Devuelve accion, p y c; "
        "solo borradores, sin confirmar ni despachar."
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
