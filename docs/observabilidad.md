# Semana 10 — Fase 3: observabilidad segura

Preparación actualizada: [Fase 4.2, diagnóstico HTTP y segundo intento](preparacion-langsmith-segundo-intento.md).
No ejecutar el procedimiento externo durante esta fase local.

Lanzador y condiciones de Fase 4.3: [lanzador de un solo uso](lanzador-langsmith-fase43.md).

Instrumentación implementada y validable localmente. No se ha enviado ninguna traza
a LangSmith. Una captura local JSON no acredita un run existente en el servicio.
No se han conectado Gemini, pagos ni otros modelos. Los precios y stock son sintéticos.

## Alcance y controles

Se mantiene `tracing_context(enabled=False)` y callbacks del grafo vacíos. Los spans
manuales nunca serializan argumentos ni resultados. La API y la UI funcionan como
antes; ningún parámetro HTTP abre una sesión observable. El único driver incluido
que abre sesión usa una solicitud fija de stock y MockLLM.

`VELTRI_TRACING_ENABLED=1` habilita instrumentación solo dentro de una sesión sintética
de confianza. `VELTRI_TRACING_SYNTHETIC_ONLY` debe ser `1`. Los valores ausentes o
inválidos cierran el opt-in. Para construir cliente externo se requiere ADEMÁS
`VELTRI_TRACING_ALLOW_EXTERNAL=1`, secreto no vacío y destino validado. Ambos opt-in
permanecen en `0` en `.env.example`. No se modifica `.env`.

El constructor exige proyecto fijo `veltri-semana10-demo` y endpoint oficial US o EU.
Se rechazan opciones adicionales de réplicas y direccionamiento por agentes del SDK.
No se autodetecta un proyecto privado. Región, permisos y retención requieren revisión
antes de la primera conexión. No se instalaron ni actualizaron dependencias.

Datos permitidos: UUID aleatorios, relaciones padre/hijo, nombres cerrados de operación,
inicio/fin reales y metadata constante `synthetic=true`, `model_mode=mock`,
`scenario=stock_demo`. Inputs y outputs vacíos. Error externo fijo `operation_failed`.
No se incluyen mensajes, contexto, tenants, datos personales, precios, stock exacto,
pagos, hashes de pedido, fragmentos RAG, excepciones originales, eventos ni adjuntos.
La clave se excluye de repr y model_dump. En una futura conexión, se usará únicamente
para autenticación del SDK; no forma parte del cuerpo de la traza.

El SDK utiliza ocultación adicional de inputs/outputs y metadata, omite runtime y
mantiene OpenTelemetry desactivado. Los spans se correlacionan mediante ContextVar,
incluidos los nodos ejecutados por LangGraph. Un fallo de create/update no repite
negocio ni sustituye respuestas. No se garantiza latencia cero: un envío futuro
sincrónico puede esperar el timeout del SDK. La validación conectada sigue pendiente.

## Procedimiento reproducible ahora: sin red

PowerShell, desde la raíz y con el entorno virtual existente:

```powershell
$env:USE_MOCK_LLM = '1'
$env:VELTRI_TRACING_ENABLED = '1'
$env:VELTRI_TRACING_SYNTHETIC_ONLY = '1'
$env:VELTRI_TRACING_ALLOW_EXTERNAL = '0'
$env:LANGSMITH_TRACING = 'false'
$env:LANGCHAIN_TRACING_V2 = 'false'
.venv/Scripts/python scripts/demo_observabilidad.py
```

La salida debe indicar `captura_local_sin_envio`, MockLLM, revisión humana y 18 eventos
(9 creaciones y 9 cierres). Árbol observado: consulta; seguridad; A1.plan_mock;
validar_plan; dominio con A5.plan_mock y comprobar_stock; decidir; responder.
`dominio` envuelve el nodo real a5_inventario. La llamada directa a alternativas
dentro de A5 no tiene span separado; no se fabrican spans de operaciones no envueltas.
Las operaciones del plan se rotulan mock y no se reportan tokens ni costes reales.
Una raíz terminada sin error técnico no significa venta aprobada: el resultado
comercial sigue requiriendo revisión humana por CPU-AMD-5500 agotado.

Para abrir la aplicación, en otra terminal con los opt-in en 0:

```powershell
$env:USE_MOCK_LLM = '1'
$env:VELTRI_TRACING_ENABLED = '0'
$env:VELTRI_TRACING_ALLOW_EXTERNAL = '0'
.venv/Scripts/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000. La UI no genera trazas externas. Para la evidencia comercial
usar la demo fija anterior; el driver inicia el mismo Orquestador sin servidor HTTP.
Así no se abre una vía para trazar consultas arbitrarias de visitantes.

## Procedimiento futuro conectado — NO EJECUTAR sin autorización adicional

1. Revisar la salida local y el contrato HTTP simulado de las pruebas; confirmar
   proyecto privado, región, permisos, retención y compatibilidad con SDK instalado.
2. Cargar `LANGSMITH_API_KEY` mediante `.env` ignorado o gestor de secretos del proceso,
   sin pegarla en comandos, historial, capturas ni repositorio. Establecer
   `LANGSMITH_PROJECT=veltri-semana10-demo` y `LANGSMITH_ENDPOINT` como
   `https://api.smith.langchain.com` o `https://eu.api.smith.langchain.com`.
3. Solo tras autorización de envío, configurar temporalmente los dos opt-in en `1`
   y SYNTHETIC_ONLY en `1`. Mantener los flags globales de trazado en false.
4. Ejecutar `.venv/Scripts/python scripts/demo_observabilidad.py --enviar` una vez.
   No hacerlo durante esta fase. El flag de CLI y la configuración son necesarios;
   el mensaje `envio_solicitado_no_verificado` NO confirma persistencia remota.
5. Abrir LangSmith en la cuenta autorizada, proyecto indicado, rango horario de la demo;
   buscar raíz `consulta`, metadata scenario=stock_demo/model_mode=mock. Cotejar sus
   nombres, padres y tiempos con el driver. Registrar ID y URL del run verificado.
6. Capturar panel con raíz y detalles de A1, A5 y comprobar_stock; comprobar cuerpos
   vacíos y metadata permitida, error fijo si procede. No mostrar clave, configuración
   de cuenta ni datos de otros proyectos. No afirmar vista nativa completa del grafo:
   estos son spans manuales. Capturar aparte el diagrama real del StateGraph.
7. Solo después de cotejar el run en el panel, rotularlo como traza auténtica de una
   ejecución sintética con MockLLM. No acredita inferencia Gemini ni conciliación real.
8. Desactivar ambos opt-in y detener el proceso de la demo; la API local permanece
   sin sesión observable. Ejecutar de nuevo la demo apagada: debe producir cero eventos.

```powershell
$env:VELTRI_TRACING_ENABLED = '0'
$env:VELTRI_TRACING_ALLOW_EXTERNAL = '0'
.venv/Scripts/python scripts/demo_observabilidad.py
Remove-Item Env:LANGSMITH_API_KEY -ErrorAction SilentlyContinue
```

Si se usó `.env`, restaurar también ambos opt-in a 0 allí y retirar el secreto si solo
se necesitaba temporalmente. No registrar sus valores ni tomar capturas de ese archivo.

## Evidencias y límites académicos

- LangGraph: diagrama obtenido de `crear_grafo(...).get_graph().draw_mermaid()`;
  seguridad y A1 siguen fuera del StateGraph. No se agregaron nodos ni aristas.
- LCEL: se usa `.invoke` de un Runnable compilado. No existen cadenas explícitas
  RunnableSequence/Parallel o ChatPromptTemplate; instrumentar no las crea.
- BPMN: compatibilidad parcial; el TO-BE encadena dominios y el grafo elige una rama.
  A8 no aparece en TO-BE. No se modificó el BPMN para ocultar esas diferencias.
- HITL: bandeja en memoria y resoluciones demo por código, sin autenticación de revisor,
  checkpoints, interrupt ni reanudación nativa. La observabilidad no concede aprobación.
- Persisten las discrepancias de UI/aprobación, IGV, garantía/envíos y CP-1 detectadas
  en Fase 2. No se corrigieron bajo esta autorización.
- Enunciado ya confirmado: Deep Agents, LangChain, LangGraph y LangSmith transversal. La clasificación anterior de cuatro etapas no sustituye capas; ver docs/auditoria-final-semana10.md.

Referencia de privacidad: [ocultación de datos en LangSmith](https://docs.langchain.com/langsmith/mask-inputs-outputs).
Implementación contrastada con el SDK instalado; el comportamiento remoto aún no se verificó.

## Validación local del 29/10/2026

Sobre el commit base `591670b`, con cambios locales sin commit:

- `python scripts/verificar.py`: 419 aprobadas, 0 fallos, 0 errores, 0 omitidas;
  2 advertencias de obsolescencia de Chroma/Google SDK. Pytest: 55.49 segundos.
  Ruff OK y escaneo de secretos sin hallazgos.
- Se conservan las 397 pruebas originales y se agregaron 22 pruebas offline.
  Incluyen flags, secreto excluido, privacidad del cuerpo HTTP serializado por el SDK,
  excepciones, concurrencia, UUID distintos entre consultas sucesivas, caída de
  telemetría, idempotencia, bloqueo previo y reglas de stock/socket/pago.
- La primera ejecución adicional de socket falló por un fixture incompleto: faltaban
  cinco categorías de componentes. Se completó la entrada sin cambiar la aserción
  ni el validador. La suite final pasó; no se ocultó una regresión de negocio.
- Demo apagada: cero eventos. Demo local activa: nueve spans y dieciocho eventos;
  ambas devuelven revision_humana. No equivalen a una traza remota.
- A1–A8: 24/24 comprobaciones sintéticas satisfactorias con MockLLM; cero llamadas
  a modelos reales. Cuatro operaciones ASGI devolvieron 200.
- Nodos y aristas compilados idénticos a Fase 2. Checkpointer ausente; sin llamadas
  interrupt/Command. Umbrales y línea base protegidos sin cambios.
- Verificación con guarda de red externa y credenciales reales retiradas del entorno
  de los procesos de prueba; los archivos de auditoría registran cero intentos externos.
  El SDK se verificó con transporte HTTP simulado, no mediante una conexión remota.

Inventario: [evidencias-semana10.json](evidencias-semana10.json). Cinco artefactos
técnicos obtenidos y verificados, tres listos para capturar, uno pendiente de
configuración/autorización y cuatro pendientes de confirmación académica. Ninguno
se presenta como captura de pantalla de navegador o LangSmith.

Archivos creados: `src/core/observabilidad.py`, `scripts/demo_observabilidad.py`,
`tests/test_observabilidad.py`, `docs/observabilidad.md`, `docs/evidencias-semana10.json`.
Archivos modificados: `src/config.py`, `.env.example`, `src/agents/base.py`,
`src/graph/workflow.py`, `src/graph/nodes.py`, `docs/arquitectura.md`,
`docs/guion-video.md`, `.agents/rules/estructura-y-comandos.md`.
No se hicieron commits, publicaciones, cambios de UI, BPMN, IGV, garantía ni Word.

Resumen para el video:

1. Preparamos monitoreo seguro para una demo sintética, apagado por defecto y sin enviar datos.
2. Pasaron 419 pruebas y verificamos los ocho agentes, el grafo y la bandeja de revisión.
3. Dejamos el procedimiento y las evidencias listas; una traza auténtica espera autorización.

## Resultado del intento externo autorizado del 31/10/2026

Una única demo se detuvo: dos POST 202 y primer PATCH 400, sin reintentos. No existe una traza completa verificada; ambos opt-in quedaron apagados. Detalle: [resultado de LangSmith](evidencias/semana10-fase4/resultado-langsmith.md). Los apartados anteriores que indican cero envíos describen las fases locales previas.

## Fase 4.1 — cierre local del diagnóstico

Se conservó el contexto de creación en update_run y se validó con transporte simulado y 420 pruebas. No se ha demostrado que esa diferencia provocara el HTTP 400. No hubo nuevas conexiones a LangSmith. Ambos opt-in siguen apagados. [Diagnóstico y límites](evidencias/semana10-fase41/diagnostico.md).

## Resultado de Fase 4.3

Intento detenido; no existe traza completa verificada. [Registro del segundo intento](evidencias/semana10-fase43/resultado.md). Ambos opt-in apagados; no repetir la ejecución.

## Auditoría final del enunciado confirmado

[Auditoría de los cinco requisitos](auditoria-final-semana10.md): Deep Agents ausente, componentes LCEL limitados y LangSmith pendiente de verificar la traza existente. Sin otra demo.
