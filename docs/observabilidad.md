# Observabilidad segura de Veltri

## Estado actual

Instrumentación: `src/core/observabilidad.py`; transporte: `src/core/diagnostico_http.py`. Monitoreo apagado por defecto. La API no permite habilitarlo por HTTP.

El segundo intento recibió nueve POST y nueve PATCH HTTP 202; la lectura posterior devolvió 403 y se detuvo. No hay run_id, duración ni árbol remoto verificados. Se conservan el [resultado](evidencias/semana10-fase43/resultado.md) y el [registro consumido](evidencias/semana10-fase43/ejecucion-unica.json). El [primer resultado remoto](evidencias/semana10-fase4/resultado-langsmith.md) conserva el HTTP 400; su causa histórica no está confirmada.

## Controles de privacidad

- Primer opt-in: `VELTRI_TRACING_ENABLED=1`, con `VELTRI_TRACING_SYNTHETIC_ONLY=1`.
- Segundo opt-in independiente: `VELTRI_TRACING_ALLOW_EXTERNAL=1`.
- Sesión de confianza con MockLLM, proyecto `veltri-semana10-demo`, destino oficial validado y clave local. Valores ausentes o inválidos cierran el acceso.
- Flags globales `LANGSMITH_TRACING` y `LANGCHAIN_TRACING_V2` en false.
- Solo UUID aleatorios, nombres cerrados, parentesco, tiempos y metadata sintética constante; inputs y outputs vacíos.
- Sin mensajes, datos personales, tenants, SKUs, precios, pagos, RAG ni credenciales en trazas. La clave se usa solo para autenticar y se excluye de representaciones.
- El transporte conserva el primer fallo y bloquea solicitudes posteriores, redirecciones y reintentos. El diagnóstico solo registra método, ruta sin parámetros sensibles, estado, categoría, correlación sintética y etapa.
- Los cierres conservan el contexto de creación. Las pruebas locales acreditan formato y controles; no persistencia remota.

## Demostración local sin envío

Desde la raíz, con el entorno virtual preparado:

```powershell
$env:USE_MOCK_LLM = '1'
$env:VELTRI_TRACING_ENABLED = '1'
$env:VELTRI_TRACING_SYNTHETIC_ONLY = '1'
$env:VELTRI_TRACING_ALLOW_EXTERNAL = '0'
$env:LANGSMITH_TRACING = 'false'
$env:LANGCHAIN_TRACING_V2 = 'false'
try {
    .venv/Scripts/python scripts/demo_observabilidad.py
} finally {
    $env:VELTRI_TRACING_ENABLED = '0'
    $env:VELTRI_TRACING_ALLOW_EXTERNAL = '0'
}
```

La captura local contiene nueve creaciones y nueve cierres: consulta, seguridad, A1.plan_mock, validar_plan, dominio, A5.plan_mock, comprobar_stock, decidir y responder. No es una traza remota. El stock es sintético y requiere revisión humana.

## Lanzador remoto y autorización

`scripts/langsmith_segundo_intento.py` es de un solo uso; su registro ya está consumido. **No borrar ni reiniciar el registro para volver a enviar.**

No ejecutar el lanzador ni `demo_observabilidad.py --enviar` sin autorización humana nueva y específica. Una limpieza o validación local no la conceden. Cualquier autorización futura exige revisar doble opt-in, rotación de la clave expuesta, payload, prueba local, bloqueo de reintentos y apagado en toda salida. Nunca copiar claves a comandos, registros o capturas.

La siguiente evidencia necesaria es revisar la traza existente en el panel autenticado: proyecto indicado, 31/10/2026, 09:39:46–09:40:03 America/Lima, raíz `consulta`. Verificar run_id, duración, árbol, metadata e inputs/outputs vacíos. Ese intervalo es del procedimiento, no una duración remota acreditada. El 403 puede relacionarse con permisos; su causa no está demostrada.

## Alcance académico vigente

LCEL, HITL nativo y Deep Agents existen en `src/academic/` y se prueban localmente con MockLLM, sin trazas externas. La bandeja comercial es distinta del interrupt/checkpointer académico. BPMN es parcialmente compatible. La presentación vigente está en [el índice](README.md).

Verificación: `python scripts/verificar.py`, incluidas las pruebas de observabilidad, transporte HTTP y lanzador. Referencia oficial: [privacidad LangSmith](https://docs.langchain.com/langsmith/mask-inputs-outputs).
