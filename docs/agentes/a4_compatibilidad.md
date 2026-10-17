# A4_COMPATIBILIDAD — D2

Responsabilidad propuesta: Validar configuración completa. No confirma ventas ni despachos.

```mermaid
flowchart LR
    E[EntradaSeleccion con tenant explícito] --> V[Validación y guarda de entrada]
    V --> M[Modelo obtenido por get_llm]
    M --> P[PlanModelo validado]
    P --> T[validar_configuracion]
    T --> S[ResultadoTecnico tipado]
    N[Nodo futuro a4_compatibilidad] -. integración pendiente .-> E
```

Contrato visual previo al código. El nodo mencionado NO se implementa en FASE 6.
La generación de un plan no autoriza operaciones comerciales. Datos y cálculos
siguen en tools/; cada agente hereda BaseAgent y tiene prompt propio. Se prueban
caso válido, límite y fallo con MockLLM. Las salidas del modelo no pueden cambiar
el tenant, las cantidades, precios, stock, evidencia ni el estado de un pago.
