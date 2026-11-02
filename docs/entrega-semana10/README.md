# Informe académico de Semana 10

Entregable: `Veltri_Semana10_Informe_Academico.docx`.
Fecha de corte: 31 de octubre de 2026, America/Lima.

El Word contiene 17 páginas, seis figuras documentales, trece tablas, código con
archivos y líneas, resultados locales y referencias. Se revisaron visualmente
todas las páginas después de la exportación nativa de Word a PDF y PNG de QA.
Los PNG de QA son páginas renderizadas del informe, no capturas de la aplicación.
La revisión actual está en `qa/langgraph-corregido/`; incluye los grados por nodo y
la corrección a 11 nodos operativos, 13 vértices y 20 aristas.

No hay capturas auténticas incorporadas: no se aportaron manuales y el acceso
automatizado al navegador estaba bloqueado. No se intentó eludir esa restricción.
El requisito 3 de LangSmith permanece explícitamente pendiente de acreditación.
No se hicieron nuevos envíos externos ni se modificó la lógica comercial.

Los registros originales siguen en `docs/evidencias/semana10-entrega-final/` y en
las carpetas de las fases anteriores. `procedencia.json` registra sus hashes.
`generar_informe.py` permite reproducir el documento con las bibliotecas del
runtime documental. `figuras/` contiene diagramas derivados, nunca capturas falsas.

La herramienta documental LibreOffice no estaba disponible en el runtime Windows;
la revisión utilizó Microsoft Word instalado, exportación PDF y rasterización
local con pypdfium2. Los archivos de `qa/` son material interno de revisión.

## Pendientes para la acreditación completa

- Incorporar capturas auténticas de código, ejecución, BPMN y aplicación.
- Verificar visualmente la traza ya existente de LangSmith: run_id, duración,
  árbol de spans, metadatos y entradas/salidas vacías; adjuntar sus capturas.
- Validar los datos institucionales y de autoría individual antes de presentar.

## Resumen para el video

Reunimos código, diagramas y resultados verificables en un informe de cinco actividades.
Separamos las demos académicas del flujo comercial y explicamos las diferencias con BPMN.
La traza de LangSmith y las capturas auténticas quedan señaladas como evidencia pendiente.
