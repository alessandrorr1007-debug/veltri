# Documentación de Veltri

## Ejecutar y mantener

Instalación y comandos: [README principal](../README.md). No copiar plantillas sobre el proyecto actual.

- [Arquitectura](arquitectura.md), [agentes A1–A8](agentes.md) y [grafo](grafo.md).
- [API](api.md) e [interfaz](interfaz.md).
- [Datos sintéticos](datos.md), [herramientas](herramientas.md) y [contratos](esquemas.md).
- [RAG](conocimiento.md), [decisión e HITL](decision_hitl.md).
- [Observabilidad y seguridad LangSmith](observabilidad.md).
- `agentes/`: contratos visuales por agente; `contratos/`: JSON Schema exportables.

## Presentar Semana 10

- [Word corregido de 17 páginas](entrega-semana10/Veltri_Semana10_Informe_Academico.docx), [generador](entrega-semana10/generar_informe.py) y [alcance](entrega-semana10/README.md).
- [Ejecuciones originales](evidencias/semana10-entrega-final/ejecuciones.json), [pruebas](evidencias/semana10-entrega-final/verificar.log) e [inventario de capturas](evidencias/semana10-entrega-final/inventario-13.json).
- [BPMN TO-BE original](bpmn_to_be.bpmn) y [BPMN AS-IS](bpmn_as_is.bpmn), comparación del proceso previo.
- [Segundo intento LangSmith](evidencias/semana10-fase43/resultado.md) y [registro de un solo uso](evidencias/semana10-fase43/ejecucion-unica.json).
- `evidencias/semana10-fase4/`: resultados originales del primer intento remoto, API, ocho agentes y revisión local; se retiraron los índices provisionales.
- `entrega-semana10/qa/langgraph-corregido/`: revisión visual del Word vigente.

El grafo comercial tiene **11 nodos operativos, 13 vértices y 20 aristas**. El Word y su generador contienen la corrección. Las instantáneas originales conservan afirmaciones y referencias históricas; no sustituyen esta documentación. Los documentos históricos retirados pueden recuperarse desde el respaldo de mantenimiento.

Siguen pendientes las capturas auténticas y acreditar visualmente la traza LangSmith. HTTP 202 no acredita un árbol remoto completo. No realizar otro envío para localizarla.

## Mantenimiento

[Depuración y recuperación](mantenimiento.md). Inventarios extensos, plantillas y guiones retirados permanecen fuera del repositorio.
