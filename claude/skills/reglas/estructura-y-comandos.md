# Estructura y comandos reales del proyecto

Esta regla describe lo que EXISTE. Si algo cambia (una carpeta o un comando), actualiza este archivo en la misma fase. Una regla que apunta a algo inexistente se vuelve ruido.

## Estructura

```
veltri/
├── GEMINI.md                  reglas permanentes (AGENTS.md apunta a este archivo)
├── AGENTS.md                  puntero para Codex y otros agentes
├── LEEME_entorno.md           guía de uso del entorno
├── .agents/                   rules, workflows y skills del agente
├── scripts/                   verificar, proteger, escanear secretos, instalar hooks
├── data/                      catalogo.json, compatibilidad.json, politicas.md
├── evals/                     casos_dorados.json, linea_base.json (protegido)
├── docs/                      arquitectura.md, guion-video.md, agentes/
├── frontend/                  index.html, css/, js/, assets/ locales
├── src/
│   ├── config.py
│   ├── core/                  llm.py, umbrales.py (protegido), decision.py, hitl.py, seguridad.py, gobernanza.py
│   ├── knowledge/             almacén RAG (ChromaDB), ingesta
│   ├── schemas/               modelos Pydantic
│   ├── tools/                 hardware, armador, inventario, pedidos (código determinista)
│   ├── agents/                d1_ventas, d2_tecnico, d3_inventario, d4_pedidos
│   ├── graph/                 state.py, nodes.py, workflow.py
│   └── api/                   main.py (FastAPI)
└── tests/
```

## Comandos que existen hoy

- `python scripts/verificar.py`: ruff + pytest + escaneo de secretos
- `python scripts/escanear_secretos.py`: busca claves en el repo
- `python scripts/instalar_hooks.py`: instala el hook pre-commit de Git
- `python -m pytest`: pruebas

## Comandos que aparecen en su fase (agrégalos aquí cuando existan)

- Servidor: `uvicorn src.api.main:app --reload` (Fase de API)
- Demo de consola: `python demo.py` (Fase de pruebas y demo)
- Indexar el almacén: `python -m src.knowledge.ingesta` (Fase de conocimiento)

## Convenciones

- Python 3.12 o superior, tipado y docstring corto en español en cada módulo.
- Nombres de archivos y carpetas en minúsculas con guion bajo.
- Cada paquete tiene `__init__.py`.
- Una prueba por comportamiento, con nombre que describa el caso.
