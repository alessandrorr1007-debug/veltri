# Estructura y comandos reales del proyecto

Actualizar esta regla cuando aparezcan módulos o comandos nuevos.

## Archivos y carpetas existentes (FASES 1, 2, 3, 4 y 5)
- AGENTS.md apunta a GEMINI.md; LEEME_entorno.md guía la instalación.
- .agents/workflows/, .agents/skills/ y .agents/rules/: guías instaladas.
- claude/: paquete original conservado como referencia.
- scripts/: verificar.py, proteger.py, escanear_secretos.py, instalar_hooks.py.
- data/: catalogo.json, compatibilidad.json y politicas.md (ejemplos sintéticos).
- docs/: arquitectura.md, datos.md, herramientas.md, esquemas.md, guion-video.md
  conocimiento.md, decision_hitl.md y contratos/ con 18 JSON Schema.
- evals/: casos_dorados.json y linea_base.json (protegido).
- src/core/: llm.py (fábrica aún sin implementar), umbrales.py (protegido),
  criterios.py, decision.py e hitl.py (compuerta y bandeja local).
- src/tools/: catalogo.py, inventario.py, hardware.py, cotizacion.py, armador.py,
  pagos.py, pedidos.py y montos.py. Pedidos son borradores de demo en memoria.
- src/schemas/: base.py, entradas.py, resultados.py, consulta.py, decision.py, hitl.py
  y __init__.py.
- src/knowledge/: documentos.py, vectorizacion.py, almacen.py e ingesta.py.
- src/graph/, src/api/: paquetes vacíos.
- src/agents/: paquetes vacíos d1_ventas, d2_tecnico, d3_inventario y d4_pedidos.
- Cada paquete Python trae __init__.py.
- tests/: test_invariantes.py, test_datos.py, test_herramientas.py, test_esquemas.py
  test_conocimiento.py y test_decision_hitl.py.
- frontend/: solo .gitkeep; no hay interfaz implementada.
- requirements-fase1.txt: pytest y ruff; requirements-dev.txt y requirements.txt:
  listas completas previstas por la plantilla. requirements-fase3.txt añade Pydantic
  y reúne las dependencias mínimas de contratos; requirements-fase4.txt añade
  ChromaDB y filelock para conocimiento.

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

## Fases futuras (sin comandos ejecutables todavía)
Capa cognitiva/MockLLM, agentes, RAG generativo, grafo, API e interfaz.
No existen config.py, seguridad.py, gobernanza.py,
demo.py ni src/api/main.py.

## Convenciones
Python 3.12 o superior, tipado y docstring corto en español por módulo.
Nombres en minúsculas con guion bajo; __init__.py por paquete.
Una prueba por comportamiento. No confundir escenarios dorados con flujos ya ejecutables.
