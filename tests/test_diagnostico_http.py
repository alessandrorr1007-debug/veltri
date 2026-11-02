"""Transporte HTTP simulado: estados y privacidad sin clave real ni sockets."""

import json
from uuid import UUID, uuid4

import pytest
import requests
from requests.adapters import HTTPAdapter

from src.core.diagnostico_http import ErrorTransporteSeguro, TransporteDiagnostico


@pytest.mark.parametrize("codigo", [200, 202, 400, 401, 403, 429, 500])
@pytest.mark.parametrize("metodo,etapa", [("POST", "crear_span"), ("PATCH", "cerrar_span")])
def test_estados_y_privacidad(codigo, metodo, etapa, monkeypatch):
    llamadas = []
    canario = "contenido_sintetico_confidencial"

    def simulado(self, request, **kwargs):
        llamadas.append(1)
        respuesta = requests.Response()
        respuesta.status_code = codigo
        respuesta._content = canario.encode()
        respuesta.headers["privado"] = canario
        return respuesta

    monkeypatch.setattr(HTTPAdapter, "send", simulado)
    transporte = TransporteDiagnostico()
    path = "/runs" if metodo == "POST" else "/runs/" + str(uuid4())
    kwargs = {"headers": {"Authorization": canario}, "data": canario}
    if codigo < 300:
        assert transporte.request(metodo, "https://api.smith.langchain.com" + path, **kwargs)
    else:
        with pytest.raises(ErrorTransporteSeguro, match="fallo_http_seguro"):
            transporte.request(metodo, "https://api.smith.langchain.com" + path, **kwargs)
        original = transporte.primer_fallo.copy()
        with pytest.raises(ErrorTransporteSeguro, match="transporte_detenido"):
            transporte.post("https://api.smith.langchain.com/runs")
        assert transporte.primer_fallo == original
    registro = transporte.registros[0]
    assert registro["estado"] == codigo and registro["etapa"] == etapa
    assert registro["metodo"] == metodo and len(llamadas) == 1
    assert set(registro) == {"metodo", "ruta", "estado", "categoria", "correlacion", "etapa"}
    UUID(registro["correlacion"])
    assert canario not in json.dumps(transporte.registros)
    assert transporte.get_adapter("https://").max_retries.total == 0


@pytest.mark.parametrize("error,categoria", [
    (requests.Timeout("detalle_privado"), "timeout"),
    (requests.ConnectionError("detalle_privado"), "conexion"),
])
def test_excepciones_no_se_registran(error, categoria, monkeypatch):
    def simulado(*args, **kwargs):
        raise error
    monkeypatch.setattr(HTTPAdapter, "send", simulado)
    transporte = TransporteDiagnostico()
    with pytest.raises(ErrorTransporteSeguro) as fallo:
        transporte.post("https://api.smith.langchain.com/runs")
    assert transporte.primer_fallo["categoria"] == categoria
    assert "detalle_privado" not in str(fallo.value) + json.dumps(transporte.registros)


def test_ruta_query_y_destino_no_filtran(monkeypatch):
    def prohibido(*args, **kwargs):
        pytest.fail("No debe llegar al transporte")
    monkeypatch.setattr(HTTPAdapter, "send", prohibido)
    transporte = TransporteDiagnostico()
    with pytest.raises(ErrorTransporteSeguro):
        transporte.get("https://otro.example.test/cliente_privado?token=canario")
    assert "canario" not in json.dumps(transporte.registros)
    assert "cliente_privado" not in json.dumps(transporte.registros)


def test_query_no_aparece_en_registro(monkeypatch):
    def simulado(*args, **kwargs):
        respuesta = requests.Response()
        respuesta.status_code = 202
        respuesta._content = b'{}'
        return respuesta
    monkeypatch.setattr(HTTPAdapter, "send", simulado)
    transporte = TransporteDiagnostico()
    transporte.post("https://api.smith.langchain.com/runs?dato=canario")
    assert transporte.registros[0]["ruta"] == "/runs"
    assert "canario" not in json.dumps(transporte.registros)


@pytest.mark.parametrize("codigo", [200, 202, 400, 401, 403, 429, 500])
def test_demo_sdk_expone_diagnostico_cerrado(codigo, monkeypatch):
    from langsmith import Client as SDKClient
    from pydantic import SecretStr

    from scripts.demo_observabilidad import ejecutar_demo
    from src.config import ConfiguracionObservabilidad
    from src.core import observabilidad as obs

    llamadas = []

    def simulado(self, request, **kwargs):
        llamadas.append(request.method)
        respuesta = requests.Response()
        respuesta.status_code = codigo if request.method == "PATCH" else 202
        respuesta._content = b'contenido_sintetico_privado'
        return respuesta

    monkeypatch.setattr(HTTPAdapter, "send", simulado)
    monkeypatch.setattr(obs, "Client", SDKClient)
    diagnostico = []
    salida = ejecutar_demo(ConfiguracionObservabilidad(
        habilitada=True, permitir_envio_externo=True,
        endpoint="https://api.smith.langchain.com", clave=SecretStr("valor_sintetico"),
    ), None, diagnostico_http=diagnostico)
    assert salida.respuesta.hitl_requerido
    assert diagnostico[2]["estado"] == codigo
    assert diagnostico[2]["etapa"] == "cerrar_span"
    assert len(llamadas) == (18 if codigo < 300 else 3)
    assert len(diagnostico) == len(llamadas)
    texto = json.dumps(diagnostico)
    assert "contenido_sintetico_privado" not in texto
    assert "valor_sintetico" not in texto and "CPU-AMD-5500" not in texto


def test_redirect_no_se_sigue(monkeypatch):
    llamadas = []

    def simulado(self, request, **kwargs):
        llamadas.append(request.url)
        respuesta = requests.Response()
        respuesta.status_code = 302
        respuesta.headers["Location"] = "https://otro.example.test/dato_privado"
        respuesta._content = b'{}'
        respuesta._content_consumed = True
        respuesta.url = request.url
        return respuesta

    monkeypatch.setattr(HTTPAdapter, "send", simulado)
    transporte = TransporteDiagnostico()
    with pytest.raises(ErrorTransporteSeguro):
        transporte.post("https://api.smith.langchain.com/runs", allow_redirects=True)
    assert len(llamadas) == 1
    assert transporte.primer_fallo["estado"] == 302
    assert "dato_privado" not in json.dumps(transporte.registros)
