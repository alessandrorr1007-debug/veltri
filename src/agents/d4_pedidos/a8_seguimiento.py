"""A8: seguimiento local de borradores, sin prometer envío o confirmación."""

from src.agents.base import BaseAgent
from src.schemas.agentes import EntradaSeguimiento, EstadoBorrador, SalidaAgente
from src.tools.registro import RegistroPorTenant


class A8Seguimiento(BaseAgent):
    """Consulta el tenant del contexto, nunca el sugerido por un modelo."""

    id = "A8"
    accion = "seguimiento"
    prompt = "Planifica solo seguimiento. Devuelve accion, p y c; no inventes estados ni despachos."

    def run(
        self, entrada: EntradaSeguimiento, registro: RegistroPorTenant
    ) -> SalidaAgente[EstadoBorrador]:
        entrada = self._entrada(entrada, EntradaSeguimiento)
        plan = self._plan({"tarea": "seguimiento"})
        borrador = self._ejecutar(registro.consultar, entrada.tenant_id, entrada.clave)
        resultado = EstadoBorrador(encontrado=borrador is not None, borrador=borrador)
        return self._salida(entrada.tenant_id, plan, resultado, EstadoBorrador)
