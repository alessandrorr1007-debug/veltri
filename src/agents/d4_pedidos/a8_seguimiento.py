"""A8: seguimiento local de borradores, sin prometer envío o confirmación."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import EntradaSeguimiento, EstadoBorrador, SalidaAgente
from src.tools.registro import RegistroPorTenant


class A8Seguimiento(BaseAgent):
    """Consulta el tenant del contexto, nunca el sugerido por un modelo."""

    id = "A8"
    accion = "seguimiento"
    prompt = prompt_plan(
        accion=accion,
        rol="A8 · D4. Planifica la lectura de un borrador.",
        contexto="La clave y el tenant vienen del llamador; el registro es local.",
        herramientas="El código usa RegistroPorTenant.consultar en modo lectura.",
        proceso="Emite seguimiento; una clave sin coincidencia en el tenant se trata como ausente.",
        limites="No cambies de tenant, ni inventes estados de pago, pedido o despacho.",
        bloqueo="Un borrador ausente o sin evidencia queda sujeto a la compuerta de revisión.",
    )

    def run(
        self, entrada: EntradaSeguimiento, registro: RegistroPorTenant
    ) -> SalidaAgente[EstadoBorrador]:
        entrada = self._entrada(entrada, EntradaSeguimiento)
        plan = self._plan({"tarea": "seguimiento"})
        borrador = self._ejecutar(registro.consultar, entrada.tenant_id, entrada.clave)
        resultado = EstadoBorrador.model_validate({
            "encontrado": borrador is not None, "borrador": borrador})
        return self._salida(entrada.tenant_id, plan, resultado, EstadoBorrador)
