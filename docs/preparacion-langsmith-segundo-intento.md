# Fase 4.2 — preparación del segundo intento, sin envío

Fecha: 31/10/2026. La autorización de esta fase es exclusivamente local.
No se ha hecho un segundo envío ni se ha conectado con una cuenta LangSmith.
El HTTP 400 histórico continúa sin causa confirmada; no se recuperó su respuesta.

## Cambio mínimo

`src/core/diagnostico_http.py` incorpora TransporteDiagnostico, utilizado únicamente
cuando la fábrica ya supera las compuertas existentes. Construirlo no abre sockets.
No altera agentes, API, BPMN, reglas, catálogo, IGV, garantía o frontend.
La corrección de Fase 4.1 conserva proyecto, padre e identificadores en el cierre.

Los únicos campos del registro son metodo, ruta, estado, categoria, correlacion y
etapa. La correlación es un UUID aleatorio nuevo por transporte; no se deriva del
tenant, mensaje o pedido. Las rutas dinámicas se registran como `/runs/{run_id}`;
se omiten query strings y UUID del path. Etapas: crear_span, cerrar_span, verificar_run
y validar_destino. Los registros permanecen locales y no se agregan a las trazas.

Categorías cerradas: exito, solicitud_invalida, autenticacion, permisos, limite,
servidor, http_no_exitoso, timeout, conexion y configuracion. No se accede al texto
de error del servidor. No se guardan cabeceras, cuerpos, exceptions originales,
mensajes, variables de entorno, tenants, SKUs ni credenciales.

El primer fallo se conserva en primer_fallo y en la lista. Los accesos posteriores
se bloquean sin nuevos registros HTTP ni red. La excepción pública usa texto fijo;
no reemplaza el estado primario por transporte_detenido en los registros.
Se desactivan reintentos del adaptador y redirects. El flujo normal de negocio
conserva su tolerancia a telemetría caída: puede terminar sin traza completa. El
resultado comercial jamás prueba éxito del monitoreo.

`ejecutar_demo` admite un colector diagnóstico opcional solo desde código de confianza.
La salida CLI incluye diagnostico_http y monitoreo_fallo; la API no abre sesiones
ni permite configurar este colector mediante HTTP. Con opt-in apagado no se crea
cliente y la lista permanece vacía.

## Pruebas y limitaciones

Se simulan 200/202/400/401/403/429/500 en creación y cierre; además timeout, conexión,
destino inválido y redirect. Se verifica conservación del primer error, una sola
llamada en los fallos, ausencia de canarios en registros y vínculo con el SDK real
instalado, con transporte de red sustituido. Se conserva la prueba de contexto
de Fase 4.1 y las pruebas de privacidad/opt-in previas.

La primera ejecución de la suite durante el desarrollo tuvo 14 fallos de tests nuevos:
el fixture esperaba allow_redirects dentro del adaptador, pero Session.send lo consume.
Se corrigió esa expectativa y se añadió una prueba conductual de no seguir un 302.
No se relajó ninguna prueba preexistente ni una regla comercial.

Esa prueba adicional detectó que Session.send procesa preparación de redirects aun
con allow_redirects=false, antes de devolver la respuesta al logger. Se eliminó
ese procesamiento intermedio usando directamente el adaptador con reintentos en 0.
Así el estado primario 302 se registra antes de cualquier tratamiento de redirect.
Los 26 casos del módulo de diagnóstico pasan con esta implementación.

Un estado y una categoría NO revelan el detalle interno de un 400. Si esos campos
no alcanzan, se informará la limitación. No se habilitará captura cruda para obtener
una explicación. Las respuestas simuladas no acreditan aceptación remota.

## Procedimiento futuro: requiere autorización nueva

1. Revisar esta guía, los tests, payloads sintéticos y permisos/retención del proyecto.
   Confirmar clave local vigente sin mostrarla y ambos opt-in inicialmente en 0.
   No utilizar .env.txt ni subir archivos de secretos. Si una clave expuesta no fue
   reemplazada, revocarla antes de solicitar envío.
2. Autorizar expresamente UNA demo a proyecto veltri-semana10-demo, endpoint US
   https://api.smith.langchain.com, MockLLM, fixture fijo, inputs/outputs vacíos y
   metadata synthetic=true/model_mode=mock/scenario=stock_demo.
3. Antes de enviar, usar un registro persistente de autorización separado del primer
   intento, que impida ejecutar dos veces el comando. El runner externo anterior NO
   debe reutilizarse: tiene su autorización consumida y otro transporte. Preparar y
   revisar ese lanzador cuando se autorice; no ejecutar manualmente varias veces.
4. En un proceso hijo acotado, activar temporalmente VELTRI_TRACING_ENABLED=1,
   VELTRI_TRACING_ALLOW_EXTERNAL=1 y VELTRI_TRACING_SYNTHETIC_ONLY=1. Mantener
   USE_MOCK_LLM=1 y flags globales LANGSMITH_TRACING/LANGCHAIN_TRACING_V2=false.
   No modificar el archivo .env para activar; conservar allí ambos flags en 0.
5. Invocar una sola vez `scripts/demo_observabilidad.py --enviar`, con salida local
   capturada. Este comando NO se ejecutó en Fase 4.2. Revisar primero diagnostico_http
   y monitoreo_fallo: ante un fallo, detener el procedimiento sin otra demo ni lecturas
   remotas adicionales, reportando método/ruta/estado/categoría/etapa.
6. Si todos los cierres fueron aceptados, desactivar ambos opt-in inmediatamente.
   Efectuar únicamente lecturas autorizadas para obtener el run_id de la raíz consulta
   en el proyecto y rango horario de la demo; cotejar los nueve spans, UUID, padres,
   trace_id, tiempos de inicio/fin y duración. El logger admite GET /runs/{run_id};
   otras rutas requieren un cliente de lectura separado y previamente revisado.
   No registrar ni capturar datos de otros proyectos. UUID generados localmente o
   respuestas HTTP 202 no equivalen por sí solos a un run remoto verificado.
7. Capturar el panel con run_id, duración, árbol y metadata sintética, cuerpos vacíos.
   Si Computer Use sigue bloqueado, entregar instrucciones de captura manual sin
   eludirlo. No afirmar éxito académico completo sin verificar el run y sus evidencias.
8. En finally, incluso ante error, cerrar transporte/proceso y verificar ambos opt-in
   en 0. Conservar solo el resumen seguro y los campos permitidos del run verificado.
   No ejecutar una segunda demo para comprobar la desactivación.

## Recomendación

La instrumentación puede someterse a revisión para autorizar una prueba remota acotada,
con la condición operativa del lanzador de un solo uso del paso 3. Esta fase prepara
el diagnóstico; no garantiza resolver el 400 ni autoriza el envío. El requisito 3
sigue pendiente. No se crearon commits, despliegues ni Word.

## Video

Preparamos un diagnóstico HTTP que conserva el primer fallo sin guardar datos sensibles.
Lo probamos localmente con estados simulados y mantuvimos el monitoreo apagado.
La segunda ejecución sigue pendiente de autorización y de verificar una traza auténtica.

## Resultado final de verificación

`python scripts/verificar.py`: 446 aprobadas, 0 fallos, errores u omitidas; 2 advertencias de dependencias. Ruff y escaneo de secretos OK. 26 casos adicionales respecto de 420. 15 procesos auditados, cero intentos externos y 40 archivos comerciales/protegidos sin cambios. Registros: [verificar.log](evidencias/semana10-fase42/verificar.log) y [resultado-local.json](evidencias/semana10-fase42/resultado-local.json).
