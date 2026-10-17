"""A5: inventario y alternativas comprobados contra el catálogo sintético."""

from src.agents.base import BaseAgent
from src.schemas.agentes import EntradaSeleccion, ResultadoInventario, SalidaAgente
from src.tools.catalogo import Catalogo
from src.tools.inventario import alternativas, comprobar_stock


class A5Inventario(BaseAgent):
    """Sugiere sin sustituir ni reservar productos."""

    id = "A5"
    accion = "stock"
    prompt = "Planifica solo stock. Devuelve accion, p y c; no inventes disponibilidad."

    def run(
        self, entrada: EntradaSeleccion, catalogo: Catalogo
    ) -> SalidaAgente[ResultadoInventario]:
        entrada = self._entrada(entrada, EntradaSeleccion)
        plan = self._plan({"tarea": "stock"})
        stock = self._ejecutar(comprobar_stock, catalogo, entrada.seleccion)
        sugerencias = {f["sku"]: alternativas(catalogo, f["sku"]) for f in stock["faltantes"]}
        resultado = ResultadoInventario(stock=stock, alternativas=sugerencias)
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoInventario)
