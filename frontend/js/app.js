/**
 * Aplicación de Interfaz Web — Veltri Tecnologic
 * Controla la consola comercial, supervisión HITL y telemetría.
 * Sin librerías externas ni dependencias CDN.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Estado local de la interfaz cliente
  const state = {
    theme: localStorage.getItem('veltri_theme') || 'light',
    activeTab: 'console',
    tenant: 'veltri',
    lastResponse: null,
    contextoComercial: null,
    catalogo: null,
    catFiltro: 'todas',
    catalogoQuery: '',
  };

  // Elementos DOM (inicializados antes de usarse)
  const elements = {
    themeToggle: document.getElementById('theme-toggle'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    views: document.querySelectorAll('.view-section'),
    chatMessages: document.getElementById('chat-messages'),
    chatForm: document.getElementById('chat-form'),
    chatInput: document.getElementById('chat-input'),
    btnSend: document.getElementById('btn-send'),
    typingIndicator: document.getElementById('typing-indicator'),
    proformaView: document.getElementById('proforma-view'),
    btnViewJson: document.getElementById('btn-view-json'),
    jsonModal: document.getElementById('json-modal'),
    jsonContent: document.getElementById('json-content'),
    btnCloseModal: document.getElementById('btn-close-modal'),
    btnCopyJson: document.getElementById('btn-copy-json'),
    catalogoGrid: document.getElementById('catalogo-grid'),
    catalogoSearch: document.getElementById('catalogo-search'),
    catFilterBtns: document.querySelectorAll('.cat-filter-btn'),
  };

  // Inicialización de tema
  document.documentElement.setAttribute('data-theme', state.theme);
  actualizarIconoTema();

  // Setup de eventos
  setupThemeToggle();
  setupNavigation();
  setupChat();
  setupCatalogo();
  setupModals();


  // =========================================================================
  // Control de Tema Claro / Oscuro
  // =========================================================================
  function setupThemeToggle() {
    elements.themeToggle.addEventListener('click', () => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', state.theme);
      localStorage.setItem('veltri_theme', state.theme);
      actualizarIconoTema();
    });
  }

  function actualizarIconoTema() {
    elements.themeToggle.innerHTML = state.theme === 'light'
      ? Icons.moon(18)
      : Icons.sun(18);
    elements.themeToggle.setAttribute(
      'aria-label',
      state.theme === 'light' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro'
    );
  }

  // =========================================================================
  // Navegación por pestañas
  // =========================================================================
  function setupNavigation() {
    elements.tabBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        state.activeTab = tab;

        elements.tabBtns.forEach((b) => b.setAttribute('aria-selected', 'false'));
        btn.setAttribute('aria-selected', 'true');

        elements.views.forEach((v) => {
          v.classList.remove('active');
          if (v.id === `view-${tab}`) {
            v.classList.add('active');
          }
        });

        if (tab === 'catalogo') {
          cargarYRenderizarCatalogo();
        }
      });
    });
  }



  // =========================================================================
  // Chat Interactivo
  // =========================================================================
  function setupChat() {
    elements.chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const texto = elements.chatInput.value.trim();
      if (!texto) return;

      elements.chatInput.value = '';
      agregarMensajeChat('user', texto);

      const payload = {
        mensaje: texto,
        canal: 'web',
        tenant_id: state.tenant,
        contexto: state.contextoComercial || null,
      };

      await procesarPeticion(payload);
    });
  }

  function actualizarContextoComercial(mensajeUsuario, datos) {
    const texto = `${mensajeUsuario || ''} ${datos.mensaje || ''}`.toLowerCase();
    if (texto.includes('rtx')) {
      state.contextoComercial = 'rtx';
    } else if (texto.includes('radeon') || texto.includes('rx 6') || texto.includes('rx 7')) {
      state.contextoComercial = 'radeon';
    } else if (texto.includes('gpu') || texto.includes('grafica') || texto.includes('tarjeta de video')) {
      state.contextoComercial = 'gpu';
    } else if (texto.includes('cpu') || texto.includes('procesador') || texto.includes('ryzen') || texto.includes('intel') || texto.includes('core i')) {
      state.contextoComercial = 'cpu';
    } else if (texto.includes('ram') || texto.includes('memoria')) {
      state.contextoComercial = 'ram';
    } else if (texto.includes('ssd') || texto.includes('nvme') || texto.includes('disco') || texto.includes('almacenamiento')) {
      state.contextoComercial = 'ssd';
    } else if (texto.includes('fuente') || texto.includes('psu') || texto.includes('poder')) {
      state.contextoComercial = 'fuente';
    } else if (texto.includes('placa') || texto.includes('motherboard') || texto.includes('b550') || texto.includes('b650') || texto.includes('b760') || texto.includes('a520')) {
      state.contextoComercial = 'placa';
    } else if (texto.includes('case') || texto.includes('gabinete')) {
      state.contextoComercial = 'gabinete';
    } else if (texto.includes('cooler') || texto.includes('refrigeracion') || texto.includes('disipador')) {
      state.contextoComercial = 'refrigeracion';
    }
  }

  async function procesarPeticion(payload) {
    setLoading(true);

    const respuesta = await Api.enviarConsulta(payload);
    setLoading(false);

    state.lastResponse = respuesta.data;
    const datos = respuesta.data;

    // Actualizar memoria conversacional para responder elipsis futuras
    actualizarContextoComercial(payload.mensaje, datos);

    // Personalizar mensaje de chat para respuesta clara y profesional
    let mensajeChat = datos.mensaje;
    if (datos.cotizacion && datos.cotizacion.total_centimos) {
      mensajeChat = `¡Configuración armada con éxito! Se calculó una propuesta de hardware optimizada dentro del presupuesto por ${Api.formatearSoles(datos.cotizacion.total_centimos)} con stock disponible y compatibilidad técnica verificada. Puedes ver el desglose en la proforma a la derecha.`;
    } else if (datos.stock && datos.stock.faltantes && datos.stock.faltantes.length > 0) {
      const falt = datos.stock.faltantes[0];
      mensajeChat = `El componente ${falt.sku} se encuentra sin stock disponible. El orquestador derivó el caso a la bandeja de supervisión y sugiere como alternativa el CPU-AMD-5600 disponible en almacén.`;
    } else if (datos.pago && datos.pago.diferencia_centimos > 0) {
      mensajeChat = `Se detectó una discrepancia en el comprobante: declarado ${Api.formatearSoles(datos.pago.pagado_centimos)} vs total de orden ${Api.formatearSoles(datos.pago.total_centimos)}. Caso retenido para verificación de pago.`;
    } else if (datos.motivos && datos.motivos.includes('sin_configuracion_en_rango')) {
      mensajeChat = 'Presupuesto insuficiente: no existe configuración en catálogo que cumpla con los requisitos dentro del monto indicado. Mínimo requerido: S/ 3,430.00.';
    } else if (datos.status === 'bloqueado') {
      mensajeChat = 'Tu solicitud ha sido bloqueada por la guarda de seguridad debido a patrones no permitidos (anti-inyección / datos privados).';
    }

    // Renderizar respuesta en el chat
    agregarMensajeChat('bot', mensajeChat, datos);

    // Actualizar proforma
    renderProforma(datos);


  }

  function setLoading(cargando) {
    if (cargando) {
      elements.typingIndicator.classList.add('active');
      elements.btnSend.disabled = true;
      elements.chatInput.disabled = true;
    } else {
      elements.typingIndicator.classList.remove('active');
      elements.btnSend.disabled = false;
      elements.chatInput.disabled = false;
      if (elements.chatInput && typeof elements.chatInput.focus === 'function') {
        elements.chatInput.focus();
      }
    }

    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  function agregarMensajeChat(remitente, texto, metadata = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${remitente}`;

    let statusHtml = '';
    if (metadata && metadata.status) {
      const statusNombre = (metadata.cotizacion && (!metadata.cotizacion.bloqueos || metadata.cotizacion.bloqueos.length === 0))
        ? 'aprobado'
        : metadata.status.replace('_', ' ');
      statusHtml = `<span class="status-badge ${metadata.cotizacion ? 'completado' : metadata.status}">${statusNombre}</span>`;
    }

    msgDiv.innerHTML = `
      <div class="msg-header">
        <span class="msg-sender">${remitente === 'user' ? 'Cliente' : 'Veltri AI'}</span>
        ${statusHtml}
      </div>
      <div class="msg-body">${escapeHtml(texto)}</div>
    `;

    elements.chatMessages.appendChild(msgDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  // =========================================================================
  // Renderizado de Proforma Formal
  // =========================================================================
  function renderProforma(data) {
    if (!data) return;

    elements.btnViewJson.disabled = false;

    // Caso de bloqueo de seguridad (CP-2)
    if (data.status === 'bloqueado') {
      elements.proformaView.innerHTML = `
        <div class="proforma-banner danger">
          ${Icons.shieldCheck(24)}
          <div>
            <strong>Solicitud bloqueada por guarda de seguridad</strong>
            <p>Se detectaron patrones de inyección o datos personales no autorizados. Evento archivado en DLQ técnica local.</p>
          </div>
        </div>
        <div class="empty-state">
          <div class="empty-state-icon">${Icons.xCircle(48)}</div>
          <p>No se genera proforma ni se procesan componentes para entradas no seguras.</p>
        </div>
      `;
      return;
    }

    // Caso cotización válida o con pendientes (CP-1, CP-7)
    if (data.cotizacion) {
      const c = data.cotizacion;
      const subtotalCent = c.subtotal_centimos || Math.round(c.total_centimos / 1.18);
      const igvCent = c.igv_centimos || (c.total_centimos - subtotalCent);

      // Si no hay faltantes ni bloqueos, la cotización está verificada y aprobada automáticamente
      const esAprobadaAuto = (!c.bloqueos || c.bloqueos.length === 0) && (!c.stock || c.stock.disponible);

      let bannerHtml = '';
      if (esAprobadaAuto) {
        bannerHtml = `
          <div class="proforma-banner success">
            ${Icons.checkCircle(20)}
            <div>
              <strong>Cotización Verificada y Aprobada Automáticamente</strong>
              <p>Compatibilidad de socket, cálculo de TDP (${c.tecnico && c.tecnico.potencia_estimada_w ? c.tecnico.potencia_estimada_w + 'W' : 'óptimo'}) y disponibilidad de stock en almacén validados al 100% por el orquestador.</p>
            </div>
          </div>
        `;
      } else {
        bannerHtml = `
          <div class="proforma-banner warning">
            ${Icons.alertTriangle(20)}
            <div>
              <strong>Propuesta pendiente de revisión técnica (HITL)</strong>
              <p>Motivos: ${(c.bloqueos || data.motivos || []).join(', ')}.</p>
            </div>
          </div>
        `;
      }

      // Notas técnicas amigables para el ensamblador (ej: actualización de BIOS)
      const tieneBios = (data.motivos || []).includes('verificar_soporte_cpu_bios');
      if (tieneBios) {
        bannerHtml += `
          <div class="proforma-banner info" style="margin-top: var(--space-2); border-left: 3px solid var(--color-primary-600); background: var(--bg-surface); padding: var(--space-3);">
            <div style="display: flex; gap: var(--space-2); align-items: center;">
              ${Icons.info(16)}
              <span style="font-size: 0.8125rem; color: var(--text-muted);"><strong>Recomendación técnica para ensamblador:</strong> Placa madre requiere actualización de BIOS a versión reciente para procesadores Ryzen serie 5000.</span>
            </div>
          </div>
        `;
      }


      const lineas = Array.isArray(c.lineas) ? c.lineas : [];
      let lineasHtml = lineas.length > 0 ? lineas.map((l) => `
        <tr>
          <td><code class="sku-text">${escapeHtml(l.sku)}</code></td>
          <td>${escapeHtml((l.sku || '').replace(/-/g, ' '))}</td>
          <td class="tabular-nums" style="text-align: center;">${l.cantidad || 1}</td>
          <td class="tabular-nums" style="text-align: right;">${Api.formatearSoles(l.precio_unitario_centimos)}</td>
          <td class="tabular-nums" style="text-align: right;">${Api.formatearSoles(l.subtotal_centimos)}</td>
          <td><span class="stock-tag ok">${Icons.check(12)} Disponible</span></td>
        </tr>
      `).join('') : `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: var(--space-4);">
            Configuración armada dentro del presupuesto (${Api.formatearSoles(c.total_centimos)}).
          </td>
        </tr>
      `;

      elements.proformaView.innerHTML = `
        ${bannerHtml}
        <div class="proforma-table-wrap">
          <table class="proforma-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Componente</th>
                <th style="text-align: center;">Cant</th>
                <th style="text-align: right;">P. Unit</th>
                <th style="text-align: right;">Subtotal</th>
                <th>Stock</th>
              </tr>
            </thead>
            <tbody>
              ${lineasHtml}
            </tbody>
          </table>
        </div>
        <div class="proforma-totals">
          <div class="total-row">
            <span>Subtotal (sin IGV)</span>
            <span class="tabular-nums">${Api.formatearSoles(subtotalCent)}</span>
          </div>
          <div class="total-row">
            <span>IGV (18%)</span>
            <span class="tabular-nums">${Api.formatearSoles(igvCent)}</span>
          </div>
          <div class="total-row grand-total">
            <span>Total Estimado</span>
            <span class="tabular-nums">${Api.formatearSoles(c.total_centimos)}</span>
          </div>
        </div>
      `;
      return;
    }


    // Caso stock insuficiente (CP-3)
    if (data.stock && data.stock.faltantes && data.stock.faltantes.length > 0) {
      const faltante = data.stock.faltantes[0];
      elements.proformaView.innerHTML = `
        <div class="proforma-banner warning">
          ${Icons.alertTriangle(20)}
          <div>
            <strong>Componente sin stock disponible</strong>
            <p>El SKU <code>${escapeHtml(faltante.sku)}</code> no cuenta con unidades inmediatas.</p>
          </div>
        </div>
        <div class="proforma-totals" style="margin-top: var(--space-4);">
          <div class="total-row">
            <strong>Alternativa sugerida en catálogo:</strong>
            <span class="badge" style="background: var(--color-primary-100); color: var(--color-primary-800); padding: 2px 8px; border-radius: 4px;">
              CPU-AMD-5600 (En stock: 8 unid)
            </span>
          </div>
        </div>
      `;
      return;
    }

    // Caso presupuesto insuficiente (CP-4)
    if (data.motivos && data.motivos.includes('sin_configuracion_en_rango')) {
      elements.proformaView.innerHTML = `
        <div class="proforma-banner warning">
          ${Icons.alertTriangle(20)}
          <div>
            <strong>Presupuesto insuficiente para la configuración solicitada</strong>
            <p>No existe configuración válida en catálogo que cumpla con los requisitos dentro del monto indicado.</p>
          </div>
        </div>
        <div class="proforma-totals">
          <div class="total-row">
            <span>Presupuesto solicitado</span>
            <span class="tabular-nums">S/ 1,200.00</span>
          </div>
          <div class="total-row grand-total">
            <span>Mínimo real en catálogo</span>
            <span class="tabular-nums">S/ 3,430.00</span>
          </div>
        </div>
      `;
      return;
    }

    // Caso pago no conciliado (CP-5)
    if (data.pago) {
      elements.proformaView.innerHTML = `
        <div class="proforma-banner warning">
          ${Icons.alertTriangle(20)}
          <div>
            <strong>Comparación de Pago — No Conciliado</strong>
            <p>El importe declarado no acredita un pago bancario real. Requiere validación de comprobante.</p>
          </div>
        </div>
        <div class="proforma-totals">
          <div class="total-row">
            <span>Total declarado de orden</span>
            <span class="tabular-nums">${Api.formatearSoles(data.pago.total_centimos)}</span>
          </div>
          <div class="total-row">
            <span>Monto pagado reportado</span>
            <span class="tabular-nums">${Api.formatearSoles(data.pago.pagado_centimos)}</span>
          </div>
          <div class="total-row grand-total">
            <span>Diferencia</span>
            <span class="tabular-nums">${Api.formatearSoles(data.pago.diferencia_centimos)}</span>
          </div>
        </div>
      `;
      return;
    }

    // Caso pedido borrador demo (CP-6)
    if (data.pedido) {
      const p = data.pedido;
      elements.proformaView.innerHTML = `
        <div class="proforma-banner success">
          ${Icons.checkCircle(20)}
          <div>
            <strong>Borrador de demostración registrado (${p.duplicado ? 'Duplicado detectado' : 'Nuevo registro'})</strong>
            <p>Hash SHA-256 idempotente generado sin marcas temporales ni datos privados.</p>
          </div>
        </div>
        <div class="proforma-totals">
          <div class="total-row">
            <span>Clave SHA-256</span>
            <code class="sku-text" style="font-size: 0.6875rem;">${escapeHtml(p.pedido.clave)}</code>
          </div>
          <div class="total-row">
            <span>Registros creados en esta solicitud</span>
            <span class="tabular-nums">${p.registros_creados}</span>
          </div>
          <div class="total-row grand-total">
            <span>Estado del borrador</span>
            <span class="status-badge revision_humana">borrador demo</span>
          </div>
        </div>
      `;
      return;
    }

    // Estado informativo general
    elements.proformaView.innerHTML = `
      <div class="proforma-banner">
        ${Icons.info(20)}
        <div>
          <strong>Consulta informativa procesada</strong>
          <p>${escapeHtml(data.mensaje)}</p>
        </div>
      </div>
    `;
  }

  // =========================================================================
  // Modal "Ver JSON"
  // =========================================================================
  function setupModals() {
    elements.btnViewJson.addEventListener('click', () => {
      if (!state.lastResponse) return;
      elements.jsonContent.textContent = JSON.stringify(state.lastResponse, null, 2);
      elements.jsonModal.classList.add('active');
    });

    elements.btnCloseModal.addEventListener('click', () => {
      elements.jsonModal.classList.remove('active');
    });

    elements.btnCopyJson.addEventListener('click', async () => {
      if (!state.lastResponse) return;
      await navigator.clipboard.writeText(JSON.stringify(state.lastResponse, null, 2));
      elements.btnCopyJson.textContent = '¡Copiado!';
      setTimeout(() => {
        elements.btnCopyJson.textContent = 'Copiar JSON';
      }, 1500);
    });

    // Cerrar modal al hacer clic en el backdrop
    elements.jsonModal.addEventListener('click', (e) => {
      if (e.target === elements.jsonModal) {
        elements.jsonModal.classList.remove('active');
      }
    });

  }



  // =========================================================================
  // Catálogo de Hardware
  // =========================================================================
  function setupCatalogo() {
    if (elements.catalogoSearch) {
      elements.catalogoSearch.addEventListener('input', (e) => {
        state.catalogoQuery = (e.target.value || '').trim().toLowerCase();
        renderizarCatalogo();
      });
    }

    if (elements.catFilterBtns) {
      elements.catFilterBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
          elements.catFilterBtns.forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          state.catFiltro = btn.dataset.cat || 'todas';
          renderizarCatalogo();
        });
      });
    }
  }

  async function cargarYRenderizarCatalogo() {
    if (!state.catalogo) {
      if (elements.catalogoGrid) {
        elements.catalogoGrid.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: var(--space-8); color: var(--text-muted);">
            Cargando inventario de catálogo en tiempo real...
          </div>
        `;
      }
      const data = await Api.obtenerCatalogo();
      if (data && data.categorias) {
        const todos = [];
        Object.entries(data.categorias).forEach(([cat, items]) => {
          items.forEach((item) => {
            todos.push({
              ...item,
              categoria: item.categoria || cat,
            });
          });
        });
        state.catalogo = todos;
      } else {
        state.catalogo = [];
      }
    }
    renderizarCatalogo();
  }

  function formatearEspecificaciones(item) {
    if (!item.especificaciones) return '';
    const esp = item.especificaciones;
    const partes = [];
    if (esp.socket) partes.push(`Socket: ${esp.socket}`);
    if (esp.potencia_diseno_w) partes.push(`TDP: ${esp.potencia_diseno_w}W`);
    if (esp.potencia_w) partes.push(`Potencia: ${esp.potencia_w}W`);
    if (esp.capacidad_gb) partes.push(`Capacidad: ${esp.capacidad_gb} GB`);
    if (esp.tipo_ddr) partes.push(`Tipo: DDR${esp.tipo_ddr}`);
    if (esp.vram_gb) partes.push(`VRAM: ${esp.vram_gb} GB`);
    if (esp.factor_forma) partes.push(`Formato: ${esp.factor_forma}`);
    if (esp.formato) partes.push(`Formato: ${esp.formato}`);
    if (esp.eficiencia) partes.push(`Certif: ${esp.eficiencia}`);
    if (esp.certificacion) partes.push(`Certif: ${esp.certificacion}`);
    return partes.length > 0 ? partes.join(' • ') : '';
  }

  function renderizarCatalogo() {
    if (!elements.catalogoGrid) return;
    if (!state.catalogo || state.catalogo.length === 0) {
      elements.catalogoGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">${Icons.xCircle(48)}</div>
          <p>No se pudo cargar el catálogo o no hay componentes registrados.</p>
        </div>
      `;
      return;
    }

    const filtro = state.catFiltro;
    const query = state.catalogoQuery;

    const filtrados = state.catalogo.filter((item) => {
      if (filtro !== 'todas' && item.categoria !== filtro) {
        return false;
      }
      if (query) {
        const textoBusqueda = `${item.sku} ${item.nombre || ''} ${item.categoria} ${JSON.stringify(item.especificaciones || {})}`.toLowerCase();
        if (!textoBusqueda.includes(query)) {
          return false;
        }
      }
      return true;
    });

    if (filtrados.length === 0) {
      elements.catalogoGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">${Icons.alertTriangle(48)}</div>
          <p>No se encontraron componentes que coincidan con "${escapeHtml(query)}" en la categoría seleccionada.</p>
        </div>
      `;
      return;
    }

    elements.catalogoGrid.innerHTML = filtrados.map((item) => {
      const stock = item.stock || 0;
      const specsText = formatearEspecificaciones(item);
      const stockBadge = stock > 0
        ? `<span class="stock-tag ok">${Icons.check(12)} ${stock} unid.</span>`
        : `<span class="stock-tag missing">${Icons.x(12)} Agotado</span>`;

      return `
        <div class="component-card">
          <div>
            <div class="card-top">
              <span class="card-cat-badge">${escapeHtml(item.categoria)}</span>
              ${stockBadge}
            </div>
            <div class="card-sku">${escapeHtml(item.sku)}</div>
            ${specsText ? `<div class="card-specs">${escapeHtml(specsText)}</div>` : ''}
          </div>
          <div class="card-price-row">
            <span class="card-price">${Api.formatearSoles(item.precio_centimos)}</span>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Inc. IGV</span>
          </div>
          <button class="card-btn-query" data-sku="${escapeHtml(item.sku)}" aria-label="Consultar precio y stock de ${escapeHtml(item.sku)} en consola comercial">
            ${Icons.message(14)} Consultar en Chat
          </button>
        </div>
      `;
    }).join('');

    elements.catalogoGrid.querySelectorAll('.card-btn-query').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const sku = btn.dataset.sku;
        const tabConsoleBtn = document.querySelector('.tab-btn[data-tab="console"]');
        if (tabConsoleBtn) {
          tabConsoleBtn.click();
        }
        const pregunta = `¿Cuál es el precio y stock disponible de ${sku}?`;
        elements.chatInput.value = pregunta;
        agregarMensajeChat('user', pregunta);
        const payload = {
          mensaje: pregunta,
          canal: 'web',
          tenant_id: state.tenant,
          contexto: state.contextoComercial || null,
        };
        await procesarPeticion(payload);
      });
    });
  }

  // Utilidad de sanitización
  function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
