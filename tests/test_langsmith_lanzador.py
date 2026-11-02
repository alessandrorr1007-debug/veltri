"""Lanzador real con servidor simulado en el adaptador: sin red ni .env real."""

import json
import os
from uuid import uuid4

import pytest
import requests
from pydantic import SecretStr
from requests.adapters import HTTPAdapter

from scripts.langsmith_segundo_intento import lanzar
from src.config import ConfiguracionObservabilidad


def config():
    return ConfiguracionObservabilidad(endpoint="https://api.smith.langchain.com",
                                      clave=SecretStr("valor_sintetico"))


def servidor(monkeypatch, fallo=None, desajuste=False):
    llamadas = []
    runs = {}
    project = str(uuid4())

    def simulado(self, request, **kwargs):
        llamadas.append(request.method)
        respuesta = requests.Response()
        respuesta.url = request.url
        respuesta.status_code = 202
        if request.method in {"POST", "PATCH"}:
            body = json.loads(request.body)
            if request.method == "POST":
                runs[body["id"]] = body
            else:
                runs[body["id"]].update(body)
                if fallo:
                    respuesta.status_code = fallo
            data = {}
        elif "/sessions/" in request.url:
            respuesta.status_code = 200
            data = {"name": "veltri-semana10-demo"}
        else:
            respuesta.status_code = 200
            data = {**runs[request.url.rsplit("/", 1)[1]], "session_id": project}
            if desajuste:
                data["name"] = "valor_no_valido"
        respuesta._content = json.dumps(data).encode()
        return respuesta

    monkeypatch.setattr(HTTPAdapter, "send", simulado)
    return llamadas, runs


def test_lanzador_exito_unico_privado(tmp_path, monkeypatch):
    llamadas, runs = servidor(monkeypatch)
    path = tmp_path / "unico.json"
    result = lanzar(config(), path, clave_rotada_confirmada=True, pausa_verificacion=0)
    assert result["estado"] == "traza_remota_verificada"
    assert result["run_id_verificado"] in runs
    assert len(result["spans_verificados"]) == 9
    assert llamadas.count("POST") == llamadas.count("PATCH") == 9
    assert llamadas.count("GET") == 10
    assert result["optin_final_apagado"]
    assert os.environ["VELTRI_TRACING_ENABLED"] == "0"
    assert os.environ["VELTRI_TRACING_ALLOW_EXTERNAL"] == "0"
    before = len(llamadas)
    with pytest.raises(FileExistsError):
        lanzar(config(), path, clave_rotada_confirmada=True, pausa_verificacion=0)
    assert len(llamadas) == before
    for run in runs.values():
        assert run["inputs"] == run["outputs"] == {}
        assert run["extra"]["metadata"] == {
            "synthetic": True, "model_mode": "mock", "scenario": "stock_demo",
        }
    text = path.read_text()
    assert "valor_sintetico" not in text and "CPU-AMD-5500" not in text
    assert "veltri_demo_sintetica" not in text


@pytest.mark.parametrize("codigo", [400, 401, 403, 429, 500])
def test_primer_error_detiene_sin_lecturas(tmp_path, monkeypatch, codigo):
    llamadas, _ = servidor(monkeypatch, fallo=codigo)
    result = lanzar(config(), tmp_path / "unico.json", clave_rotada_confirmada=True,
                    pausa_verificacion=0)
    assert llamadas == ["POST", "POST", "PATCH"]
    assert result["estado"] == "detenido_sin_reintento"
    assert result["primer_fallo"]["estado"] == codigo
    assert result["primer_fallo"]["etapa"] == "cerrar_span"
    assert result["optin_final_apagado"]
    assert result["run_id_verificado"] is None


def test_202_no_acredita_sin_coincidencia_remota(tmp_path, monkeypatch):
    llamadas, _ = servidor(monkeypatch, desajuste=True)
    result = lanzar(config(), tmp_path / "unico.json", clave_rotada_confirmada=True,
                    pausa_verificacion=0)
    assert result["run_id_verificado"] is None
    assert len(llamadas) == 19
    assert result["optin_final_apagado"]


def test_falta_confirmacion_no_consume_ni_conecta(tmp_path, monkeypatch):
    llamadas, _ = servidor(monkeypatch)
    path = tmp_path / "unico.json"
    with pytest.raises(ValueError, match="rotacion_no_confirmada"):
        lanzar(config(), path)
    assert not path.exists() and not llamadas


def test_modelo_real_bloqueado(tmp_path, monkeypatch):
    from src.agents.base import BaseAgent
    from src.core.llm import MockLLM

    llamadas, _ = servidor(monkeypatch)
    original = BaseAgent.__init__

    def crear_no_mock(self, **kwargs):
        original(self, **kwargs)
        assert isinstance(self._llm, MockLLM)
        self._llm = object()

    monkeypatch.setattr(BaseAgent, "__init__", crear_no_mock)
    result = lanzar(config(), tmp_path / "unico.json", clave_rotada_confirmada=True,
                    pausa_verificacion=0)
    assert result["estado"] == "detenido_sin_reintento"
    assert "GET" not in llamadas
    assert result["optin_final_apagado"]


def test_payload_invalido_no_llega_al_adaptador(monkeypatch):
    from scripts.langsmith_segundo_intento import DetenerIntento, TransporteUnico

    llamadas, _ = servidor(monkeypatch)
    transporte = TransporteUnico()
    with pytest.raises(DetenerIntento):
        transporte.post("https://api.smith.langchain.com/runs", json={"mensaje": "canario"})
    assert not llamadas
    assert "canario" not in json.dumps(transporte.registros)
