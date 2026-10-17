---
name: diseno-ui-profesional
description: Úsalo siempre que se cree, rediseñe o revise cualquier interfaz web de Veltri (pantallas, componentes, CSS, layout). Aplica un sistema de diseño sobrio y profesional y evita el aspecto genérico de plantilla de IA.
---

# Diseño de interfaz profesional para Veltri

## Dirección
Interfaz sobria, precisa y confiable para ingeniería y hardware. Referentes de tono: herramientas SaaS técnicas (líneas nítidas, neutros de alta fidelidad, un solo acento de marca). Nada de brillos de fantasía.

## Evita
- Degradados cian o morados, resplandores (glows) y sombras de neón.
- Tarjetas idénticas con sombra suave y textos centrados sin jerarquía.
- Emojis como íconos (se ven distinto en cada sistema operativo).
- Colores, tamaños o espaciados sueltos fuera de los tokens.
- JSON crudo mostrado al cliente (se ofrece un botón "Ver JSON").
- Barras de scroll y controles nativos sin estilo que rompan el tema.

## Tokens obligatorios (variables CSS en `frontend/css/tokens.css`)
- Color: marca (azul cobalto), 10 pasos de neutros, semánticos (éxito esmeralda, advertencia ámbar, peligro carmín, info) y modo claro y oscuro.
- Tipografía: Inter para interfaz y JetBrains Mono para SKUs, precios en S/ y JSON, con cifras tabulares. Archivos de fuente locales con fuentes de respaldo del sistema.
- Espaciado en múltiplos de 4 u 8 px; radios 4 (insignias), 8 (controles) y 12 (tarjetas); duraciones de animación de 150 a 200 ms.
- Íconos: un solo set vectorial (Lucide) incrustado en el proyecto.

## Vistas
1. **Consola comercial:** chat, casos de prueba rápidos (botones de 40 px o más), proforma formal (SKU, componente, precio, subtotal, IGV, total en S/, badges de categoría, stock) y botón "Ver JSON".
2. **Supervisión HITL:** tabla de pedidos retenidos con prioridad, motivo, probabilidad y confianza; aprobar o rechazar con modal de confirmación y comentario; manejo visible de errores.
3. **Trazas y telemetría:** línea de tiempo vertical de agentes (estado, latencia en ms, confianza), KPIs y métricas de compatibilidad (socket, cuello de botella, TDP, holgura).

## Estados obligatorios en cada componente
Carga (skeleton o indicador de escritura), vacío, error, éxito, deshabilitado y foco visible.

## Accesibilidad y responsive
Contraste WCAG AA, foco visible con teclado, etiquetas en formularios, objetivos táctiles de 40 px o más, `prefers-reduced-motion` respetado, y vistas correctas en móvil, tablet y escritorio. Textos en español peruano claro. Sin dependencias de CDN.

## Checklist final
- [ ] Sin emojis ni colores sueltos.
- [ ] Funciona sin internet.
- [ ] Modo claro y oscuro revisados.
- [ ] Estados de carga, vacío y error probados.
- [ ] Navegación por teclado completa.
- [ ] La interfaz no cambió ningún contrato JSON ni endpoint.
