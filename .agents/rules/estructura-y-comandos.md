# Estructura y comandos reales del proyecto

Actualizar esta regla cuando aparezcan módulos o comandos nuevos.

## Archivos y carpetas existentes (FASES 1, 2, 3, 4, 5, 6, 7, 8 y 9)
- AGENTS.md apunta a GEMINI.md; LEEME_entorno.md guía la instalación.
- .agents/workflows/, .agents/skills/ y .agents/rules/: guías instaladas.
- claude/: paquete original conservado como referencia.
- scripts/: verificar.py, proteger.py, escanear_secretos.py, instalar_hooks.py.
- data/: catalogo.json, compatibilidad.json y politicas.md (ejemplos sintéticos).
- docs/: arquitectura.md, datos.md, herramientas.md, esquemas.md, guion-video.md,
  conocimiento.md, decision_hitl.md, agentes.md, grafo.md, api.md, interfaz.md, agentes/ y contratos/ con 35 JSON Schema.
- evals/: casos_dorados.json y linea_base.json (protegido).
- src/core/: llm.py (fábrica real/mock), observabilidad.py (spans sintéticos opt-in), umbrales.py (protegido),
  criterios.py, decision.py, hitl.py, seguridad.py (guarda previa al modelo) y dlq.py (cola local de bloqueos).
- src/config.py: configuración .env/entorno, mock por defecto.
- src/core/diagnostico_http.py: transporte de diagnóstico con primer fallo seguro y sin reintentos; tests/test_diagnostico_http.py lo verifica offline.
- src/tools/: catalogo.py, inventario.py, hardware.py, cotizacion.py, armador.py,
  pagos.py, pedidos.py, montos.py, registro.py y consulta_comercial.py (atención determinista con memoria y catálogo).
- src/schemas/: base.py, entradas.py, resultados.py, consulta.py, decision.py, hitl.py, agentes.py,
  flujo.py (incluye SolicitudAPI con contexto) y __init__.py.
- src/knowledge/: documentos.py, vectorizacion.py, almacen.py e ingesta.py.
- src/graph/: state.py (EstadoFlujo tipado sin texto libre), nodes.py (nodos de dominio y compuerta)
  y workflow.py (StateGraph acotado y fachada Orquestador).
- src/api/: main.py (FastAPI con POST /consulta, GET /catalogo, contrato ConsultaResponse y montaje estático de frontend/).
- src/agents/: base.py y ocho módulos de agente repartidos en
  d1_ventas (A1–A3), d2_tecnico (A4), d3_inventario (A5), d4_pedidos (A6–A8).
- Cada paquete Python trae __init__.py.
- tests/: test_invariantes.py, test_datos.py, test_herramientas.py, test_esquemas.py,
  test_conocimiento.py, test_decision_hitl.py, test_llm.py, test_agentes.py, test_flujo.py, test_api.py y test_consulta_comercial.py.
- frontend/: index.html, css/tokens.css, css/styles.css, js/icons.js, js/api.js, js/app.js (SPA de cliente sin CDN ni emojis con Consola Comercial y Catálogo de Hardware).
- requirements.txt: dependencias de ejecución y académicas, con versiones directas y transitivas fijadas para el perfil Windows x64/CPython 3.14 verificado.
- requirements-dev.txt: incluye requirements.txt y añade pytest, Ruff, httpx y herramientas del generador Word.
- requirements-academico.txt: alias de compatibilidad hacia requirements.txt; no es otra lista de versiones.
- docs/README.md: índice vigente; docs/mantenimiento/limpieza-20261102.md: auditoría y recuperación de residuos.


## Comandos disponibles
- docs/entrega-semana10/: informe Word, figuras documentales, procedencia y QA de la Fase 6. generar_informe.py usa el runtime documental y las evidencias guardadas, sin red.
- python scripts/demo_academica.py: LCEL, HITL nativo y Deep Agents reales con MockLLM; exporta evidencia local sin trazas.
- python -m pip install -r requirements-dev.txt: instalación completa verificada; requirements-academico.txt conserva compatibilidad con las guías académicas.
- python scripts/langsmith_segundo_intento.py --enviar-autorizado --rotacion-confirmada: una demo externa SOLO bajo autorización humana nueva, registro de un solo uso; guía docs/lanzador-langsmith-fase43.md.
- python scripts/demo_observabilidad.py: demo sintética fija, captura local sin envío por defecto; guía en docs/observabilidad.md.
- python scripts/verificar.py: ruff + pytest + escaneo de secretos.
- python scripts/escanear_secretos.py: escaneo de secretos.
- python scripts/proteger.py: protección de archivos staged.
- python scripts/instalar_hooks.py: instala el hook pre-commit en Git.
- python -m pytest: pruebas completas.
- python -m pytest tests/test_herramientas.py -q: pruebas de herramientas.
- python -m pytest tests/test_esquemas.py -q: pruebas de contratos.
- python scripts/exportar_esquemas.py: regenera docs/contratos/.
- python -m src.knowledge.ingesta --tenant IDENTIFICADOR: ingesta del corpus de demo.
- python -m pytest tests/test_conocimiento.py -q: pruebas de conocimiento.
- python -m pytest tests/test_decision_hitl.py -q: pruebas de compuerta y revisión.
- python -m pytest tests/test_llm.py tests/test_agentes.py -q: pruebas cognitivas.
- python -m pytest tests/test_flujo.py -q: pruebas integradas de flujo y casos dorados.
- python -m pytest tests/test_api.py -q: pruebas de la API FastAPI y contratos HTTP.
- uvicorn src.api.main:app --reload: inicia el servidor de desarrollo local y sirve la UI en http://localhost:8000.

## Fases futuras (sin comandos ejecutables todavía)
Demo final y preflight de entrega.
No existen gobernanza.py ni demo.py.

## Convenciones
Python 3.12 o superior, tipado y docstring corto en español por módulo.
Nombres en minúsculas con guion bajo; __init__.py por paquete.
Una prueba por comportamiento. No confundir escenarios dorados con flujos ya ejecutables.
