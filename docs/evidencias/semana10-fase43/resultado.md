# Fase 4.3 — resultado de la segunda ejecución autorizada

Resumen: nueve POST y nueve PATCH recibieron HTTP 202. La primera lectura GET del
run recibió HTTP 403 en la etapa verificar_run; después no hubo más solicitudes.
No reapareció el HTTP 400 de cierre en este intento. Un 403 se clasifica como permisos,
pero sin cuerpo de respuesta no se atribuye a una configuración concreta de la clave.
La duración remota y el run_id siguen sin verificar; no se interpreta esto como
ausencia demostrada de la traza. Puede estar ingerida sin que esta credencial permita leerla.

Para revisión manual en el panel: buscar raíz `consulta`, proyecto `veltri-semana10-demo`,
31/10/2026 entre 09:39:46 y 09:40:03 America/Lima. Confirmar metadata y árbol antes
de presentar capturas. No ejecutar otra demo para localizarla. La siguiente acción
recomendable es revisar acceso de lectura o verificar manualmente la traza existente,
con autorización específica si se requieren nuevas solicitudes externas.

Intento detenido; no existe traza completa verificada.

Pruebas previas: 456 aprobadas, 0 fallos/errores/omitidas; Ruff y secretos OK.
Rotación de clave confirmada expresamente por el usuario. No se guardó el valor.
Estado: detenido_sin_reintento. Intentos de demo: 1.
Run ID verificado: None. Spans verificados: 0.
Opt-in finales apagados: True. Configuración persistente apagada.

## HTTP observado

- POST /runs: 202; exito; crear_span.
- POST /runs: 202; exito; crear_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- POST /runs: 202; exito; crear_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- POST /runs: 202; exito; crear_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- POST /runs: 202; exito; crear_span.
- POST /runs: 202; exito; crear_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- POST /runs: 202; exito; crear_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- POST /runs: 202; exito; crear_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- POST /runs: 202; exito; crear_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- PATCH /runs/{run_id}: 202; exito; cerrar_span.
- GET /runs/{run_id}: 403; permisos; verificar_run.

Primer fallo seguro: {"metodo": "GET", "ruta": "/runs/{run_id}", "estado": 403, "categoria": "permisos", "correlacion": "9e56aa80-aaa3-40a9-a566-665f7d3e5337", "etapa": "verificar_run"}
No se hicieron solicitudes para investigar el error ni se repitió la demo.
Requisito 3 NO acreditado. Un tercer intento requiere autorización independiente.

## Capturas del usuario

- Proyecto veltri-semana10-demo, con el run correspondiente al horario de esta demo.
- Detalle del run: ID, estado y duración; no mostrar configuración de claves.
- Árbol con nueve spans y parentesco, rotulado MockLLM.
- Inputs/outputs vacíos y metadata synthetic/model_mode/scenario.
Si no hay traza verificada, no capturar un fragmento como demostración completa.

No se modificaron agentes, negocio, BPMN, frontend, IGV ni políticas. Sin commits ni Word.

## Video

Validamos un lanzador de un solo uso con cuerpos vacíos y metadata sintética.
Ejecutamos una única demo autorizada y conservamos el resultado real, sin reintentos.
El envío quedó apagado; el estado del requisito depende de la verificación y sus capturas.
