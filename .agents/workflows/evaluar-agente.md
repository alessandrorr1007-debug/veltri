---
description: Evalúa un agente o el sistema contra los casos dorados y detecta regresiones
---

# /evaluar-agente

Úsalo después de cambiar un agente, un prompt, una herramienta o el grafo.

1. **Carga los casos.** Lee `evals/casos_dorados.json` (CP-1 a CP-7). Pregunta si se evalúa un agente concreto o el sistema completo.
2. **Ejecuta con MockLLM.** Corre cada caso relevante sin red. Para cada uno compara el resultado con `esperado`.
3. **Reglas de evaluación.**
   - Una respuesta correcta con la fuente, el SKU o el motivo equivocado cuenta como FALLO.
   - Las cifras se validan contra el cálculo determinista, no contra lo que dice el texto.
   - Un caso que antes pasaba y ahora falla es una REGRESIÓN y se reporta primero.
4. **Compara con la línea base.** Lee `evals/linea_base.json`. Si está vacía, indica que aún no hay línea base.
5. **No toques la línea base.** Nunca la actualices por tu cuenta. Si los 7 casos pasan y quieres congelarla, pídeme autorización explícita.
6. **Reporte.** Tabla con caso, resultado (pasa, falla o regresión), motivo y qué archivo revisar. Termina con el comando para reproducirlo.
