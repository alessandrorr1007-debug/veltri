# Arquitectura de Veltri Tecnologic

Diagrama inicial por capas. Se refina a medida que se implementa cada fase.

```mermaid
flowchart TD
    U[Cliente: Web o WhatsApp] --> API[API FastAPI /consulta]
    API --> SEG[Filtro de seguridad]
    SEG -->|sospechoso| DLQ[Cola de fallidos]
    SEG --> ORQ[Orquestador LangGraph]
    ORQ --> D1[D1 Ventas: A1 A2 A3]
    ORQ --> D2[D2 Tecnico: A4]
    ORQ --> D3[D3 Inventario: A5]
    ORQ --> D4[D4 Pedidos y pagos: A6 A7 A8]
    D1 & D2 & D3 & D4 --> DEC[Capa de decision: decide]
    DEC --> HITL{Compuerta HITL}
    HITL -->|aprobado| OUT[ConsultaResponse JSON]
    HITL -->|revision| COLA[Cola de supervision humana]
    ORQ -.-> RAG[(Almacen RAG: catalogo, compatibilidad, politicas)]
    D1 & D2 & D3 & D4 -.-> TOOLS[Herramientas deterministas]
```

## Estado tras FASE 1
El diagrama anterior es el diseño futuro, sin cambio de capas. Solo existen
datos sintéticos en data/ y pruebas de integridad; no hay RAG ni flujos operativos.
Contrato y limitaciones: docs/datos.md.

## Estado tras FASE 2
Herramientas deterministas locales implementadas; los demás bloques del diagrama
inicial siguen siendo diseño futuro. No hay llamadas al modelo ni servicios.

```mermaid
flowchart LR
    DAT[JSON sintéticos de data] --> CAT[Instantánea de catálogo]
    CAT --> INV[Stock y alternativas]
    CAT --> HW[Compatibilidad y potencia estimada]
    INV --> COT[Simulación de cotización en céntimos]
    HW --> COT
    CAT --> ARM[Búsqueda por presupuesto]
    ARM --> COT
    COT -. revisión pendiente .-> HUM[Revisión humana futura]
    IMP[Importes declarados] --> PAG[Comparación sin acreditación bancaria]
    SEL[Alias y selección de demo] --> PED[Hash y borradores en memoria]
```

Contratos y límites en docs/herramientas.md. No existe conexión automática entre
pagos y pedidos; ningún borrador se confirma por coincidencia de montos.

## Estado tras FASE 3
Contratos estrictos entre llamadores futuros y herramientas. Sin cambios de capas
ni API implementada. El diagrama inicial sigue describiendo el sistema previsto.

```mermaid
flowchart LR
    E[Entradas estructuradas] --> V[Contratos Pydantic]
    V --> T[Herramientas deterministas existentes]
    T --> R[Validación de resultados y coherencia]
    R --> S[ConsultaResponse 1.0-demo]
    S -. pendiente .-> API[API futura]
```

Los modelos no ejecutan agentes ni conceden autorizaciones. Contratos y límites
en docs/esquemas.md; el motor de decisión y la revisión humana quedan pendientes.

## Estado tras FASE 4
Capa local de recuperación para el futuro RAG. Sin LLM generativo ni cambios en
agentes, grafo o API. Las herramientas deterministas siguen siendo la autoridad
para validar cálculos y stock de demostración.

```mermaid
flowchart LR
    DAT[Tres fuentes sintéticas permitidas] --> DOC[Fragmentos con citas y hashes]
    DOC --> PRIV[Guardas de privacidad]
    PRIV --> VEC[Vectores léxicos locales]
    VEC --> CH[Chroma por tenant y snapshot]
    Q[Consulta y tenant explícito] --> FIL[Filtro tenant y snapshot activo]
    FIL --> CH
    CH --> CIT[Contexto citado sin autorización de negocio]
    CIT -. integración futura .-> RAG[RAG generativo]
```

La autorización del tenant y el filtro anti injection conversacional siguen
pendientes del backend. Guardas y límites: docs/conocimiento.md.

## Estado tras FASE 5
Compuerta y bandeja local implementadas sobre resultados estructurados. El diseño
inicial sigue siendo futuro para agentes, grafo, filtro conversacional y API.

```mermaid
flowchart LR
    T[Resultados tipados de herramientas] --> E[Evidencia de decisión]
    P[Puntajes sintéticos p y c] --> E
    E --> D[Compuerta con umbrales protegidos]
    D -->|sin bloqueos y p alto| R[Ruta propuesta sin ejecutar negocio]
    D -->|bloqueos o zona intermedia| H[Revisión por tenant]
    D -->|p bajo sin bloqueos| X[Escalada local]
    X --> H
    H --> C[Solicitar corrección o rechazar]
    H -->|sin bloqueos| A[Aprobación de demo sin ejecución]
```

Bandeja en memoria con resoluciones idempotentes; no sustituye autenticación ni
un registro de auditoría durable. Contratos y supuestos: docs/decision_hitl.md.

## Estado tras FASE 6
Ocho agentes independientes y fábrica cognitiva implementados. Los nodos de los
diagramas por agente son diseño para la próxima fase; no hay grafo ni API.

```mermaid
flowchart LR
    E[Entradas tipadas y tenant] --> G[Guarda de entrada]
    G --> A[BaseAgent y agentes A1 a A8]
    F[get_llm con configuración local] --> M[MockLLM o Gemini estructurado]
    A --> M
    M --> P[Plan de intención validado]
    P --> T[Herramientas deterministas]
    T --> S[Salida de agente tipada]
    S -. integración futura .-> D[Compuerta y grafo]
```

A7/A8 comparten un registro de borradores por tenant; nunca confirman ventas.
No se usan puntuaciones reales para autorizar negocio ni se calcula con LLM.
Contratos, pruebas y límites: docs/agentes.md y docs/agentes/.

## Estado tras FASE 7
Orquestador LangGraph acotado con seguridad previa, rutas tipadas y compuerta HITL.
Los mensajes bloqueados van a DLQ local sin guardar texto libre; el grafo opera sobre
rutas tipadas sin memoria conversacional ni checkpoints. La API y la interfaz quedan
para las siguientes fases.

```mermaid
flowchart TD
    IN[SolicitudFlujo: consulta y parametros] --> SEG[Filtro anti-inyección y PII]
    SEG -->|entrada bloqueada| DLQ[Cola local DLQ]
    SEG -->|valido| A1[A1 Interpretacion: fuera del grafo]
    A1 -->|plan tipado| ORQ[StateGraph: validar_plan]
    ORQ -->|ruta tipada| DOM{Nodos de Dominio}
    DOM -->|armar| A2[A2 Armado]
    DOM -->|cotizar| A3[A3 Cotizacion]
    DOM -->|compatibilidad| A4[A4 Compatibilidad]
    DOM -->|stock| A5[A5 Inventario]
    DOM -->|pago| A6[A6 Pagos]
    DOM -->|pedido| A7[A7 Pedidos]
    DOM -->|seguimiento| A8[A8 Seguimiento]
    DOM -->|informacion| RAG[Recuperacion RAG citada]
    DOM -->|limitacion o datos invalidos| DEC[Nodo decidir: evaluar]
    A2 & A3 & A4 & A5 & A6 & A7 & A8 & RAG --> DEC
    DEC --> HITL{Compuerta decide}
    HITL -->|requiere revision| BAN[Bandeja HITL por tenant]
    HITL --> RESP[Nodo responder]
    BAN --> RESP
    RESP --> OUT[ResultadoFlujo con ConsultaResponse 1.0-demo]
```

Detalles de contratos, privacidad, flujo y pruebas en docs/grafo.md.

## Estado tras FASE 8
API FastAPI (`src/api/main.py`) implementada con el endpoint `/consulta` y contrato
estricto `ConsultaResponse`. La API actúa como la fachada HTTP pública para clientes
Web y WhatsApp, sin dependencias CDN (`docs_url=None`, `redoc_url=None`) y garantizando
que todo error (422, 404, 500) devuelva siempre un JSON estructurado tipado.

```mermaid
flowchart TD
    U[Cliente: Web o WhatsApp] -->|POST /consulta| API[FastAPI: main.py]
    API -->|SolicitudAPI a SolicitudFlujo| ORQ[Orquestador LangGraph]
    ORQ --> SEG[Filtro anti-inyección y PII]
    SEG -->|entrada bloqueada| DLQ[Cola local DLQ]
    SEG -->|valido| GRAFO[StateGraph multiagente: A1 a A8]
    GRAFO --> DEC[Compuerta decide: HITL]
    DEC --> RESP[Proyección a ConsultaResponse 1.0-demo]
    DLQ --> RESP
    RESP -->|ConsultaResponse JSON| API
    API -->|HTTP 200 / 422 / 500 tipado| U
```

Detalles de endpoints, formatos y manejo de errores en docs/api.md.

## Estado tras FASE 9
Interfaz web local (`frontend/`) servida estáticamente en la raíz por FastAPI (`src/api/main.py`),
diseñada bajo estándares WCAG AA, sin CDN y sin emojis (reemplazados por iconos SVG locales).
La UI integra la Consola Comercial con botones rápidos para los casos dorados CP-1 a CP-7,
proforma formal en Soles (`S/`), supervisión de la bandeja HITL en tiempo real y telemetría de
los pasos del grafo.

```mermaid
flowchart TD
    subgraph UI["Frontend Local (frontend/)"]
        direction TB
        CC["Consola Comercial<br>(Casos CP-1 a CP-7)"]
        PRO["Proforma Formal<br>(Desglose S/ e IGV)"]
        HITL_UI["Supervisión Humana<br>(Bandeja HITL)"]
        TEL_UI["Telemetría y Trazas<br>(Observabilidad)"]
    end

    subgraph API_GW["API FastAPI (src/api/main.py)"]
        STATIC["StaticFiles: frontend/"]
        EP["POST /consulta"]
    end

    subgraph BACKEND["Capa Orquestadora y Multiagente"]
        ORQ["Orquestador LangGraph<br>(StateGraph)"]
        DOM["Agentes A1-A8 & RAG"]
        GATE["Compuerta Decisión HITL"]
    end

    CC -->|POST /consulta| EP
    EP --> ORQ
    ORQ --> DOM
    DOM --> GATE
    GATE -->|ConsultaResponse tipado| EP
    EP -->|JSON respuesta| CC
    CC --> PRO
    GATE -. actualización .-> HITL_UI
    ORQ -. pasos y tiempos .-> TEL_UI
```

Detalles de maquetación, tokens de diseño y componentes en docs/interfaz.md.



