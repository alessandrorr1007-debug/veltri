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
- src/core/: llm.py (fábrica real/mock), umbrales.py (protegido),
  criterios.py, decision.py, hitl.py, seguridad.py (guarda previa al modelo) y dlq.py (cola local de bloqueos).
- src/config.py: configuración .env/entorno, mock por defecto.
- src/tools/: catalogo.py, inventario.py, hardware.py, cotizacion.py, armador.py,
  pagos.py, pedidos.py, montos.py y registro.py. Pedidos son borradores de demo en memoria.
- src/schemas/: base.py, entradas.py, resultados.py, consulta.py, decision.py, hitl.py, agentes.py,
  flujo.py (incluye SolicitudAPI) y __init__.py.
- src/knowledge/: documentos.py, vectorizacion.py, almacen.py e ingesta.py.
- src/graph/: state.py (EstadoFlujo tipado sin texto libre), nodes.py (nodos de dominio y compuerta)
  y workflow.py (StateGraph acotado y fachada Orquestador).
- src/api/: main.py (FastAPI con POST /consulta, contrato ConsultaResponse y montaje estático de frontend/).
- src/agents/: base.py y ocho módulos de agente repartidos en
  d1_ventas (A1–A3), d2_tecnico (A4), d3_inventario (A5), d4_pedidos (A6–A8).
- Cada paquete Python trae __init__.py.
- tests/: test_invariantes.py, test_datos.py, test_herramientas.py, test_esquemas.py,
  test_conocimiento.py, test_decision_hitl.py, test_llm.py, test_agentes.py, test_flujo.py y test_api.py.
- frontend/: index.html, css/tokens.css, css/styles.css, js/icons.js, js/api.js, js/app.js (SPA sin CDN ni emojis).
- requirements-fase1.txt: pytest y ruff; requirements-dev.txt y requirements.txt:
  listas completas previstas por la plantilla. requirements-fase3.txt añade Pydantic
  y reúne las dependencias mínimas de contratos; requirements-fase4.txt añade
  ChromaDB y filelock para conocimiento. requirements-fase6.txt añade dotenv y
  google-genai para configuración y conector del modelo. requirements-fase7.txt añade
  langgraph y langsmith para el orquestador local. requirements-fase8.txt añade
  fastapi y httpx para la API.

## Comandos disponibles
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
