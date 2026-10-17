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
