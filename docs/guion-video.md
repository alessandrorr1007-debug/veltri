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



