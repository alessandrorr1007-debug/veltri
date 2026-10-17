# Decisión y revisión humana — FASE 5

Compuerta determinista sobre evidencia tipada, sin agentes, LLM, grafo, API ni
interfaz. No cambia ConsultaResponse 1.0-demo ni los JSON de datos. Umbrales y
línea base protegidos permanecen intactos. Los nuevos contratos están en
src/schemas/decision.py y src/schemas/hitl.py, exportados en docs/contratos/.

## Qué decide
SolicitudDecision recibe opcion, p, c, origen_puntuacion y evidencia discriminada
por tipo. Las opciones son informar, consultar_stock, cotizar,
validar_compatibilidad, comparar_pago y registrar_borrador. Cada una exige su tipo
de evidencia: fuentes informativas o el resultado Pydantic de la herramienta
correspondiente. No interpreta texto del LLM, fragmentos RAG, frases ni mensajes.
Rechaza evidencia de otro dominio, campos extra, NaN, infinitos, valores fuera de
[0,1], booleanos y cadenas en los puntajes.

En esta fase p y c solo admiten origen prueba_no_calibrada: son entradas sintéticas
de pruebas, no probabilidades medidas ni confianza calibrada. No se llama a
get_llm ni se implementa MockLLM todavía; se prueban funciones puras directamente.
La producción y calibración de puntajes quedará para la fase cognitiva.

## Precedencia y salidas
core/criterios.py lee TAU_AUTO y TAU_REV de core/umbrales.py. No replica valores.
1. Si existe un bloqueo, destino revision_humana sin importar p.
2. Sin bloqueos, p >= TAU_AUTO da destino ejecutar.
3. Sin bloqueos, TAU_REV <= p < TAU_AUTO da revision_humana.
4. Sin bloqueos, p < TAU_REV da escalar.

Un bloqueo con p bajo conserva revisión humana y sus motivos; no se pierde por
la ruta de baja puntuación. c se registra, pero no modifica la ruta porque no hay
un umbral de confianza definido. Esa decisión es explícita y debe revisarse antes
de usar puntuaciones reales; no se inventa un umbral adicional.

ResultadoDecision conserva opcion, p, c, origen, destino, hitl_requerido,
bloqueos/motivos, fuentes y hash_evidencia. accion_ejecutada siempre false.
Ejecutar significa ruta propuesta para integración futura, NO una venta ejecutada,
una autorización de pago ni una ejecución automática de herramientas.

Los bloqueos se derivan del resultado tipado: faltantes con SKU, exceso de
presupuesto, conflictos técnicos, fichas y BIOS sin verificar, pago no conciliado
y borrador de pedido. Incluso una cotización sin conflictos conserva la revisión
por sus datos sintéticos. Igualar montos no elimina la falta de evidencia bancaria.
Solo información y stock disponible pueden producir una ruta automática en la demo.

Los puntajes no acreditan la veracidad de la evidencia. Los resultados deben
proceder de herramientas ejecutadas en un contexto confiable y revalidarse antes
de efectos de negocio futuros. Pydantic no autentica el origen ni comprueba que
un snapshot de stock siga vigente. Decide revalida modelos para detectar cambios
en listas/diccionarios después de construirlos; la huella fija la evaluación.

## Bandeja HITL local
core/hitl.py implementa BandejaRevision, en memoria, aislada por tenant explícito.
No usa rutas ni tenant por defecto. Encolar vuelve a ejecutar decide; no recibe
una decisión preaprobada. La misma solicitud produce un ID SHA-256 por tenant y
un solo registro, con bloqueo por instancia para llamadas concurrentes. El ID
incluye tenant y la huella de toda la evaluación; un cambio de p, c o evidencia
crea otra revisión. El orden de listas forma parte de esa instantánea.

obtener y listar devuelven copias revalidadas. Una revisión de otro tenant es
indistinguible de una inexistente. El contrato vuelve a calcular la decisión para
asegurar que corresponde a la solicitud conservada.

Estados: pendiente para la zona de revisión; escalada para baja puntuación sin
bloqueos; estados finales aprobada_demo, rechazada o correccion_solicitada.
resolver exige ResolucionRevision con acción, alias sintético demo_ y motivo
enumerado. No hay comentarios libres ni identidades reales en la bandeja.

Propuestas de funcionamiento local:
- aprobar_demo solo cierra revisiones sin bloqueos, de información/stock; no
  ejecuta acciones ni modifica la evidencia o ConsultaResponse.
- Una solicitud bloqueada o escalada necesita corrección/nueva evaluación antes
  de aprobarse. No hay opción para saltar el stock, socket, presupuesto o pago.
- Repetir una resolución idéntica es idempotente. Cambiar una resolución final se
  rechaza. Una corrección se presenta como nueva solicitud; no se borra el historial.
- Alias de revisor representa una acción de prueba del llamador, NO autentica
  una persona ni demuestra intervención humana real. Roles, identidad verificada,
  asignación de responsables, SLA, persistencia y auditoría durable quedan pendientes.

No es una cola de producción: se pierde al reiniciar y no coordina procesos
separados. El tenant también debe venir de identidad autorizada en la futura API.
Ninguna revisión se indexa en RAG. No hay notificaciones ni mensajes externos.

## Ejecución y pruebas
Sin nuevas dependencias; se usa requirements-fase4.txt.
```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest tests/test_decision_hitl.py -q
python scripts/exportar_esquemas.py
python scripts/verificar.py
```

Pruebas cubren fronteras de los umbrales, puntajes inválidos, evidencia del dominio
correcto, bloqueo con p alta o baja, stock agotado CP-3, presupuesto CP-4, pago
CP-5, fichas sintéticas y borradores. También aislamiento, idempotencia, copias,
concurrencia, resoluciones finales y prohibición de aprobar bloqueos. CP-1 a CP-7
siguen sin constituir flujos end-to-end. No hay grafo para probar el filtro de CP-2;
seguridad conversacional y DLQ quedan pendientes de integración.
