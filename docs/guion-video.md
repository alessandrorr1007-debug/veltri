# Guion del video (práctica calificada)

Una fila por fase. Se completa con la skill `documentar-para-video`.

| Fase | Qué mostrar | Comando | Qué decir | Duración |
|------|-------------|---------|-----------|----------|
| 0 | Entorno agéntico: reglas, workflows, skills | abrir paneles de Antigravity | Cómo se le dio criterio al agente antes de construir | 1 min |
| 1 | Catálogo de 84 SKUs, relaciones, políticas y pruebas de datos | python scripts/verificar.py | Creamos datos de ejemplo, detectamos errores y dejamos pendientes las decisiones comerciales; luego siguen herramientas deterministas | 1 min |
| 2 | Herramientas, pruebas de stock, presupuesto, pago e idempotencia | python -m pytest tests/test_herramientas.py -q | Calculamos con código y datos de ejemplo; los faltantes y pagos sin evidencia siguen pendientes de revisión; después vienen los esquemas tipados | 1 min |
| 3 | Contratos Pydantic, JSON Schema y rechazo de resultados contradictorios | python -m pytest tests/test_esquemas.py -q | Definimos entradas y salidas para evitar datos inválidos y revisiones ocultas; después seguirá el conocimiento RAG | 1 min |
| 4 | Ingesta de corpus sintético, citas exactas y aislamiento por tenant | python -m src.knowledge.ingesta --tenant veltri_tecnologic_pe | Recuperamos información local con fuentes, sin modelo; evitamos mezclar tenants y dejamos la decisión para la siguiente fase | 1 min |
| 5 | Umbrales protegidos, stock agotado con puntuación alta y bandeja HITL | python -m pytest tests/test_decision_hitl.py -q | Una puntuación alta no elimina bloqueos; registramos revisión sin ejecutar ventas; siguen la capa cognitiva y los agentes | 1 min |
| 6 | Diagramas, fábrica única, MockLLM y ocho agentes tipados | python -m pytest tests/test_llm.py tests/test_agentes.py -q | Separamos intención y cálculo: el modelo no modifica precios ni aprueba pagos; después integraremos el grafo | 1 min |
| 7 | Orquestador LangGraph, DLQ local, rutas tipadas y compuerta HITL | python -m pytest tests/test_flujo.py -q | Conectamos los ocho agentes en un grafo acotado sin historial libre: bloqueamos inyecciones antes de entrar y exigimos revisión si faltan datos o se vulneran reglas; sigue la API FastAPI | 1 min |
| 8 | API FastAPI /consulta, contrato ConsultaResponse y sin CDN | python -m pytest tests/test_api.py -q | Exponemos el orquestador mediante POST /consulta garantizando que toda respuesta sea tipada y sin CDN externa; después sigue la interfaz web | 1 min |
| 9 | Interfaz web local: Consola Comercial, HITL y Trazas (sin CDN ni emojis) | uvicorn src.api.main:app --reload | Mostramos la interfaz web operativa en Soles: cotiza en vivo, visualiza la compuerta HITL con aprobación/rechazo y traza los pasos del grafo; sigue la verificación de entrega | 1 min |
| 10 | Motor Comercial Inteligente: Memoria Conversacional, Extremos y Catálogo Visual | python -m pytest tests/test_consulta_comercial.py -q | Atendemos preguntas naturales de catálogo distinguiendo extremos (más cara vs. más barata), recordando el contexto de la charla sin recargar y explorando piezas interactivamente; entrega final validada | 1 min |
| Semana 10, Fase 3 | Opt-in apagado, payload local seguro, árbol observado y pruebas | python scripts/demo_observabilidad.py; python scripts/verificar.py | Instrumentamos una demo sintética sin enviar trazas externas; conservamos el negocio y esperamos autorización para verificar el panel real | 1 min |




| Semana 10, Fase 4 — intento LangSmith | Preflight y registro del único intento | Abrir docs/evidencias/semana10-fase4/resultado-langsmith.md | Validamos privacidad; un cierre recibió HTTP 400 y detuvimos sin repetir. Monitoreo apagado, requisito 3 pendiente | 30 s |

| Semana 10, Fase 4.1 | Comparación de payloads y suite real | python scripts/verificar.py | Conservamos contexto al cerrar spans; 420 pruebas pasan offline y la causa remota sigue sin confirmar | 30 s |
| Semana 10, Fase 4.2 | Diagnóstico HTTP seguro y estados simulados | python scripts/verificar.py | Conservamos el primer error sin cuerpos ni secretos; el segundo envío sigue pendiente de autorización | 30 s |

| Semana 10, Fase 4.3 | Lanzador, diagnóstico HTTP y resultado observado | Abrir docs/evidencias/semana10-fase43/resultado.md | Una ejecución autorizada, sin reintentos; distinguimos persistencia remota de una respuesta 202 | 45 s |

| Semana 10, auditoría final | Matriz, grafo y paquetes reales | Abrir docs/auditoria-final-semana10.md | A1–A8 no son Deep Agents; mostramos tres capas y LangSmith transversal sin ocultar pendientes | 1 min |

| Semana 10, demos académicas | LCEL, interrupt/resume y delegación real | python scripts/demo_academica.py | Ejecutamos tres demos locales con MockLLM; la traza remota requiere verificación visual | 90 s |

| Semana 10, Fase 6 | Word de 16 páginas, figuras, tablas y límites de evidencia | Abrir docs/entrega-semana10/Veltri_Semana10_Informe_Academico.docx | Documentamos las cinco actividades; LangSmith y capturas permanecen pendientes de acreditar | 60 s |


## Mantenimiento del repositorio — 2 de noviembre de 2026

Se inventarió el repositorio y se conservaron las evidencias de Semana 10.
La instalación se consolidó y comprobó sin red en un entorno nuevo.
Mostrar `docs/mantenimiento/limpieza-20261102.md`, los dos requirements principales y los resultados antes/después; la acreditación LangSmith y las capturas siguen pendientes.
