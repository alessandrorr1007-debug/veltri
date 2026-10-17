"""A2: armado determinista de demostración con un plan validado por dominio."""

from src.agents.base import BaseAgent
from src.schemas.agentes import EntradaArmado, SalidaAgente
from src.schemas.resultados import ResultadoArmado
from src.tools.armador import armar
from src.tools.catalogo import Catalogo


class A2Armado(BaseAgent):
    """El modelo no elige precios ni componentes."""

    id = "A2"
    accion = "armar"
    prompt = "Planifica solo armar. Devuelve accion, p y c; no calcules ni autorices una venta."

    def run(self, entrada: EntradaArmado, catalogo: Catalogo) -> SalidaAgente[ResultadoArmado]:
        entrada = self._entrada(entrada, EntradaArmado)
        plan = self._plan({"tarea": "armar", "parametros": "rango_estructurado_del_llamador"})
        resultado = ResultadoArmado.model_validate(
            self._ejecutar(armar, catalogo, **entrada.solicitud.model_dump())
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoArmado)
