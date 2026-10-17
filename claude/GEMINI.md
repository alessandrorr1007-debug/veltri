# Veltri Tecnologic: reglas permanentes del agente

Proyecto: sistema multiagente (LangGraph) que cotiza PCs, valida compatibilidad técnica, concilia pagos y registra pedidos para una tienda de hardware en Lima, Perú (precios en Soles, S/). Sigue la arquitectura por capas del curso: orquestador, capa de decisión, agentes por dominio (D1 a D4), almacén de conocimiento (RAG), herramientas y gobernanza.

Lee este archivo al inicio de cada sesión. Estas reglas no se negocian ni se relajan para "avanzar más rápido".

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

## Método de trabajo

- Trabaja por fases pequeñas y espera mi "continúa" entre una y otra.
- Antes de crear un agente nuevo, usa `/agente-nuevo`: primero el diagrama y el contrato, luego el código.
- Antes de dar algo por terminado, ejecuta `python scripts/verificar.py` y muéstrame la salida real. No afirmes que pasa sin correrlo.
- Al cerrar cada fase, usa la skill `documentar-para-video`: resumen de 3 líneas en lenguaje simple.
- Las pruebas de lógica usan el `MockLLM`; no dependen de la red ni gastan cuota.
- Una respuesta correcta con la cita o fuente equivocada cuenta como fallo.

## Lo que NO haces

- No instales plugins, servidores MCP ni dependencias "por si acaso": justifica cada una antes.
- No cambies contratos JSON ni endpoints sin avisarme.
- No uses emojis en la interfaz; solo íconos vectoriales locales.
- No dependas de CDN: fuentes e íconos van dentro del proyecto.
- No subas nada a GitHub sin mi OK y sin pasar `/preflight-entrega`.
- Los precios del catálogo son de ejemplo, no cotizaciones reales; dilo en README y video.

## Dónde mirar

- Estructura y comandos reales: `.agents/rules/estructura-y-comandos.md`
- Procedimientos (se invocan con `/`): `.agents/workflows/`
- Conocimiento reutilizable: `.agents/skills/`
- Casos dorados de evaluación: `evals/casos_dorados.json`
