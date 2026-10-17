# A8_SEGUIMIENTO — D4

Responsabilidad propuesta: Consultar borrador del mismo tenant. No confirma ventas ni despachos.

```mermaid
flowchart LR
    E[EntradaSeguimiento con tenant explícito] --> V[Validación y guarda de entrada]
    V --> M[Modelo obtenido por get_llm]
    M --> P[PlanModelo validado]
    P --> T[RegistroPorTenant.consultar]
    T --> S[EstadoBorrador tipado]
    N[Nodo futuro a8_seguimiento] -. integración pendiente .-> E
```

Contrato visual previo al código. El nodo mencionado NO se implementa en FASE 6.
La generación de un plan no autoriza operaciones comerciales. Datos y cálculos
siguen en tools/; cada agente hereda BaseAgent y tiene prompt propio. Se prueban
caso válido, límite y fallo con MockLLM. Las salidas del modelo no pueden cambiar
el tenant, las cantidades, precios, stock, evidencia ni el estado de un pago.
