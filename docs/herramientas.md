# Herramientas deterministas — FASE 2

Módulos Python puros en src/tools/, sin SDK, LLM, red, agentes ni endpoints.
Se conservan los JSON de la fase 1 y los archivos protegidos sin cambios.
Los resultados son diccionarios internos, previos a la fase de esquemas Pydantic;
no son el contrato ConsultaResponse ni modifican sus campos futuros.

## Entradas y salidas
- catalogo.Catalogo: carga una instantánea de data/; obtener/listar devuelven
  copias. lineas valida SKUs, cantidades enteras positivas y precios en céntimos.
  Stock no negativo. Rechaza bool, floats y SKUs desconocidos; no descuenta stock.
- inventario.comprobar_stock: disponible, faltantes por SKU y hitl_requerido.
  alternativas ofrece SKUs con stock de igual categoría y socket/tipo RAM cuando
  existen esos campos; cada reemplazo requiere nueva validación de la PC completa.
- hardware.validar_configuracion: selección sku → cantidad. Esta versión admite
  exactamente una unidad de cada categoría, GPU y refrigeración dedicada incluidas.
  Un kit RAM es una unidad del catálogo; modulos indica sus módulos físicos.
  Valida socket, chipset, tipo/capacidad/ranuras RAM, interfaz SSD, montaje,
  refrigeración, fuente y conectores. Devuelve conflictos con códigos estables,
  pendientes y potencia_estimada_w. Sin conflictos no significa aprobación real:
  aprobado_tecnicamente=false y hitl_requerido=true por las fichas sintéticas.
- cotizacion.cotizar: lineas con fuente por SKU, total_centimos, sobre_presupuesto,
  stock, tecnico y bloqueos. Presupuesto inclusivo; no añade IGV/envío/montaje.
  Genera siempre simulación (genera_proforma=false), nunca una proforma autorizada.
- armador.armar: mínimo y máximo opcional en céntimos, solo_rtx opcional.
  Busca entre productos con stock una PC de ocho categorías sin conflictos en
  los datos. Con máximo elige el mayor total admisible; sin máximo, el menor total
  que cumple el mínimo (por ejemplo 500000 para “5000 a más”; 0 para “lo más barato”).
  Es una regla provisional de demostración, NO optimización de rendimiento ni
  recomendación comercial. Debe acordarse el criterio de rendimiento en otra fase.
  No interpreta texto libre: el llamador debe proporcionar límites numéricos.
  Si no hay solución, cotizacion=null e informa minimo_catalogo_centimos para ese
  inventario/filtro, o null si no hay PC posible. No es un mínimo del mercado real.
  Empates se resuelven de forma estable por orden de SKU. Enumeración de núcleos
  CPU/placa/GPU/RAM/SSD y búsqueda binaria en soportes fuente/gabinete/cooler.
- pagos.comparar_pago: calcula coincidencia y diferencia en céntimos. Otra moneda
  no se convierte. El estado siempre es no_conciliado: no hay evidencia bancaria.
  Este módulo no autentica pagos ni implementa conciliación financiera real.
- pedidos.clave_pedido: hash SHA-256 UTF-8 de cliente|productos|cantidad|canal.
  Canonicalización propuesta: SKUs ordenados en array JSON compacto y cantidades
  alineadas en otro array JSON compacto; canal web o whatsapp; sin timestamps.
  Solo alias sintéticos demo_ seguidos de letras minúsculas, sin datos personales.
- pedidos.RegistroDemo: idempotencia dentro de una instancia en un proceso.
  registrar devuelve duplicado, registros_creados (0 o 1) y borrador_demo.
  No hay persistencia, atomicidad concurrente, reserva, cobro, confirmación ni envío.
  No usar este repositorio de prueba para pedidos comerciales.

## Supuestos y límites
Potencia usa exclusivamente los parámetros propuestos en compatibilidad.json,
con aritmética entera y redondeo hacia arriba. No se ejecuta la cadena formula
como código, ni se asignan porcentajes de cuello de botella o FPS.
Los datos deben cumplir el contrato de fase 1: el loader comprueba identidad,
moneda, precio y stock; las pruebas de integridad verifican el resto del contrato.
Una ficha corrupta puede producir excepción: nunca se convierte en aprobación.
No se implementan probabilidades, capa de decisión, compuerta de aprobación humana,
MockLLM ni banco simulado: las pruebas llaman funciones deterministas directamente.
Los flags HITL describen bloqueos; no constituyen la futura cola de supervisión.

CP-3, CP-4, CP-5 y CP-6 tienen comprobaciones parciales de herramientas. CP-7
comprueba límites y búsqueda, pero presupuestos insuficientes no generan PCs.
CP-1 no puede aprobarse con evidencia sintética; CP-2 requiere la futura seguridad.
No se afirma que los siete casos end-to-end estén implementados o aprobados.

## Reproducir
```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest tests/test_herramientas.py -q
python scripts/verificar.py
```

Sin nuevas dependencias. Pendiente: fichas de fabricante, criterio de armado,
política tributaria/comercial, identidad de cliente e idempotencia persistente,
proveedor de evidencia bancaria y flujo de autorización humana.
