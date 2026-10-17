# Políticas de demostración — FASE 1

No son políticas vigentes de Veltri ni autorización para cobrar, reservar o despachar.
Fuente de reglas obligatorias: GEMINI.md y evals/casos_dorados.json. Las propuestas
requieren aprobación de la tienda antes de uso real.

## Reglas definidas en los documentos
- Cotización: precios en soles; aritmética determinista en fases posteriores.
  Nunca generar una proforma sobre el presupuesto máximo. No inventar precios.
- Stock: no autorizar productos agotados; exigir revisión humana y sugerir
  reemplazo sin sustituir silenciosamente. CPU-AMD-5500 está agotado en la demo.
- Compatibilidad: socket incompatible exige revisión humana. La confianza del
  modelo nunca elimina un bloqueo de stock, pago, socket o presupuesto.
- Pagos: un monto discordante queda no conciliado y exige revisión humana.
  Yape aparece en CP-5; eso no confirma una cuenta o convenio comercial real.
- Pedidos: idempotencia SHA-256 de cliente|productos|cantidad|canal, sin fechas
  ni identificadores generados. No se implementa el registro en esta fase.
- Privacidad: DNI, RUC, correo y teléfono no se indexan ni se incluyen en logs.

## Propuestas pendientes de aprobación
- Cotización válida por 24 horas, sujeta a confirmar precio y disponibilidad;
  no reserva inventario. Revalidar ambos antes de confirmar el pedido.
- Precios de demo como total unitario de referencia; tratamiento de IGV,
  comprobantes, envío y montaje aún no definido. No añadir un impuesto implícito.
- Conciliar en PEN contra una fuente bancaria autorizada, monto exacto y
  referencia única; una captura o declaración del cliente no acredita pago.
  Sin evidencia, pago parcial, exceso, duplicado o moneda distinta: revisión.
- Registrar pedido confirmado solo después de stock y compatibilidad aprobados,
  pago conciliado y aceptación del cliente. Sin automatizar despacho ni devolución.
- Una revisión humana documenta motivo, evidencia y resolución; no permite
  confirmar un producto agotado ni una configuración incompatible sin corregirlos.
- Canonicalizar productos y cantidades antes del hash; definir identidad de cliente,
  alcance de duplicados, retención y acceso a evidencias en la fase de pedidos.
- Confirmar fabricantes, modelos completos, BIOS, conectores y dimensiones antes
  de cotizar equipos reales. Las fichas de demo son deliberadamente sintéticas.
- Garantías, devoluciones, cancelación, plazos, medios de pago habilitados y
  responsables de revisión: pendientes; no prometer condiciones no acordadas.
