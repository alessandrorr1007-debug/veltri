# Semana 10 — evidencias técnicas de Veltri

Fecha: 31 de octubre de 2026, America/Lima. Este expediente complementa las
auditorías históricas; sus afirmaciones de ausencia de LCEL y Deep Agents ya no
describen el módulo académico actual. No se ha sustituido la arquitectura comercial.

## Estado de los cinco requisitos

1. **LCEL implementado y ejecutado localmente.** `src/academic/lcel.py` compone
   `RunnableLambda | RunnableParallel | RunnableLambda`: valida un fixture tipado,
   consulta el stock sintético mediante `src/tools/inventario.py` y devuelve
   `SalidaAcademica`. El operador produce un `RunnableSequence`, comprobado por
   prueba. `.invoke()` ejecuta la composición; no es una unión de tipos Python.
   Su utilidad es demostrar el bloqueo de revisión para el caso local sin stock.
   No incluye ChatPromptTemplate porque este pipeline no necesita un prompt.
   Capturas auténticas del código y la ejecución siguen pendientes.
2. **LangGraph e HITL demostrados localmente; BPMN parcialmente compatible.**
   `grafo-comercial.mmd` y `.json` provienen del grafo compilado actual: 12 nodos
   operativos, 14 vértices con START/END y 20 aristas. A1 y seguridad están fuera
   del grafo. La bandeja anterior se ejecuta y registra antes/después en
   `ejecuciones.json`. El módulo `src/academic/hitl.py` incorpora, exclusivamente
   para la demo, `InMemorySaver`, `interrupt` y `Command(resume=...)`.
   Se verifican aprobación, rechazo, corrección y decisión inválida.
   Las decisiones del script son fixtures de un revisor simulado, no una persona
   autenticada ni autorizaciones de pedidos. Los checkpoints no sobreviven al proceso.
3. **LangSmith pendiente de acreditar.** El expediente remoto histórico conserva
   nueve creaciones y nueve cierres HTTP 202, seguidos de GET 403. No hay run_id
   remoto verificado ni duración o árbol cotejado. No se realizó otra demostración.
   Debe revisarse la traza existente mediante el panel autenticado; 202 no acredita
   persistencia. No atribuir definitivamente el 403 a una clave Tracing Only.
4. **Deep Agents reales implementados y ejecutados con MockLLM.**
   `src/academic/deep_agents.py` utiliza `deepagents.create_deep_agent`, el modelo
   adaptado de `get_llm()` y las herramientas del framework `write_todos` y `task`.
   DA-CoordinadorAcademico delega en DA-Catalogo y DA-Revision. Cada especialista
   ejecuta `revisar_fixture_sintetico`, herramienta determinista de solo lectura.
   El registro del adaptador verifica respuestas exitosas de esas herramientas.
   Las respuestas y el plan son programados; se acredita ejecución del framework,
   no capacidad de planificación autónoma. Los todos y mensajes son contexto de
   la ejecución; no se afirma memoria persistente o uso de archivos virtuales.
   A1–A8 siguen siendo agentes personalizados y no se convierten en Deep Agents.
5. **Cuatro componentes relacionados con código real.** Deep Agents aporta
   coordinación de alto nivel y subagentes; LangChain aporta BaseChatModel,
   herramientas y composición LCEL; LangGraph ejecuta los grafos y la pausa nativa;
   LangSmith es una plataforma transversal de observabilidad. Las demos académicas
   no envían trazas. La instrumentación comercial existente está apagada y su
   evidencia remota sigue pendiente. Véase `ecosistema.mmd`.

## Comparación con BPMN TO-BE sin modificarlo

- Inicio y recepción: A1 y filtro de seguridad anteceden a StateGraph, mientras el
  BPMN distribuye recepción e interpretación en actividades.
- Cotización: BPMN propone A2 → A4 → A5 → A3; el grafo selecciona una rama principal
  por solicitud y pasa a decidir/responder. Son estructuras diferentes.
- Compuertas: el gateway inclusivo BPMN no equivale al selector tipado de una rama.
- Stock y compatibilidad: existen herramientas y agentes, pero su presencia no
  demuestra ejecución secuencial de todas las actividades BPMN.
- Pagos y pedidos: comparación y borradores locales; no conciliación con un
  proveedor externo ni despacho real. A8 existe en el código y no aparece en BPMN.
- Revisión comercial: bandeja en memoria sin interrupt/checkpointer ni revisor
  autenticado. La nueva demo nativa es independiente y no corrige esta diferencia.
- IGV, garantías y tiempos: permanecen las discrepancias documentadas en
  `docs/auditoria-final-semana10.md`; no se corrigieron cifras ni promesas comerciales.

## Reproducción y seguridad

Instalar `requirements-academico.txt` en el entorno virtual. Ejecutar:

```
.venv/Scripts/python scripts/demo_academica.py
.venv/Scripts/python scripts/verificar.py
```

La demo desactiva las banderas de trazabilidad en su proceso y usa
`tracing_context(enabled=False)`. No lee `.env`, no instancia clientes de pago,
no admite texto arbitrario ni expone endpoints. Solo acepta el escenario cerrado
`revision_sintetica`; campos adicionales o escenarios distintos son rechazados.
El archivo `.env.txt` también se ignora en Git como precaución para copias locales.
Las dependencias de proveedores exigidas por Deep Agents no implican llamadas
remotas; los modelos se obtienen exclusivamente mediante `get_llm` en modo mock.

Versiones elegidas: deepagents 0.4.11, langchain 1.2.11,
langchain-anthropic 1.3.4 y langchain-google-genai 4.4.2. Se preservan
langchain-core 1.6.12, langgraph 1.2.16, langsmith 0.14.11 y google-genai 2.31.0.
La versión más reciente de Deep Agents requería actualizar dependencias ya usadas;
se eligió una versión compatible para limitar el impacto. `pip check` no detectó
dependencias rotas. Consultar versiones realmente ejecutadas en `ejecuciones.json`.

## Evidencias disponibles y capturas pendientes

`ejecuciones.json` contiene resultados auténticos locales, fecha UTC, versiones,
mensajes, llamadas a herramientas y decisiones simuladas. Los `.mmd` describen
grafos reales o diagramas explicativos expresamente rotulados. Los diagramas
no son capturas del panel. `fuentes-con-lineas.txt` permite localizar el código.
`verificar.log` y `pytest-suite.xml` conservan la verificación completa.
`inventario-13.json` actualiza la preparación de las capturas sin fabricar PNG.

Para LangSmith: abrir el proyecto veltri-semana10-demo, buscar la ejecución del
31/10/2026 entre 09:39:46 y 09:40:03 America/Lima, abrir la raíz `consulta`,
verificar run_id, duración, nueve spans, metadata sintética e inputs/outputs vacíos.
Capturar lista del proyecto, detalle de la raíz y árbol completo. Evitar páginas
de claves, datos de cuenta y secretos. Si no aparece, informar sin repetir el envío.

El Word final sigue condicionado a verificar la traza y obtener las capturas reales;
este expediente no se presenta como entrega académica íntegramente acreditada.

## Referencias técnicas

- https://docs.langchain.com/oss/python/deepagents/quickstart
- https://docs.langchain.com/oss/python/deepagents/subagents
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://reference.langchain.com/python/langchain_core/runnables/

## Guion de tres líneas

Creamos demos reales de LCEL, HITL nativo y Deep Agents sin cambiar las ventas.
Las ejecutamos con MockLLM y verificamos sus herramientas, delegaciones y resultados.
Falta cotejar la traza existente de LangSmith y capturar el panel antes del Word final.

## Verificación final ejecutada

`python scripts/verificar.py`, bajo guarda local sin red externa y sin claves reales:

- Ruff: All checks passed!
- Pytest: 464 passed, 2 warnings in 48.51s.
- Escaneo de secretos: sin hallazgos.
- 456 pruebas previas conservadas más 8 nuevas; 0 fallos, errores u omitidas.
- Dos avisos de deprecación de ChromaDB y Google SDK, sin regresiones.
- Ningún archivo protegido modificado; sin commits ni envíos nuevos a LangSmith.
