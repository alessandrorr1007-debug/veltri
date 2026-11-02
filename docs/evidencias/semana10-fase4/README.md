# Veltri — Semana 10, Fase 4 (expediente parcial)

Fecha de preparación y verificación: 31/10/2026, America/Lima. Commit base: 591670b,
con instrumentación local de Fase 3 sin publicar. No se generó Word.

## Qué está obtenido

- API local real en http://127.0.0.1:8000, MockLLM, monitor externo apagado.
- Cuatro operaciones HTTP 200: portada, catálogo, stock sintético y cotización S/3500.
  Entradas, resultados y tiempos medidos están en registros/api-local-entradas-salidas.json.
- Caso observado: CPU-AMD-5500 sin stock; exige revision_humana y sugiere alternativas.
  A1 interpreta y A5 consulta stock. Se cotejó la respuesta HTTP con la demo del
  Orquestador, que produjo nueve spans usando capturador local: NO es LangSmith.
- La revisión desde código pasó de pendiente a correccion_solicitada. Revisor sintético,
  sin autenticación humana; ninguna resolución ejecutó negocio. No hay interrupt,
  checkpoints ni reanudación nativa.
- Pruebas ejecutadas el 31/10/2026: 419 aprobadas, cero fallos, errores y omitidas;
  dos advertencias de dependencias. Ruff y secretos OK. Logs y JUnit en pruebas/.
- Se preservan los registros de 24 casos de A1–A8 de Fase 3 (29/10/2026), sin
  atribuirlos a una nueva ejecución ni a modelos reales.
- Se copian los diagramas existentes y se obtiene Mermaid directamente del grafo
  compilado. El SVG se reutiliza de Fase 3. El BPMN es una copia exacta del original.

## Qué falta

La carpeta capturas/ no contiene capturas auténticas aún: el control de Edge no pudo
verificar su URL en los intentos anteriores. No se reemplazan con imágenes generadas,
renders de una interfaz inventada ni ilustraciones de paneles de LangSmith.
El estado detallado de las trece evidencias está en tabla-evidencias.json y .csv.

Las evidencias de LCEL son parciales: .invoke de un grafo Runnable, fábrica de modelo
y contratos Pydantic; no hay cadenas LCEL explícitas. BPMN y LangGraph tienen
compatibilidad parcial. Persisten las discrepancias UI/aprobación, IGV y políticas
detectadas anteriormente; no se corrigieron ni se ocultaron. Las cuatro etapas
Build/Test/Deploy/Monitor son provisionales hasta confirmar material del profesor.

## Propuesta de conexión externa: aún NO autorizada

Proyecto fijo veltri-semana10-demo; endpoint propuesto https://api.smith.langchain.com
(región US, pendiente de confirmar). Una sola demo sintética de stock, MockLLM.
Datos a enviar: UUID aleatorios, nombres cerrados, relaciones padre/hijo, tiempos
reales y metadata fija synthetic=true/model_mode=mock/scenario=stock_demo.
Inputs y outputs vacíos; error fijo operation_failed cuando corresponda.
La clave se utilizaría solo para autenticar el SDK, nunca como dato de la traza
ni en capturas o archivos de evidencias. No enviar mensajes, tenants, pagos,
selecciones, SKUs ni documentos RAG. Ambos opt-in se desactivarían al terminar.
No se ha accedido a LangSmith, no hay run_id remoto y falta autorización expresa.
Configuración sin secretos: registros/configuracion-langsmith-PENDIENTE-AUTORIZACION.json.
Procedimiento reproducible: ../../observabilidad.md.

## Capturas pendientes: instrucciones para obtenerlas

1. Abrir la URL local anterior en Edge, con barra de direcciones visible; capturar
   la portada antes de enviar una consulta y el catálogo sintético (C06).
2. Enviar «Consultar stock de CPU-AMD-5500»; capturar entrada y resultado, distinguiendo
   el estado mostrado por UI del contrato JSON del backend. No afirmar aprobación real.
3. Abrir el código citado en registros/componentes-lcel-fuentes.txt (C01), el Mermaid
   y SVG reales (C02), y el BPMN original en un modelador disponible (C03).
4. Mostrar los registros antes/después de la revisión desde código (C04/C05), sin
   rotularlos como una pantalla de supervisión que la UI no implementa.
5. Mostrar las ocho clases y registros de casos conservando fecha y modo MockLLM
   (C07), y la salida real del verificador (C08).
6. C09 permanece pendiente: SOLO tras autorizar envío, verificar el run en LangSmith
   y capturar ID, duración, resultado técnico y spans. No usar la captura local como sustituto.
7. C10–C13 requieren confirmar la clasificación académica; una API local no acredita
   despliegue público ni una ejecución real del proveedor del modelo.

## Preparación del futuro informe Word

Los cinco requisitos tienen fuentes localizadas y límites expresos. Antes de redactar,
faltan PNG auténticos, run LangSmith autorizado/verificado y material del profesor
para la denominación de las etapas y «dev agentes». Numerar figuras solo cuando
existan; acompañarlas de código, fuente, fecha y estado. No generar todavía Word.

## Guion breve para video

Probamos Veltri localmente con información sintética y conservamos sus resultados verificables.
Organizamos pruebas, grafo, agentes y revisión desde código sin modificar las reglas comerciales.
Las capturas y la traza externa quedan pendientes de acceso visual y autorización, respectivamente.

## Resultado del intento externo autorizado del 31/10/2026

Este resultado sustituye el estado anterior de envío pendiente: hubo un intento autorizado, detenido por HTTP 400 y sin reintentos. Ver [resultado-langsmith.md](resultado-langsmith.md). No hay traza completa verificada.
