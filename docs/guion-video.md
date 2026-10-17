# Guion del video (práctica calificada)

Una fila por fase. Se completa con la skill `documentar-para-video`.

| Fase | Qué mostrar | Comando | Qué decir | Duración |
|------|-------------|---------|-----------|----------|
| 0 | Entorno agéntico: reglas, workflows, skills | abrir paneles de Antigravity | Cómo se le dio criterio al agente antes de construir | 1 min |
| 1 | Catálogo de 84 SKUs, relaciones, políticas y pruebas de datos | python scripts/verificar.py | Creamos datos de ejemplo, detectamos errores y dejamos pendientes las decisiones comerciales; luego siguen herramientas deterministas | 1 min |
| 2 | Herramientas, pruebas de stock, presupuesto, pago e idempotencia | python -m pytest tests/test_herramientas.py -q | Calculamos con código y datos de ejemplo; los faltantes y pagos sin evidencia siguen pendientes de revisión; después vienen los esquemas tipados | 1 min |
| 3 | Contratos Pydantic, JSON Schema y rechazo de resultados contradictorios | python -m pytest tests/test_esquemas.py -q | Definimos entradas y salidas para evitar datos inválidos y revisiones ocultas; después seguirá el conocimiento RAG | 1 min |
