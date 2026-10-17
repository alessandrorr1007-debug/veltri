---
description: Crea un agente nuevo siguiendo diagrama, contrato, código y pruebas en ese orden
---

# /agente-nuevo

Úsalo cuando haya que crear un agente (por ejemplo A9). Pregunta primero el nombre, el dominio (D1 a D4) y qué decide el agente. No escribas código antes de terminar los pasos 1 y 2.

1. **Diagrama primero.** Crea `docs/agentes/<nombre>.md` con un diagrama Mermaid: entradas, herramientas que usa, salidas y qué nodo del grafo lo invoca. El diagrama es el contrato visual; si no existe, no se escribe el agente.
2. **Contrato tipado.** Define en `src/schemas/` el modelo Pydantic de entrada y de salida del agente. La salida no puede contener prosa libre que el grafo tenga que interpretar.
3. **Herramientas deterministas.** Cualquier cálculo (precios, stock, compatibilidad, montos) va en `src/tools/`, no en el prompt del agente.
4. **Agente.** Implementa en `src/agents/<dominio>/` heredando de `BaseAgent`, con su prompt propio y el modelo obtenido solo con `get_llm()`.
5. **Nodo y ruta.** Registra el nodo en `src/graph/` y enruta por campos tipados, nunca leyendo texto del LLM.
6. **Pruebas.** Escribe pruebas con `MockLLM`: caso feliz, caso límite y caso de falla. Agrega al menos un caso a `evals/casos_dorados.json` si el agente cambia el comportamiento de algún CP.
7. **Verificación.** Ejecuta `python scripts/verificar.py` y muestra la salida real.
8. **Cierre.** Actualiza `docs/arquitectura.md` y entrega el resumen de 3 líneas para el video (skill `documentar-para-video`). Espera mi "continúa".
