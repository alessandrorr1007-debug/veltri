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
    tenant: null,
    peticiones: new AbortController(),
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
  setupEmpresas();


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
      if (!texto || !state.tenant) return;

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
    const signal = state.peticiones.signal;
    setLoading(true);
    const respuesta = await Api.enviarConsulta(payload, signal);
    if (signal.aborted) return;
    setLoading(false);
    state.lastResponse = respuesta.data;
    const datos = respuesta.data;
    if (respuesta.ok && datos.status !== 'bloqueado') {
      actualizarContextoComercial(payload.mensaje, datos);
    }
    agregarMensajeChat('bot', datos.mensaje, datos);

    // Actualizar proforma
    renderProforma(datos);
    return datos;
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
      const statusNombre = metadata.status.replace('_', ' ');
      statusHtml = `<span class="status-badge ${metadata.status}">${statusNombre}</span>`;
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
      const bannerHtml = `
        <div class="proforma-banner warning">
          ${Icons.alertTriangle(20)}
          <div>
            <strong>Propuesta pendiente de revisión técnica</strong>
            <p>${escapeHtml(data.mensaje)}</p>
          </div>
        </div>
      `;

      const lineas = Array.isArray(c.lineas) ? c.lineas : [];
      let lineasHtml = lineas.length > 0 ? lineas.map((l) => `
        <tr>
          <td><code class="sku-text">${escapeHtml(l.sku)}</code></td>
          <td>${escapeHtml((l.sku || '').replace(/-/g, ' '))}</td>
          <td class="tabular-nums" style="text-align: center;">${l.cantidad || 1}</td>
          <td class="tabular-nums" style="text-align: right;">${Api.formatearSoles(l.precio_unitario_centimos)}</td>
          <td class="tabular-nums" style="text-align: right;">${Api.formatearSoles(l.subtotal_centimos)}</td>
          <td>${c.stock.faltantes.some((f) => f.sku === l.sku) ? 'Insuficiente' : 'Disponible'}</td>
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
    if (!state.tenant) return;
    if (!state.catalogo) {
      if (elements.catalogoGrid) {
        elements.catalogoGrid.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: var(--space-8); color: var(--text-muted);">
            Cargando inventario de catálogo en tiempo real...
          </div>
        `;
      }
      const signal = state.peticiones.signal;
      const data = await Api.obtenerCatalogo(state.tenant, signal);
      if (signal.aborted) return;
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
            <span style="font-size: 0.75rem; color: var(--text-muted);">Precio sintético</span>
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
  function setupEmpresas() {
    const formulario = document.getElementById('sesion-local');
    const selector = document.getElementById('empresa-activa');
    const espacio = document.getElementById('espacio-empresa');
    const gestion = document.getElementById('gestion-empresa');
    const panel = document.getElementById('panel-empresas');
    const mensaje = document.getElementById('estado-sesion');
    const titulo = document.querySelector('.brand-title');
    const marca = document.querySelector('.brand-icon');
    const logoOriginal = [...marca.childNodes];
    const proformaOriginal = elements.proformaView.innerHTML;
    let empresas = [];
    let general = false;

    async function api(ruta, method = 'GET', datos, tenant = state.tenant, signal) {
      const cabeceras = { 'Content-Type': 'application/json' };
      if (tenant) cabeceras['X-Veltri-Tenant'] = tenant;
      const respuesta = await fetch('/plataforma' + ruta, {
        method, headers: cabeceras, signal, body: datos ? JSON.stringify(datos) : undefined,
      });
      if (!respuesta.ok) throw new Error(`Operación rechazada (${respuesta.status}).`);
      return respuesta.json();
    }

    function cambiarEmpresa(id) {
      state.peticiones.abort();
      state.peticiones = new AbortController();
      const empresa = empresas.find((item) => item.id === id);
      state.tenant = empresa?.activa ? id : null;
      state.contextoComercial = null;
      state.lastResponse = null;
      state.catalogo = null;
      state.catalogoQuery = '';
      state.catFiltro = 'todas';
      elements.catalogoSearch.value = '';
      elements.catFilterBtns.forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.cat === 'todas');
        btn.setAttribute('aria-pressed', String(btn.dataset.cat === 'todas'));
      });
      elements.catalogoGrid.replaceChildren();
      elements.chatMessages.replaceChildren();
      elements.chatInput.value = '';
      elements.proformaView.innerHTML = proformaOriginal;
      elements.btnViewJson.disabled = true;
      elements.jsonContent.textContent = '';
      elements.jsonModal.classList.remove('active');
      setLoading(false);
      document.querySelector('.nav-tabs').hidden = !state.tenant;
      const vista = state.tenant ? state.activeTab : null;
      elements.views.forEach((seccion) => {
        seccion.classList.toggle('active', seccion.id === `view-${vista}`);
      });
      gestion.replaceChildren();
      titulo.textContent = empresa?.nombre || 'Veltri Tecnologic';
      document.getElementById('descripcion-empresa').textContent = empresa
        ? [empresa.descripcion, ...empresa.servicios].join(' · ')
        : 'Selecciona una empresa o registra una nueva.';
      if (empresa?.logo_png) {
        const img = document.createElement('img');
        img.alt = '';
        img.src = 'data:image/png;base64,' + empresa.logo_png;
        marca.replaceChildren(img);
      } else {
        marca.replaceChildren(...(empresa ? [empresa.logo] : logoOriginal));
      }
      marca.style.setProperty('--empresa-color', empresa?.color || 'transparent');
      espacio.style.setProperty('--empresa-secundario', empresa?.color_secundario || 'transparent');
      if (state.tenant) {
        agregarMensajeChat('bot', `Bienvenido a ${empresa.nombre}. Consulta precios, stock o políticas.`);
        if (state.activeTab === 'catalogo') cargarYRenderizarCatalogo();
      }
      if (panel.open) cargarGestion();
    }

    async function cargarEmpresas(id, signal) {
      const datos = await api('/empresas', 'GET', undefined, null, signal);
      if (signal?.aborted) return;
      empresas = datos.empresas;
      general = datos.general;
      selector.replaceChildren(new Option('Selecciona', ''));
      empresas.forEach(({id, nombre, activa}) => {
        selector.add(new Option(activa ? nombre : `${nombre} (inactiva)`, id));
      });
      selector.disabled = !empresas.length;
      selector.value = id ?? empresas.find((empresa) => empresa.activa)?.id ?? '';
      formulario.hidden = true;
      espacio.hidden = false;
      cambiarEmpresa(selector.value);
    }

    selector.addEventListener('change', () => cambiarEmpresa(selector.value));
    panel.addEventListener('toggle', () => { if (panel.open) cargarGestion(); });
    formulario.addEventListener('submit', async (e) => {
      e.preventDefault();
      const credenciales = Object.fromEntries(new FormData(formulario));
      try {
        await api('/sesion', 'POST', credenciales);
        formulario.reset();
        mensaje.textContent = '';
        await cargarEmpresas();
      } catch (error) {
        mensaje.textContent = error.message;
      }
    });
    document.getElementById('salir-local').addEventListener('click', async () => {
      try {
        await api('/sesion', 'DELETE');
        cambiarEmpresa('');
        location.reload();
      } catch (error) {
        document.getElementById('descripcion-empresa').textContent = error.message;
      }
    });

    async function cargarGestion() {
      const { signal } = state.peticiones;
      const empresa = empresas.find((item) => item.id === selector.value);
      const tenant = state.tenant;
      const puedeGestionar = general || empresa?.rol === 'administrador';
      gestion.replaceChildren();
      if (general) editorEmpresa(null, 'Registrar empresa');
      if (puedeGestionar && empresa) editorEmpresa(empresa, 'Configurar empresa');
      if (!tenant) return;
      editor('Registrar borrador de prueba', [
        ['sku', 'SKU del catálogo', 'text'], ['cantidad', 'Cantidad', 'number', 1],
      ], async ({sku, cantidad}) => {
        if (!Number.isSafeInteger(Number(cantidad)) || Number(cantidad) < 1) {
          throw new Error('Ingresa una cantidad entera positiva.');
        }
        const mensaje = 'Solicitar borrador de demostración';
        document.getElementById('tab-console').click();
        agregarMensajeChat('user', mensaje);
        const datos = await procesarPeticion({
          mensaje, canal: 'web', tenant_id: tenant,
          parametros: { tipo: 'pedido', confirmar_borrador: true,
            solicitud: { cliente: 'demo_cliente', canal: 'web', seleccion: {[sku.trim()]: Number(cantidad)} },
          },
        });
        if (!signal.aborted && !datos?.pedido) throw new Error(datos?.mensaje || 'Borrador no disponible.');
        if (!signal.aborted) cargarGestion();
      });
      try {
        const [historial, catalogo, miembros] = await Promise.all([
          api('/historial', 'GET', undefined, tenant, signal),
          puedeGestionar ? Api.obtenerCatalogo(tenant, signal) : null,
          puedeGestionar ? api('/miembros', 'GET', undefined, tenant, signal) : null,
        ]);
        if (signal.aborted) return;
        if (catalogo) editorProductos(Object.values(catalogo.categorias).flat());
        if (miembros) editorMiembros(miembros);
        mostrarHistorial(historial, empresa.rol);
      } catch (error) {
        if (!signal.aborted) gestion.append(error.message);
      }
    }

    function editor(nombre, campos, enviar) {
      const form = document.createElement('form');
      const detalle = document.createElement('details');
      const titulo = document.createElement('summary');
      titulo.textContent = nombre;
      detalle.append(titulo, form);
      const controles = {};
      const status = document.createElement('p');
      status.setAttribute('role', 'status');
      campos.forEach(([clave, etiqueta, tipo, valor, opciones]) => {
        const label = document.createElement('label');
        label.textContent = etiqueta;
        const input = document.createElement(tipo === 'textarea' || tipo === 'select' ? tipo : 'input');
        if (tipo === 'select') opciones.forEach(([id, nombre]) => input.add(new Option(nombre, id)));
        if (input instanceof HTMLInputElement) input.type = tipo;
        input.name = clave;
        input.required = !['checkbox', 'file'].includes(tipo);
        if (tipo === 'file') input.accept = 'image/png';
        if (tipo === 'checkbox') input.checked = valor;
        else if (tipo !== 'file') input.value = valor ?? '';
        label.append(input);
        controles[clave] = input;
        form.append(label);
      });
      const guardar = document.createElement('button');
      guardar.className = 'btn-primary';
      guardar.textContent = 'Guardar';
      form.append(guardar, status);
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        guardar.disabled = true;
        try {
          await enviar(Object.fromEntries(new FormData(form)));
          form.querySelectorAll('input[type=password]').forEach((input) => { input.value = ''; });
          status.textContent = 'Guardado.';
        } catch (error) {
          status.textContent = error.message;
        } finally {
          guardar.disabled = false;
        }
      });
      gestion.append(detalle);
      return controles;
    }

    function editorEmpresa(empresa, titulo) {
      const campos = empresa ? [] : [['id', 'Identificador', 'text']];
      campos.push(
        ['nombre', 'Nombre comercial', 'text', empresa?.nombre],
        ['descripcion', 'Descripción', 'textarea', empresa?.descripcion],
        ['logo', 'Iniciales de la marca', 'text', empresa?.logo],
        ['logo_png', 'Logo PNG opcional (máx. 32 KiB y 256 × 256)', 'file'],
        ['quitar_logo', 'Quitar logo PNG', 'checkbox', false],
        ['color', 'Color principal', 'color', empresa?.color ?? '#2563eb'],
        ['color_secundario', 'Color secundario', 'color', empresa?.color_secundario ?? '#475569'],
        ['servicios', 'Servicios separados por coma', 'text', empresa?.servicios.join(', ')],
        ['politicas', 'Políticas comerciales', 'textarea', empresa?.politicas],
      );
      if (general) campos.push(['activa', 'Empresa activa', 'checkbox', empresa?.activa ?? true]);
      editor(titulo, campos, async ({id = empresa?.id, activa, servicios, logo_png, quitar_logo, ...resto}) => {
        const signal = state.peticiones.signal;
        let imagen = quitar_logo ? null : empresa?.logo_png ?? null;
        if (logo_png.size) {
          if (logo_png.size > 32768) throw new Error('El logo supera 32 KiB.');
          const bytes = new Uint8Array(await logo_png.arrayBuffer());
          imagen = btoa(String.fromCharCode(...bytes));
        }
        if (signal.aborted) return;
        await api('/empresas/' + encodeURIComponent(id), empresa ? 'PUT' : 'POST', {
          ...resto, logo_png: imagen, activa: general ? activa === 'on' : true,
          servicios: servicios.split(',').map((s) => s.trim()).filter(Boolean),
        }, id, signal);
        if (!signal.aborted) await cargarEmpresas(id, signal);
      });
    }

    function editorProductos(productos) {
      const categorias = ['cpu', 'gpu', 'placa', 'ram', 'ssd', 'fuente', 'gabinete', 'refrigeracion'];
      const controles = editor('Productos, precios e inventario', [
        ['existente', 'Editar producto existente', 'select', '', [
          ['', 'Nuevo'], ...productos.map((p) => [p.sku, p.sku]),
        ]],
        ['sku', 'SKU', 'text'], ['nombre', 'Nombre', 'text'],
        ['categoria', 'Categoría', 'select', 'cpu', categorias.map((id) => [id, id])],
        ['precio_centimos', 'Precio en céntimos', 'number'],
        ['stock', 'Unidades en stock', 'number'],
        ['especificaciones', 'Ficha técnica JSON', 'textarea', '{}'],
      ], async ({existente, sku, precio_centimos, stock, especificaciones, ...datos}) => {
        const signal = state.peticiones.signal;
        await api('/productos/' + encodeURIComponent(sku), 'PUT', {
          ...datos, precio_centimos: Number(precio_centimos), stock: Number(stock),
          especificaciones: JSON.parse(especificaciones),
        }, state.tenant, signal);
        if (!signal.aborted) {
          state.catalogo = null;
          await cargarGestion();
          if (state.activeTab === 'catalogo') cargarYRenderizarCatalogo();
        }
      });
      const retirar = document.createElement('button');
      retirar.type = 'button';
      retirar.textContent = 'Retirar producto seleccionado';
      retirar.disabled = true;
      controles.existente.form.append(retirar);
      controles.existente.required = false;
      retirar.addEventListener('click', async () => {
        const sku = controles.existente.value;
        if (!sku || !window.confirm(`¿Retirar ${sku} del catálogo?`)) return;
        const signal = state.peticiones.signal;
        try {
          await api('/productos/' + encodeURIComponent(sku), 'DELETE', undefined, state.tenant, signal);
          if (!signal.aborted) {
            state.catalogo = null;
            cargarGestion();
            if (state.activeTab === 'catalogo') cargarYRenderizarCatalogo();
          }
        } catch (error) {
          if (!signal.aborted) controles.existente.form.querySelector('[role=status]').textContent = error.message;
        }
      });
      controles.existente.addEventListener('change', () => {
        const producto = productos.find((p) => p.sku === controles.existente.value);
        retirar.disabled = !producto;
        Object.keys(controles).filter((k) => k !== 'existente').forEach((k) => {
          controles[k].value = k === 'especificaciones'
            ? JSON.stringify(producto?.[k] || {}, null, 2) : producto?.[k] ?? (k === 'categoria' ? 'cpu' : '');
        });
      });
    }

    function editorMiembros(miembros) {
      const roles = [['cliente', 'Cliente'], ['operador', 'Operador'], ['administrador', 'Administrador']];
      editor('Crear usuario local', [
        ['usuario', 'Usuario', 'text'], ['clave', 'Contraseña', 'password'],
        ['rol', 'Perfil', 'select', 'cliente', roles],
      ], async (datos) => {
        await api('/miembros', 'POST', datos, state.tenant, state.peticiones.signal);
      });
      editor('Asignar o retirar un permiso', [
        ['usuario', 'Usuario', 'text'],
        ['rol', 'Perfil', 'select', 'cliente', [...roles, ['retirar', 'Retirar acceso']]],
      ], async ({usuario, rol}) => {
        await api('/miembros/' + encodeURIComponent(usuario), 'PUT', {
          rol: rol === 'retirar' ? null : rol,
        }, state.tenant, state.peticiones.signal);
      });
      const p = document.createElement('p');
      p.textContent = miembros.map(({usuario, rol}) => `${usuario} (${rol})`).join(', ');
      gestion.append(p);
    }

    function mostrarHistorial({historial, estadisticas}, rol) {
      const encabezado = document.createElement('h3');
      encabezado.textContent = 'Operaciones de la empresa';
      const totales = document.createElement('p');
      totales.textContent = Object.entries(estadisticas).map(([tipo, total]) => `${tipo}: ${total}`).join(' · ')
        || 'Todavía no hay operaciones.';
      const lista = document.createElement('ul');
      historial.forEach(({tipo, id, datos}) => {
        const fila = document.createElement('li');
        fila.textContent = [
          tipo, datos.intencion, datos.estado ?? datos.status,
          datos.cotizacion ? Api.formatearSoles(datos.cotizacion.total_centimos) : '',
          tipo === 'pedido' ? id : '',
        ].filter(Boolean).join(' · ');
        if (tipo === 'revision' && rol !== 'cliente' && !datos.resolucion) {
          const acciones = {
            rechazar: 'Rechazar revisión', solicitar_correccion: 'Solicitar corrección',
            aprobar_demo: 'Aprobar simulación',
          };
          Object.entries(acciones).forEach(([accion, etiqueta]) => {
            if (accion === 'aprobar_demo' && (datos.decision.bloqueos.length || datos.estado === 'escalada')) return;
            const boton = document.createElement('button');
            boton.textContent = etiqueta;
            boton.addEventListener('click', async () => {
              const signal = state.peticiones.signal;
              try {
                await api('/revisiones/' + id, 'POST', {accion}, state.tenant, signal);
                if (!signal.aborted) cargarGestion();
              } catch (error) {
                if (!signal.aborted) fila.append(error.message);
              }
            });
            fila.append(boton);
          });
        }
        lista.append(fila);
      });
      gestion.append(encabezado, totales, lista);
    }

    cargarEmpresas().catch(() => { document.querySelector('.nav-tabs').hidden = true; });
  }

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
