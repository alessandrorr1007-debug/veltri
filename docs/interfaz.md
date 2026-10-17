# Documentación de la Interfaz Web (FASE 9)

La interfaz web de **Veltri Tecnologic** es una aplicación de página única (SPA) ligera,
robusta y desacoplada, servida estáticamente por FastAPI en la raíz (`/`) y diseñada para
operación en tiendas de hardware en Lima, Perú (precios en Soles `S/`).

---

## 1. Principios de Diseño e Invariantes

1. **Cero Dependencias Externas (Sin CDN):**
   - No se importan fuentes remotas (Google Fonts), librerías de estilos ni scripts externos.
   - Se utiliza la pila de fuentes nativas del sistema (`system-ui`, `-apple-system`, `Segoe UI`, `Roboto`)
     con soporte tipográfico tabular (`font-variant-numeric: tabular-nums`) para montos y códigos SKU.
2. **Cero Emojis:**
   - La interfaz utiliza estrictamente iconos vectoriales SVG limpios creados localmente en
     `frontend/js/icons.js` (estilo visual profesional Lucide/Heroicons), garantizando sobriedad
     comercial y consistencia multiplataforma.
3. **Accesibilidad y Ergonomía (WCAG AA):**
   - Paleta de diseño basada en Azul Cobalto (`hsl(220, 85%, 52%)`) con contraste >= 4.5:1.
   - Objetivos táctiles mínimos de 40px × 40px para pulsación táctil o clic de mouse.
   - Soporte nativo para modo claro y modo oscuro (`prefers-color-scheme`).
   - Navegación accesible mediante pestañas semánticas (`role="tablist"`, `role="tab"`, `aria-selected`).

---

## 2. Estructura de Archivos

```
frontend/
├── index.html          # Maquetación semántica, modales accesibles y footer legal
├── css/
│   ├── tokens.css      # Variables CSS: colores, tipografía, radios, sombras y modo oscuro
│   └── styles.css      # Layout responsive, componentes, estados y animaciones de carga
└── js/
    ├── icons.js        # Librería de 16 iconos vectoriales SVG locales inline
    ├── api.js          # Cliente fetch tipado contra POST /consulta y formateo S/
    └── app.js          # Lógica de interacción, casos dorados CP-1 a CP-7, HITL y trazas
```

---

## 3. Vistas Principales

### A. Consola Comercial (Atención al Cliente)
- **Barra de Casos Rápidos (CP-1 a CP-7):** Permite cargar con un clic los escenarios dorados
  de prueba (CP-1 Oficina básica, CP-2 Gaming AM5, CP-3 Incompatibilidad de socket, CP-4 Stock
  insuficiente, CP-5 Presupuesto ajustado, CP-6 Pago con captura válida, CP-7 Pago en revisión).
- **Línea de Conversación:** Visualización clara de mensajes del cliente y respuestas del sistema.
- **Proforma Comercial Formal:** Renderizado estructurado de items, código SKU, precio unitario,
  cantidad, subtotal, desglose de IGV (18%) y total en Soles (`S/`), con opción de imprimir o
  inspeccionar el JSON original (`ConsultaResponse`).
- **Alertas de Bloqueo e Incompatibilidad:** Destaca visualmente componentes con conflicto de socket,
  cuello de botella o falta de stock para evitar ventas erróneas.

### B. Supervisión Humana (Bandeja HITL)
- **Panel de Decisiones Críticas:** Lista los incidentes que requieren intervención humana
  (pagos discordantes, falta de stock crítico, excepciones técnicas o discrepancias de presupuesto).
- **Métricas Operativas:** Tarjetas con conteo en vivo de casos pendientes, aprobados y rechazados.
- **Acciones del Supervisor:** Modal accesible de confirmación para Aprobar, Rechazar o Añadir
  observaciones técnicas a cada ticket, actualizando el estado de la bandeja en tiempo real.

### C. Trazas y Telemetría (Observabilidad)
- **Línea de Tiempo del Grafo:** Desglose secuencial de la ejecución de cada consulta:
  seguridad previa, agente de dominio seleccionado (A1 a A8), compuerta de decisión y
  tiempo de respuesta en milisegundos.
- **Inspección de Contratos:** Visualizador de la carga útil JSON devuelta por la API con
  formato legible y botón de copia rápida al portapapeles.

---

## 4. Aviso Legal y Cumplimiento
El pie de página de la interfaz exhibe de forma fija y permanente:
> *"Veltri Tecnologic — Sistema Multiagente de Demostración. Precios, stock y especificaciones son sintéticos de prueba y no constituyen cotizaciones vinculantes para operaciones reales."*
