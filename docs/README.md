# Documentación de Veltri

## Ejecutar y mantener

Instalación y comandos: [README principal](../README.md). No copiar plantillas sobre el proyecto actual.

- [Arquitectura y referencia técnica](arquitectura.md): agentes, grafo, contratos, datos, herramientas, HITL, RAG, API e interfaz.
- [Seguridad y observabilidad](observabilidad.md): controles LangSmith y ejecución local.
- [Mantenimiento y verificación](mantenimiento.md): estructura, controles y recuperación.
- `agentes/`: nueve contratos visuales específicos; `contratos/`: 35 JSON Schema de intercambio.

## Presentar Semana 10

Para repetir las demos sin alterar el expediente: `python scripts/demo_academica.py`.
Se muestra el directorio temporal nuevo de salida; también admite `--salida`
con un directorio que aún no exista. Las carpetas originales de evidencias y
del Word están protegidas contra escritura por este script.

- [Word corregido de 17 páginas](entrega-semana10/Veltri_Semana10_Informe_Academico.docx), [generador](entrega-semana10/generar_informe.py).
- [Ejecuciones originales](evidencias/semana10-entrega-final/ejecuciones.json), [pruebas](evidencias/semana10-entrega-final/verificar.log) e [inventario de capturas](evidencias/semana10-entrega-final/inventario-13.json).
- [BPMN TO-BE original](bpmn_to_be.bpmn) y [BPMN AS-IS](bpmn_as_is.bpmn), comparación del proceso previo.
- [Segundo intento LangSmith](evidencias/semana10-fase43/resultado.md) y [registro de un solo uso](evidencias/semana10-fase43/ejecucion-unica.json).
- `evidencias/semana10-fase4/`: resultados originales del primer intento remoto, API, ocho agentes y revisión local; se retiraron los índices provisionales.
- `entrega-semana10/qa/control-calidad.json`: resultado de revisión visual; renders reproducibles conservados en respaldo externo.

El grafo comercial tiene **11 nodos operativos, 13 vértices y 20 aristas**. El Word y su generador contienen la corrección. Las instantáneas originales conservan afirmaciones y referencias históricas; no sustituyen esta documentación. Los documentos históricos retirados pueden recuperarse desde el respaldo de mantenimiento.

Siguen pendientes las capturas auténticas y acreditar visualmente la traza LangSmith. HTTP 202 no acredita un árbol remoto completo. No realizar otro envío para localizarla.

## Mantenimiento

[Depuración y recuperación](mantenimiento.md). Inventarios extensos, plantillas y guiones retirados permanecen fuera del repositorio.

El Word conserva su fecha y sus resultados originales; las fuentes corregidas pueden
cambiar los extractos al regenerarlo. Probar el generador en copia, sin sobrescribir
el entregable. Sus seis figuras documentales no son capturas auténticas del panel.
