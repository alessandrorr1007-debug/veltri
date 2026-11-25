# Reglas de desarrollo de Veltri Tecnologic

Veltri es una plataforma local de demostración multiempresa para cotizar PCs en soles con LangGraph, FastAPI y una interfaz web local. La [arquitectura](docs/arquitectura.md) documenta los contratos, el flujo comercial y las demostraciones académicas.

## Invariantes (no se rompen en ninguna tarea)

1. **Un solo acceso al modelo.** Todo modelo de lenguaje se obtiene con `get_llm()` (`src/core/llm.py`). El nombre del modelo viene de `.env` (`LLM_MODEL`), nunca fijo en el código. Para pruebas y demos sin red se usa el `MockLLM`.
2. **La aritmética va en código.** Precios, stock, compatibilidad de socket, cuello de botella, TDP, holgura de fuente, presupuesto, IGV y totales se calculan en `src/tools/`. El LLM nunca calcula ni inventa una cifra: solo interpreta la consulta y redacta.
3. **Ninguna rama lee texto libre del LLM.** El enrutamiento del grafo depende de campos tipados (Pydantic), no de parsear frases.
4. **Una probabilidad nunca concede autorización.** Si falla un invariante de negocio (sin stock, pago discordante, socket incompatible, sobre presupuesto), se exige revisión humana (HITL) aunque la probabilidad sea alta.
5. **Seguridad antes del grafo.** Todo mensaje pasa por el filtro anti prompt injection antes de entrar al orquestador. Los datos personales (DNI, RUC, teléfono, correo) no se indexan ni aparecen en logs ni trazas.
6. **Todo acceso al almacén RAG lleva tenant explícito.** Sin tenant no hay recuperación.
7. **La API responde siempre con el contrato `ConsultaResponse`** (JSON tipado). Nunca prosa libre.
8. **Pedidos idempotentes.** El hash SHA-256 se calcula con `cliente|productos|cantidad|canal`, sin marcas de tiempo ni IDs generados.
9. **Archivos protegidos.** No edites `src/core/umbrales.py` ni `evals/linea_base.json` sin autorización explícita del usuario en esa misma conversación. Un hook de Git bloquea esos cambios.
10. **Secretos solo en `.env`.** Nunca en código, docs, tests, datos ni capturas. `.env` está en `.gitignore`.

## Operación local y alcance

- Veltri funciona exclusivamente de manera local. No contrates ni aprovisiones servicios cloud, hosting, bases de datos externas ni APIs de pago. AWS en la semana 12 será únicamente una propuesta académica.
- Valida sesión, empresa activa y permisos en el servidor antes de vincular servicios comerciales. Las peticiones, fuentes RAG y escrituras deben conservar el ámbito autorizado. Usa datos sintéticos en las demos.
- Prioriza bajo consumo de CPU, RAM y almacenamiento. Usa MockLLM en pruebas y demostraciones sin costo y mantén desactivado el envío externo de trazas.
- Trabaja exclusivamente en `main`. No generes guías para videos, documentos de progreso y archivos redundantes.

## Desarrollo y entrega

- Sigue el [proceso SDD](docs/arquitectura.md#especificaciones-y-trazabilidad-sdd) para requisitos, aceptación, diseño, tareas, pruebas y verificación. Mantén sus referencias rastreables.
- Usa Python 3.12 o superior para el código. Reproduce el entorno de verificación con las dependencias fijadas y CPython 3.14.
- Antes de implementar un agente, define su dominio, herramienta, entrada y salida tipadas, diagrama y punto de integración en la arquitectura. Reutiliza `BaseAgent` y cubre casos válidos, límite y de fallo con MockLLM.
- Revisa `evals/casos_dorados.json` al cambiar el comportamiento. Compara CP-1 a CP-7 con los resultados de API, flujo y herramientas. Una fuente, SKU o motivo incorrectos cuentan como fallo. Valida cifras con las herramientas y conserva la línea base protegida.
- Para cambios de decisiones, define opción, evidencia de dominio, probabilidad y confianza en Pydantic. Prueba las tres zonas de decisión y los bloqueos forzados por invariantes. Lee los umbrales de `src/core/umbrales.py`.
- Comprueba aislamiento por tenant, bloqueo previo al grafo, ausencia de datos privados en RAG y trazas y errores ajustados al contrato cuando cambies entradas, datos o API. Mantén secretos y datos privados fuera del repositorio.
- Antes de entregar, ejecuta `python scripts/verificar.py` y comunica el resultado real. Revisa el diff, instala el hook con `python scripts/instalar_hooks.py` y publica solo con autorización del usuario y controles aprobados.
- Instala solo dependencias necesarias. Actualiza la documentación técnica afectada y prioriza código funcional, pruebas y seguridad.

## Interfaz

- Reutiliza los tokens de `frontend/css/tokens.css`, un acento de marca, tipografía local y el conjunto local de iconos vectoriales. Evita emojis, CDN y efectos que dificulten la lectura.
- Mantén contraste WCAG AA, etiquetas, foco visible y navegación con teclado. Comprueba vistas móviles y de escritorio, objetivos táctiles de 40 px, movimiento reducido y los estados de carga, vacío, error, éxito y deshabilitado.
- Mantén los contratos JSON y endpoints vigentes. Presenta precios y existencias como ejemplos sintéticos.
