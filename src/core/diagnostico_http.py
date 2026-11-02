"""Transporte de diagnóstico con campos cerrados; sin cuerpos, headers o reintentos."""

from urllib.parse import urlsplit
from uuid import UUID, uuid4

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ErrorTransporteSeguro(RuntimeError):
    """Solo un texto fijo, sin excepción ni respuesta original."""


class TransporteDiagnostico(requests.Session):
    """Por instancia: correlación aleatoria y primer fallo conservado.

    Los registros se mantienen localmente en memoria; no se adjuntan a spans.
    No habilita observabilidad ni abre conexiones al construir la instancia.
    """

    def __init__(self):
        super().__init__()
        self.trust_env = False
        self.mount("https://", HTTPAdapter(max_retries=Retry(total=0, redirect=0)))
        self.registros = []
        self.primer_fallo = None
        self.correlacion = str(uuid4())

    def _destino(self, request) -> tuple[str, str]:
        url = urlsplit(request.url)
        if url.scheme != "https" or url.netloc not in {
            "api.smith.langchain.com", "eu.api.smith.langchain.com"}:
            raise ErrorTransporteSeguro("destino_no_permitido")
        if request.method == "POST" and url.path == "/runs":
            return "/runs", "crear_span"
        if request.method in {"PATCH", "GET"} and url.path.startswith("/runs/"):
            try:
                UUID(url.path.removeprefix("/runs/"))
            except ValueError:
                raise ErrorTransporteSeguro("ruta_no_permitida") from None
            return "/runs/{run_id}", (
                "cerrar_span" if request.method == "PATCH" else "verificar_run")
        raise ErrorTransporteSeguro("ruta_no_permitida")

    def send(self, request, **kwargs):
        if self.primer_fallo is not None:
            raise ErrorTransporteSeguro("transporte_detenido")
        try:
            ruta, etapa = self._destino(request)
        except ErrorTransporteSeguro:
            self._registrar("OTRO", "/ruta_no_permitida", None, "configuracion", "validar_destino")
            raise
        # Enviar directamente por adaptador evita incluso preparar un redirect.
        # Session.request ya preparó TLS, timeout y proxies para este envío.
        kwargs.pop("allow_redirects", None)
        try:
            if request.url is None:
                raise ErrorTransporteSeguro("destino_no_permitido")
            respuesta = self.get_adapter(request.url).send(request, **kwargs)
        except requests.Timeout:
            self._registrar(request.method, ruta, None, "timeout", etapa)
            raise ErrorTransporteSeguro("fallo_http_seguro") from None
        except Exception:
            self._registrar(request.method, ruta, None, "conexion", etapa)
            raise ErrorTransporteSeguro("fallo_http_seguro") from None
        codigo = respuesta.status_code
        categoria = (
            "exito" if 200 <= codigo < 300 else
            {400: "solicitud_invalida", 401: "autenticacion", 403: "permisos",
             429: "limite"}.get(codigo, "servidor" if codigo >= 500 else "http_no_exitoso")
        )
        self._registrar(request.method, ruta, codigo, categoria, etapa)
        if categoria != "exito":
            try:
                respuesta.close()
            except Exception:
                # Un fallo de liberación jamás sustituye el estado HTTP primario.
                pass
            raise ErrorTransporteSeguro("fallo_http_seguro")
        return respuesta

    def _registrar(self, metodo, ruta, estado, categoria, etapa):
        registro = {"metodo": metodo, "ruta": ruta, "estado": estado,
                    "categoria": categoria, "correlacion": self.correlacion, "etapa": etapa}
        self.registros.append(registro)
        if categoria != "exito" and self.primer_fallo is None:
            self.primer_fallo = registro.copy()
