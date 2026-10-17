# Guía Maestra de Exposición y Estructura — Veltri Tecnologic

Esta guía está diseñada para que puedas **explicar y exponer el proyecto de forma ordenada, clara y fluida en 5 a 10 minutos**, mostrando exactamente dónde está cada componente y qué comando ejecutar.

---

## 1. Mapa Rápido de Carpetas (¿Dónde está cada cosa?)

| Carpeta | Propósito en el Proyecto | Archivos Clave para Mostrar |
|---|---|---|
| **`src/graph/`** | **Orquestador Multiagente (LangGraph)**: Define el grafo cíclico acotado y la máquina de estados. | [`state.py`](file:///d:/Proyectos/veltri-orquestador/src/graph/state.py), [`workflow.py`](file:///d:/Proyectos/veltri-orquestador/src/graph/workflow.py) |
| **`src/agents/`** | **8 Agentes Especializados (D1 a D4)**: Capa cognitiva tipada que interpreta intenciones. | [`d1_ventas/`](file:///d:/Proyectos/veltri-orquestador/src/agents/d1_ventas/), [`d2_tecnico/`](file:///d:/Proyectos/veltri-orquestador/src/agents/d2_tecnico/), [`d3_inventario/`](file:///d:/Proyectos/veltri-orquestador/src/agents/d3_inventario/), [`d4_pedidos/`](file:///d:/Proyectos/veltri-orquestador/src/agents/d4_pedidos/) |
| **`src/core/`** | **Gobernanza, Decisión y Seguridad**: Umbrales HITL protegidos, anti prompt injection y DLQ. | [`seguridad.py`](file:///d:/Proyectos/veltri-orquestador/src/core/seguridad.py), [`umbrales.py`](file:///d:/Proyectos/veltri-orquestador/src/core/umbrales.py), [`hitl.py`](file:///d:/Proyectos/veltri-orquestador/src/core/hitl.py), [`llm.py`](file:///d:/Proyectos/veltri-orquestador/src/core/llm.py) |
| **`src/tools/`** | **Herramientas Deterministas en Código**: La aritmética nunca la hace el LLM (precios, TDP, stock, SHA-256). | [`armador.py`](file:///d:/Proyectos/veltri-orquestador/src/tools/armador.py), [`hardware.py`](file:///d:/Proyectos/veltri-orquestador/src/tools/hardware.py), [`consulta_comercial.py`](file:///d:/Proyectos/veltri-orquestador/src/tools/consulta_comercial.py) |
| **`src/knowledge/`** | **Almacén de Conocimiento (RAG)**: Búsqueda vectorial local con aislamiento estricto por tenant. | [`almacen.py`](file:///d:/Proyectos/veltri-orquestador/src/knowledge/almacen.py), [`ingesta.py`](file:///d:/Proyectos/veltri-orquestador/src/knowledge/ingesta.py) |
| **`src/schemas/`** | **Contratos Estrictos (Pydantic)**: Esquemas tipados para entradas, respuestas y el contrato único. | [`consulta.py`](file:///d:/Proyectos/veltri-orquestador/src/schemas/consulta.py), [`flujo.py`](file:///d:/Proyectos/veltri-orquestador/src/schemas/flujo.py) |
| **`src/api/`** | **Fachada FastAPI**: Expone el endpoint `POST /consulta`, `GET /catalogo` y sirve el frontend local. | [`main.py`](file:///d:/Proyectos/veltri-orquestador/src/api/main.py) |
| **`frontend/`** | **Interfaz Web Cliente (SPA)**: Consola comercial y catálogo interactivo sin dependencias externas ni CDN. | [`index.html`](file:///d:/Proyectos/veltri-orquestador/frontend/index.html), [`js/app.js`](file:///d:/Proyectos/veltri-orquestador/frontend/js/app.js), [`css/styles.css`](file:///d:/Proyectos/veltri-orquestador/frontend/css/styles.css) |
| **`data/`** | **Datos Sintéticos**: Catálogo de 84 SKUs, matriz de compatibilidad y políticas en Soles (S/). | [`catalogo.json`](file:///d:/Proyectos/veltri-orquestador/data/catalogo.json), [`compatibilidad.json`](file:///d:/Proyectos/veltri-orquestador/data/compatibilidad.json), [`politicas.md`](file:///d:/Proyectos/veltri-orquestador/data/politicas.md) |
| **`evals/`** | **Evaluación y Casos Dorados**: Casos CP-1 a CP-7 y línea base de regresión protegida. | [`casos_dorados.json`](file:///d:/Proyectos/veltri-orquestador/evals/casos_dorados.json), [`linea_base.json`](file:///d:/Proyectos/veltri-orquestador/evals/linea_base.json) |
| **`docs/`** | **Documentación Técnica por Fases**: Diagramas Mermaid de arquitectura, contratos y guion de video. | [`arquitectura.md`](file:///d:/Proyectos/veltri-orquestador/docs/arquitectura.md), [`guion-video.md`](file:///d:/Proyectos/veltri-orquestador/docs/guion-video.md) |
| **`tests/`** | **Suite de Pruebas (100% Cobertura)**: 397 tests unitarios y de integración con MockLLM sin gastar red. | [`test_flujo.py`](file:///d:/Proyectos/veltri-orquestador/tests/test_flujo.py), [`test_consulta_comercial.py`](file:///d:/Proyectos/veltri-orquestador/tests/test_consulta_comercial.py) |

---

## 2. Guion Sugerido de Exposición (Paso a Paso en 7 Minutos)

### Minuto 1: Introducción y Problema de Negocio
- **Qué decir:** *"Veltri Tecnologic es un sistema multiagente basado en LangGraph diseñado para tiendas de hardware en Lima, Perú. Su objetivo es cotizar PCs en Soles (S/), validar compatibilidad técnica de socket y fuente, conciliar comprobantes de pago y registrar pedidos, aplicando siempre revisión humana (HITL) en caso de cualquier anomalía."*
- **Qué mostrar:** El archivo [`README.md`](file:///d:/Proyectos/veltri-orquestador/README.md) o abrir el navegador en `http://127.0.0.1:8000`.

### Minuto 2: Invariantes de Gobernanza (Lo que hace seguro al sistema)
- **Qué decir:**
  1. *La aritmética va en código (`src/tools/`): El LLM jamás inventa un precio ni calcula compatibilidades.*
  2. *Seguridad antes del grafo (`src/core/seguridad.py`): Las inyecciones de prompt y datos privados se bloquean antes de llegar al modelo.*
  3. *Una probabilidad alta nunca autoriza un error: Si falta stock o el pago no cuadra, se exige revisión humana obligatoria.*
  4. *Todo acceso RAG exige tenant explícito (`veltri_tecnologic_pe`).*
  5. *Pedidos con hash SHA-256 idempotente.*

### Minuto 3: Los 8 Agentes por Dominio (D1 a D4)
- **Qué mostrar:** La carpeta [`src/agents/`](file:///d:/Proyectos/veltri-orquestador/src/agents/).
- **Explicar los 4 dominios:**
  - **D1 Ventas:** A1 (Intención), A2 (Armado de PC), A3 (Cotización formal con IGV).
  - **D2 Técnico:** A4 (Validación técnica: socket AM4/AM5/LGA1700, TDP y cuello de botella).
  - **D3 Inventario:** A5 (Stock en almacén de los 84 componentes).
  - **D4 Pedidos/Pagos:** A6 (Conciliación de pagos Yape/Transferencia), A7 (Borrador idempotente SHA-256), A8 (Seguimiento).

### Minuto 4: Orquestador LangGraph y Capa de Decisión
- **Qué mostrar:** [`src/graph/workflow.py`](file:///d:/Proyectos/veltri-orquestador/src/graph/workflow.py).
- **Qué decir:** *"El orquestador coordina los agentes mediante un StateGraph tipado. Ningún nodo parsea texto libre; todas las transiciones usan esquemas Pydantic y compuertas deterministas."*

### Minuto 5: Demostración en Vivo en la Interfaz Web
- **Abrir en navegador:** `http://127.0.0.1:8000`.
- **Acciones a realizar:**
  1. **Cotización exitosa:** Clic en botón `CP-1: Gaming S/ 3,500` -> Muestra configuración armada dentro del presupuesto con proforma formal desglosada y cálculo de IGV.
  2. **Bloqueo de seguridad:** Clic en `CP-2: Inyección Prompt` -> La guarda bloquea la entrada y la deriva a la cola DLQ.
  3. **Consulta comercial con memoria:**
     - Escribir: *"cual es su rtx mas barata"* -> Responde `GPU-RTX3050` por S/ 1,790.00.
     - Escribir: *"y la mas cara"* -> Resuelve la elipsis recordando el contexto y responde `GPU-RTX4080SUPER` por S/ 2,990.00.
  4. **Catálogo de Hardware:** Ir a la pestaña `Catálogo de Hardware`, filtrar por `Tarjetas de Video`, buscar un componente y presionar `Consultar en Chat`.

### Minuto 6: Verificación y Calidad de Código
- **Ejecutar en la terminal:**
  ```powershell
  .\.venv\Scripts\python scripts/verificar.py
  ```
- **Qué mostrar:** Salida con **397 tests pasados**, Ruff linter sin advertencias y escaneo de secretos sin hallazgos.

---

## 3. Comandos Útiles para Demostración

```powershell
# 1. Iniciar servidor de desarrollo web
.\.venv\Scripts\python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000

# 2. Correr verificación completa (Ruff + 397 Pytest + Secretos)
.\.venv\Scripts\python scripts/verificar.py

# 3. Probar solo los 7 Casos Dorados de Flujo
.\.venv\Scripts\python -m pytest tests/test_flujo.py -v

# 4. Probar la memoria conversacional y consultas comerciales
.\.venv\Scripts\python -m pytest tests/test_consulta_comercial.py -v

# 5. Ingesta del conocimiento RAG con aislamiento por tenant
.\.venv\Scripts\python -m src.knowledge.ingesta --tenant veltri_tecnologic_pe
```
