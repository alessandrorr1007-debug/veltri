"""A5: inventario y alternativas comprobados contra el catálogo sintético."""

from src.agents.base import BaseAgent
from src.agents.prompts import prompt_plan
from src.schemas.agentes import EntradaSeleccion, ResultadoInventario, SalidaAgente
from src.tools.catalogo import Catalogo
from src.tools.inventario import alternativas, comprobar_stock


class A5Inventario(BaseAgent):
    """Sugiere sin sustituir ni reservar productos."""

    id = "A5"
    accion = "stock"
    prompt = prompt_plan(
        accion=accion,
        rol="A5 · D3. Planifica una consulta de stock y sugerencias.",
        contexto="La selección explícita se contrasta con existencias del catálogo sintético.",
        herramientas="El código usa comprobar_stock y alternativas solo para faltantes.",
        proceso="Emite stock. Si el código detecta faltantes, las alternativas son sugerencias.",
        limites="No reserves stock ni sustituyas productos; no prometas disponibilidad real.",
        bloqueo="Un faltante exige revisión aunque exista una alternativa.",
    )

    def run(
        self, entrada: EntradaSeleccion, catalogo: Catalogo
    ) -> SalidaAgente[ResultadoInventario]:
        entrada = self._entrada(entrada, EntradaSeleccion)
        plan = self._plan({"tarea": "stock"})
        stock = self._ejecutar(comprobar_stock, catalogo, entrada.seleccion)
        sugerencias = {f["sku"]: alternativas(catalogo, f["sku"]) for f in stock["faltantes"]}
        resultado = ResultadoInventario.model_validate(
            {"stock": stock, "alternativas": sugerencias}
        )
        return self._salida(entrada.tenant_id, plan, resultado, ResultadoInventario)
