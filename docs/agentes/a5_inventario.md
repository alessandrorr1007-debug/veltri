# A5_INVENTARIO — D3

Responsabilidad propuesta: Consultar stock y alternativas. No confirma ventas ni despachos.

```mermaid
flowchart LR
    E[EntradaSeleccion con tenant explícito] --> V[Validación y guarda de entrada]
    V --> M[Modelo obtenido por get_llm]
    M --> P[PlanModelo validado]
    P --> T[comprobar_stock y alternativas]
    T --> S[ResultadoInventario tipado]
    N[Nodo futuro a5_inventario] -. integración pendiente .-> E
```

Contrato visual previo al código. El nodo mencionado NO se implementa en FASE 6.
La generación de un plan no autoriza operaciones comerciales. Datos y cálculos
siguen en tools/; cada agente hereda BaseAgent y tiene prompt propio. Se prueban
caso válido, límite y fallo con MockLLM. Las salidas del modelo no pueden cambiar
el tenant, las cantidades, precios, stock, evidencia ni el estado de un pago.
