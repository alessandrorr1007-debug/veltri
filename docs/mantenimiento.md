# Mantenimiento del repositorio

Depuración documental: 2 de noviembre de 2026. Se retiraron del repositorio 140 archivos (131 de documentación, plantillas, duplicados o QA anterior; nueve cachés dentro de la plantilla retirada).

## Retirado y motivo

- `claude/`: 61 archivos de plantilla ya instalada; las reglas y herramientas activas están en `.agents/` y `scripts/`.
- Seis guías/índices antiguos y dos informes de mantenimiento: reemplazados por README, este resumen y la guía unificada de observabilidad.
- 33 archivos de auditoría y preparación anteriores a las demos definitivas: describían estados ya superados; código, pruebas y registros finales conservan la evidencia pertinente.
- 17 salidas QA del Word anterior: sustituidas por `entrega-semana10/qa/langgraph-corregido/` del Word corregido de 17 páginas.
- Cinco duplicados exactos BPMN/diagramas: se verificó igualdad de bytes antes de retirarlos; permanecen los originales `.bpmn` y los diagramas finales.
- 16 índices, extractos temporales y validaciones previas: sustituidos por el expediente final y pruebas vigentes. No se retiraron las ejecuciones remotas originales.

Se simplificaron README y arquitectura, se actualizaron referencias y se eliminaron afirmaciones de fases antiguas que negaban componentes actualmente implementados. El borrado por lotes fue rechazado automáticamente; se realizó la alternativa reversible de traslado fuera del repositorio, conservando cada archivo y su ZIP verificado.

## Protegido y conservado

Código, tests, datos y frontend permanecen idénticos. También el Word corregido, generador, seis figuras, procedencia, BPMN TO-BE/AS-IS, expediente final y registro consumido de LangSmith. Se conservan resultados originales de API, los ocho agentes y HITL, porque documentan ejecuciones reales distintas de las demos académicas.

El grafo comercial corregido tiene 11 nodos operativos, 13 vértices y 20 aristas. Las instantáneas originales del expediente se conservan sin reescribir; no deben confundirse con documentación vigente.

No se tocó la eliminación preexistente del usuario de `GUIA_EXPOSICION.md`, ni secretos, configuración privada, `.git` o almacenamiento persistente. No hubo commits, push ni envíos nuevos a LangSmith.

## Recuperación

Respaldo externo: `C:/Users/aless/AppData/Local/VeltriBackups/segunda-limpieza-20261102-1d4219cc`.

`plan.json` enumera las 140 rutas, motivos y SHA-256. `eliminados.zip` y `retirados/` conservan los archivos; `documentacion-antes.zip` conserva la documentación editada. Para recuperar, extraer solo una ruta después de comprobar que no reemplaza una versión más reciente. El respaldo de la primera limpieza permanece en su ubicación externa.

Los logs de pruebas, comparación del generador e integridad están en ese respaldo. El generador se probó sobre una copia temporal: XML del documento y seis figuras idénticos. Se instalaron sin red python-docx 1.2.0, Pillow 12.3.0 y lxml 6.1.3, ya declarados en requirements-dev.txt; pip check sin conflictos.

Verificación final: `python scripts/verificar.py` aprobó **464 pruebas en 49,27 s**, cero fallos/errores/omitidas, dos advertencias de dependencias; Ruff y escaneo de secretos OK. Las pruebas incluyen LCEL, HITL, Deep Agents y LangGraph. Los 124 archivos protegidos comparados por SHA-256 permanecen idénticos y los enlaces locales de las guías vigentes no están rotos.

## Pendientes de decisión

BPMN AS-IS aporta el proceso previo único y la skill de documentación sigue requerida por GEMINI.md; retirarlos requiere decidir que se abandona esa comparación o procedimiento. Los registros originales del expediente y el QA vigente se conservan por ser evidencia exigida, no por antigüedad. LangSmith sigue pendiente de acreditación visual; HTTP 202 no la demuestra.

## Resumen de tres líneas

Retiramos plantillas, guiones y documentos reemplazados y dejamos instrucciones actuales.
Conservamos el código, el Word corregido y las ejecuciones originales necesarias.
La recuperación y los resultados de verificación quedan fuera del repositorio para no acumular informes.
