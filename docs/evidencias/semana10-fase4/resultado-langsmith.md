# Resultado de la única ejecución autorizada de LangSmith

Fecha: 31/10/2026, 08:38:07–08:38:09 America/Lima (13:38 UTC).
Proyecto veltri-semana10-demo, endpoint US autorizado, configuración MockLLM.

La comprobación previa sin red validó 18 cuerpos serializados del SDK: inputs y
outputs vacíos, metadata sintética cerrada, sin credenciales ni datos comerciales.
Se comprobaron ambos opt-in y se activaron únicamente en el proceso de la demo.

Se hizo UN intento. Dos POST /runs recibieron HTTP 202. El primer PATCH de cierre
recibió HTTP 400. Se bloquearon las operaciones posteriores y no se repitió el envío.
El error secundario transporte_detenido refleja ese bloqueo; la respuesta primaria
que impidió terminar fue HTTP 400. No se conservó el cuerpo de error del servidor,
por lo que su causa interna queda sin diagnosticar. No se fabricó una explicación.

No se obtuvo run_id de una traza completa verificada, ni duraciones remotas ni
spans autenticados recuperados por lectura. Los UUID de las solicitudes no se
presentan como prueba de persistencia remota. La aplicación de negocio no terminó
su consulta: el bloqueo ocurrió durante el cierre del span de seguridad.

Ambos opt-in quedaron en 0 en el proceso; el archivo .env conservó su configuración
apagada. La clave no se copió al código ni a este expediente. No se modificaron
agentes, frontend, BPMN ni lógica comercial. No se generó Word.

El requisito 3 NO está acreditado. Una nueva ejecución exige autorización adicional.
Antes de reenviar hay que diagnosticar el rechazo 400. No capturar una traza parcial
como si fuera una demostración completa. Tras resolverlo y verificar un run auténtico,
las capturas necesarias serán: proyecto con run visible; detalle con ID/duración;
árbol de spans; metadata sintética e inputs/outputs vacíos, sin mostrar credenciales.

Resumen de tres líneas para video:
Validamos los datos y realizamos un único intento de monitoreo con MockLLM.
LangSmith rechazó un cierre con HTTP 400 y detuvimos el flujo sin repetirlo.
El envío quedó apagado; falta diagnosticar el error y verificar una traza completa.
