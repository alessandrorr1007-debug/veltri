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

## 3. Vistas Principales (Orientadas al Cliente)

### A. Consola Comercial (Atención al Cliente)
- **Barra de Casos Rápidos (CP-1 a CP-7):** Permite cargar con un clic los escenarios dorados
  de prueba (CP-1 Oficina básica, CP-2 Gaming AM5, CP-3 Incompatibilidad de socket, CP-4 Stock
  insuficiente, CP-5 Presupuesto ajustado, CP-6 Pago con captura válida, CP-7 Pago en revisión).
- **Línea de Conversación:** Visualización clara de mensajes del cliente y respuestas del sistema
  con memoria conversacional para resolución de elipsis (ej. *"y la mas cara"*).
- **Proforma Comercial Formal:** Renderizado estructurado de items, código SKU, precio unitario,
  cantidad, subtotal, desglose de IGV (18%) y total en Soles (`S/`), con opción de inspeccionar
  el JSON original (`ConsultaResponse`).
- **Alertas de Bloqueo e Incompatibilidad:** Destaca visualmente componentes con conflicto de socket,
  cuello de botella o falta de stock para evitar ventas erróneas.

### B. Catálogo de Hardware (Explorador Interactivo)
- **Inventario Completo (84 Componentes):** Tarjetas estructuradas con SKU, categoría,
  especificaciones técnicas (socket, TDP, VRAM, formato), precio en Soles (S/) y stock disponible.
- **Filtros por Categoría:** Botones rápidos para filtrar por *Tarjetas de Video*, *Procesadores*,
  *Placas Madre*, *Memorias RAM*, *Almacenamiento SSD*, *Fuentes de Poder*, *Gabinetes* y *Refrigeración*.
- **Búsqueda en Tiempo Real:** Entrada predictiva que filtra por SKU, descripción o atributos técnicos.
- **Acción "Consultar en Chat":** Botón en cada componente que conmuta automáticamente a la consola
  comercial y formula la pregunta de stock y precio en el chat.

> **Nota de Arquitectura:** Las decisiones de supervisión humana (HITL) y la telemetría del grafo
> multiagente operan en la capa de gobernanza del backend (`src/core/hitl.py`, `tests/test_decision_hitl.py`),
> manteniendo el frontend web limpio, seguro y enfocado exclusivamente en la experiencia del cliente final.

---

## 4. Aviso Legal y Cumplimiento
El pie de página de la interfaz exhibe de forma fija y permanente:
> *"Veltri Tecnologic — Sistema Multiagente de Demostración. Precios, stock y especificaciones son sintéticos de prueba y no constituyen cotizaciones vinculantes para operaciones reales."*
