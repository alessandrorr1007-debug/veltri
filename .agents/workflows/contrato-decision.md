---
description: Define o revisa un contrato decide() con probabilidad, confianza y compuerta HITL
---

# /contrato-decision

Úsalo al crear o modificar una decisión del sistema (clasificar intención, enrutar, juzgar suficiencia de evidencia, evaluar riesgo, triar).

1. **Contrato.** Describe la decisión: opciones posibles (enum), qué evidencia usa y qué devuelve: opción elegida, probabilidad `p` y confianza `c`. Todo tipado con Pydantic en `src/schemas/decision.py`.
2. **Umbrales.** Lee `TAU_AUTO` y `TAU_REV` desde `src/core/umbrales.py`. No los dupliques ni los modifiques (archivo protegido).
3. **Compuerta.** Implementa la regla: `p >= TAU_AUTO` ejecuta; `TAU_REV <= p < TAU_AUTO` va a revisión humana; `p < TAU_REV` se escala.
4. **Invariantes por encima de p.** Si falla un invariante de negocio (stock, pago, socket, presupuesto), se exige HITL aunque `p` sea mayor que `TAU_AUTO`. Escribe una prueba que lo demuestre.
5. **Pruebas.** Casos en cada zona (auto, revisión, escalado) y un caso donde `p` alta NO autoriza por un invariante roto.
6. **Verificación.** `python scripts/verificar.py` y muestra la salida.
7. **Cierre.** Resumen de 3 líneas para el video y espera mi "continúa".
