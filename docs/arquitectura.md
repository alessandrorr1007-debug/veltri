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
