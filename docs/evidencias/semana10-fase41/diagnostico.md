# Fase 4.1 — diagnóstico local y recuperación de continuidad

Fecha: 31/10/2026. Base Git: 591670b; árbol con cambios locales de fases anteriores.
No se revirtió ni reconstruyó el proyecto. No se conectó a LangSmith ni se consultó
una cuenta remota. No se hicieron commits ni se generó Word.

## Hechos históricos y límites

El registro conservado muestra dos POST https://api.smith.langchain.com/runs con
HTTP 202 y un PATCH https://api.smith.langchain.com/runs/3a267b0f-6726-4f18-bf24-825507efa35b
con HTTP 400. Es el primer cierre, correspondiente a seguridad según el orden del
driver. No se guardaron cuerpo de respuesta, cabeceras ni payload histórico íntegro.
No se conocen los UUID del padre histórico ni sus tiempos exactos. El código secundario
transporte_detenido proviene de la guarda del driver después del 400.

Por tanto, **la causa exacta del rechazo remoto sigue sin determinarse**. Los archivos
sdk-antes-payloads.json y sdk-despues-payloads.json son reconstrucciones locales con
otros UUID y tiempos, no capturas del envío original ni respuestas del backend.

## Estado encontrado tras la interrupción

- src/core/observabilidad.py ya contenía un cambio defensivo en update_run: nombre,
  tipo chain, inicio original, padre, session_name fijo, tags vacíos y metadata fija.
- tests/test_observabilidad.py incorporaba test_cierre_sdk_conserva_contexto_de_creacion.
  Se conservó su fallo previo en regresion-antes.log: el padre de un hijo era null.
- La reproducción posterior ya había producido nueve altas y nueve cierres correctos
  respecto de ese contrato local. Faltaba cerrar la verificación de regresión completa.
- El helper y los tests son archivos aún sin seguimiento en Git: git diff contra HEAD
  por sí solo no muestra sus cambios. Se inspeccionaron directamente, sin revertirlos.
- La configuración, agentes, grafo, documentación y .env.example tienen otros cambios
  de fases anteriores. No se atribuyen todos a este diagnóstico.

## Reproducción sin red y análisis estructural

Se usó langsmith 0.14.11 instalado, Pydantic 2.14.1, MockLLM y una credencial ficticia.
requests.Session.request fue sustituido por un transporte que devuelve 202 sintético.
Una guarda adicional bloquea TCP/DNS/UDP externos y reemplaza la lectura del .env
del proyecto por configuración ficticia. La clave real no participa en las pruebas.

Antes: nueve altas/nueve cierres; todos los UUID, IDs de URL/cuerpo, trace_id,
dotted_order y tiempos eran coherentes. Cierre inicial reconstruido contenía:

```json
{
  "id": "UUID_DEL_HIJO",
  "name": null,
  "run_type": null,
  "trace_id": "UUID_DE_LA_RAIZ",
  "parent_run_id": null,
  "dotted_order": "ORDEN_RAIZ.ORDEN_HIJO",
  "tags": null,
  "extra": null,
  "session_id": null,
  "session_name": null,
  "end_time": "FIN_ISO8601_UTC",
  "outputs": {}
}
```

Es una representación con marcadores explicativos: los JSON adyacentes conservan
el cuerpo completo de la reproducción con UUID y tiempos reales de la simulación.
No hubo events ni attachments. Cada fin es posterior o igual al inicio; el orden
incluye los UUID de raíz/hijo y los prefijos coinciden con su jerarquía de creación.
No se encontró un ID mal formado o diferente entre creación y cierre en la reconstrucción.

Después: los nueve cierres preservan nombre, tipo, inicio original, trace_id,
dotted_order, padre y proyecto. Inputs/outputs siguen vacíos y metadata constante.
El padre de la raíz sigue siendo null correctamente. session_id sigue null porque
se identifica el proyecto por session_name; no se inventa el UUID remoto del proyecto.
No se eliminan indiscriminadamente todos los null ni se manipula el SDK instalado.

## Hipótesis ordenadas por evidencia, no causas demostradas

1. Diferencia en contexto del PATCH: ausencia de proyecto y padre nulo en hijos.
   Reproducida localmente, pero el propio SDK documenta resolución de actualizaciones
   por run_id cuando no se nombra proyecto. La omisión no demuestra por sí sola error.
   Posible interacción con validación, enrutamiento o alcance de credencial del servidor;
   no se verificó el tipo/permisos de la clave ni el backend.
2. Interpretación de null en name/run_type/extra/tags: la versión instalada los emite.
   Una validación remota estricta podría rechazarlos; no tenemos ese mensaje ni una
   especificación local que demuestre tal rechazo. No se generó un 400 ficticio para
   presentar esta hipótesis como reproducida contra el servidor real.
3. Resolución de un run aún en ingestión: POST 202 significa aceptación en cola;
   no acredita disponibilidad completa. Es una alternativa sin evidencia decisiva.
4. UUID/tiempos/dotted_order inválidos: menos apoyada; pasan todas las comprobaciones
   locales. La autenticación general tampoco parece la explicación principal tras
   dos 202, pero no se descartan permisos específicos de actualización sin respuesta.

## Corrección defensiva mínima conservada

src/core/observabilidad.py, llamada update_run dentro de span: conservar el contexto
que ya se pasó a create_run, usando únicamente nombres cerrados y atributos sintéticos.
Compatible con la firma del SDK instalado: name/run_type/start_time son parámetros
explícitos; parent_run_id/session_name son kwargs consumidos por update_run.

Esto mejora coherencia y hace comprobable el contrato, pero **no se declara arreglado
el 400 remoto**. No se actualizaron dependencias, nodos, herramientas ni reglas.

La nueva prueba primero falló con el código anterior y luego se ejecuta en la suite
final. El transporte simulado inspecciona el cuerpo que produce realmente el SDK;
su respuesta 202 no equivale a validación del esquema interno del servidor.

## Seguridad y riesgos pendientes

Se mantienen ambos opt-in apagados, sesiones sintéticas de confianza, claves excluidas
de repr/dump, errores fijos y prohibición de habilitar por HTTP. No se capturan args,
mensajes, tenants, SKUs, pagos, adjuntos ni resultados comerciales en los spans.
Pruebas existentes comprueban canarios, concurrencia, idempotencia y fallos de telemetría.

.env existe y tiene una clave configurada, comprobada solo por presencia. Sus dos
flags siguen en 0. No se comprobó remotamente ni se puede certificar su rotación.
Si la clave compartida en el chat no fue reemplazada, debe revocarse. .env está
ignorado; .env.txt sigue sin seguimiento y sin protección de Git: no añadirlo a commits.
No se copió ni mostró su contenido durante el diagnóstico.

Antes de una eventual segunda ejecución conviene aprobar un mecanismo de diagnóstico
de errores que conserve solo estado HTTP y campos de error explícitamente permitidos,
sin cuerpo crudo, claves, headers o stack. El runner anterior sobrescribe el error
primario con transporte_detenido y pierde ese detalle. No se modificó ni reejecutó.

Es razonable solicitar autorización para una segunda prueba controlada después de
revisar esta evidencia y definir esa captura segura de errores; no es una garantía
de éxito remoto. No efectuar reintentos automáticos. Requisito 3 sigue pendiente.

## Referencias oficiales consultadas

- [API de actualización](https://docs.langchain.com/langsmith/smith-api/runs/update-a-run):
  modificar campos del run con PATCH; la referencia no prueba el motivo del 400 observado.
- [Trazado REST](https://docs.langchain.com/langsmith/trace-with-api): creación y cierre,
  jerarquía por parent_run_id; POST es distinto de una verificación posterior del run.
- [Firma de update_run](https://reference.langchain.com/python/langsmith/client/Client/update_run).
- Fuente instalada .venv/Lib/site-packages/langsmith/client.py, update_run y
  _update_run_non_batch; _internal/_addressing.py explica resolución por ID en updates.

## Verificación final

`python scripts/verificar.py`: **420 aprobadas, 0 fallos, 0 errores, 0 omitidas**; 2 advertencias de obsolescencia de dependencias. Pytest: 41.05 s; verificador: 53.018 s. Ruff OK; escaneo de secretos sin hallazgos. Los 419 casos previos se mantienen y se añade una prueba. Salida real en verificar.log y pytest-suite.xml.

Se auditaron 9 procesos con cero intentos externos. Se compararon 40 archivos de agentes, negocio, UI, datos, BPMN y protegidos: sin cambios respecto al inicio de Fase 4. No se hizo un segundo envío.

Archivos de implementación afectados por Fase 4.1: src/core/observabilidad.py y tests/test_observabilidad.py. Se completó documentación en esta carpeta, docs/observabilidad.md, docs/guion-video.md y el inventario. El resto del árbol sucio precede a este diagnóstico.

Para video: reproducimos localmente la diferencia de contexto al cerrar spans.
Conservamos ese contexto y pasaron 420 pruebas sin conexiones externas.
El HTTP 400 histórico sigue sin causa confirmada y no repetimos el envío.
