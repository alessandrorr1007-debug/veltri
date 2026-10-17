/**
 * Cliente de API para Veltri Tecnologic
 * Interactúa con el endpoint POST /consulta bajo el contrato ConsultaResponse.
 */

const Api = {
  endpoint: '/consulta',

  async enviarConsulta(payload) {
    try {
      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      return {
        ok: response.ok,
        status: response.status,
        data: data,
      };
    } catch (error) {
      return {
        ok: false,
        status: 0,
        data: {
          version_contrato: '1.0-demo',
          naturaleza: 'demostracion_sintetica',
          status: 'error',
          intencion: 'desconocida',
          mensaje: 'No se pudo conectar con el servidor local de la API.',
          hitl_requerido: false,
          motivos: ['conexion_rechazada'],
          fuentes: [],
          genera_proforma: false,
          aprobado_tecnicamente: false,
          archivado_en_dlq: false,
        },
      };
    }
  },

  formatearSoles(centimos) {
    if (typeof centimos !== 'number') return 'S/ 0.00';
    return `S/ ${(centimos / 100).toLocaleString('es-PE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  },
};
