"""Ejercita el proceso Uvicorn real en loopback y su almacenamiento temporal."""

import json
import os
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from time import monotonic, sleep
from types import SimpleNamespace

import pytest

from scripts.veltri_local import ErrorLocal, _proteger_red, instalar
from src.schemas.consulta import ConsultaResponse

RAIZ = Path(__file__).resolve().parents[1]
CLI = RAIZ / "scripts/veltri_local.py"
SELECCION = dict.fromkeys((
    "CPU-AMD-5600", "MB-A520-DDR4", "GPU-RX6600", "RAM-DDR4-8-2666",
    "SSD-NVME-500-G3", "PSU-450", "CASE-01", "COOL-02",
), 1)
ENTORNO = {
    **os.environ, "USE_MOCK_LLM": "0", "VELTRI_TRACING_ENABLED": "1",
    "VELTRI_TRACING_ALLOW_EXTERNAL": "1", "LANGSMITH_TRACING": "true", "PYTHONUTF8": "1",
}


def _comando(datos, *args):
    return [sys.executable, str(CLI), "--datos", str(datos), *args]


def _cli(datos, *args):
    return subprocess.run(
        _comando(datos, *args), cwd=RAIZ, env=ENTORNO, capture_output=True,
        encoding="utf-8", timeout=45, check=False,
    )


def _peticion(puerto, ruta, datos=None, cabeceras=None):
    conexion = HTTPConnection("127.0.0.1", puerto, timeout=15)
    try:
        conexion.request(
            "GET" if datos is None else "POST", ruta,
            body=None if datos is None else json.dumps(datos),
            headers={**(cabeceras or {}), "Content-Type": "application/json"},
        )
        respuesta = conexion.getresponse()
        return respuesta.status, respuesta.read()
    finally:
        conexion.close()


def _puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def _servidor(datos, puerto):
    with (datos.parent / "servidor.log").open("wb") as log:
        proceso = subprocess.Popen(
            _comando(datos, "iniciar", "--puerto", str(puerto)),
            cwd=RAIZ, env=ENTORNO, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            vence = monotonic() + 30
            while not (datos / ".veltri.estado.json").is_file():
                if proceso.poll() is not None or monotonic() > vence:
                    pytest.fail(log.name + ": " + Path(log.name).read_text(encoding="utf-8"))
                sleep(.05)
            yield
            resultado = _cli(datos, "detener")
            assert resultado.returncode == 0, resultado.stderr
            assert proceso.wait(timeout=15) == 0
        finally:
            if proceso.poll() is None:
                _cli(datos, "detener")
            if proceso.poll() is None:
                proceso.terminate()
                proceso.wait(timeout=15)
    assert "detenido" in _cli(datos, "estado").stdout
    assert not (datos / ".veltri.estado.json").exists()


def _consulta(puerto, parametros, tenant="veltri"):
    consulta = {
        "mensaje": "Consulta sintética", "canal": "web",
        "tenant_id": tenant, "parametros": parametros,
    }
    codigo, cuerpo = _peticion(puerto, "/consulta", consulta)
    assert codigo == 200
    return ConsultaResponse.model_validate_json(cuerpo)


def test_despliegue_reinicia_y_conserva_indice_sin_conservar_borradores(tmp_path):
    ruta = tmp_path / "indice"
    puerto = _puerto_libre()
    indice = _cli(ruta, "indexar", "--tenant", "otro")
    assert indice.returncode == 0, indice.stderr
    info = {"tipo": "informacion", "tema": "compatibilidad"}
    pedido = {
        "tipo": "pedido", "confirmar_borrador": True,
        "solicitud": {"cliente": "demo_cliente", "canal": "web", "seleccion": SELECCION},
    }
    with _servidor(ruta, puerto):
        status, home = _peticion(puerto, "/")
        assert status == 200 and b"Veltri" in home
        assert _peticion(puerto, "/js/app.js")[0] == 200
        status, catalogo = _peticion(puerto, "/catalogo")
        assert status == 200 and b"CPU-AMD-5600" in catalogo
        assert "en ejecución" in _cli(ruta, "estado").stdout
        assert _consulta(puerto, info).fuentes == ["data/compatibilidad.json"]
        assert _consulta(puerto, info, "otro").fuentes == ["data/compatibilidad.json"]
        assert "conocimiento_no_disponible" in _consulta(puerto, info, "ausente").motivos
        respuesta = _consulta(puerto, pedido)
        assert respuesta.pedido is not None
        seguimiento = {"tipo": "seguimiento", "clave": respuesta.pedido.pedido.clave}
        assert "seguimiento_solo_demo" in _consulta(puerto, seguimiento).motivos
        assert "borrador_no_encontrado" in _consulta(puerto, seguimiento, "otro").motivos

    with _servidor(ruta, puerto):
        assert _consulta(puerto, info, "otro").fuentes == ["data/compatibilidad.json"]
        assert "conocimiento_no_disponible" in _consulta(puerto, info, "ausente").motivos
        assert "borrador_no_encontrado" in _consulta(puerto, seguimiento).motivos
        assert _consulta(puerto, pedido).pedido.registros_creados == 1


def test_despliegue_rechaza_origen_ajeno_y_procesos_duplicados(tmp_path):
    ruta, puerto = tmp_path / "indice", _puerto_libre()
    with _servidor(ruta, puerto):
        duplicado = _cli(ruta, "iniciar", "--puerto", str(_puerto_libre()))
        assert duplicado.returncode == 1 and "en uso" in duplicado.stderr
        ocupado = _cli(tmp_path / "otro_indice", "iniciar", "--puerto", str(puerto))
        assert ocupado.returncode == 1 and "ocupado" in ocupado.stderr
        for cabeceras in (
            {"Host": "host.example.test"},
            {"Origin": "https://host.example.test"},
            {"Sec-Fetch-Site": "cross-site"},
        ):
            codigo, cuerpo = _peticion(puerto, "/catalogo", cabeceras=cabeceras)
            assert codigo == 403
            assert ConsultaResponse.model_validate_json(cuerpo).motivos == ["origen_no_permitido"]

        def consulta(i):
            if i % 2:
                return _consulta(puerto, {
                    "tipo": "pago", "solicitud": {"pagado_centimos": 1, "total_centimos": 2},
                }, "otro").intencion
            return _consulta(puerto, {
                "tipo": "stock", "seleccion": {"CPU-AMD-5600": 1},
            }).intencion

        with ThreadPoolExecutor(max_workers=4) as pool:
            assert list(pool.map(consulta, range(12))) == ["stock", "pago"] * 6
        codigo, cuerpo = _peticion(puerto, "/consulta", {})
        assert codigo == 422 and ConsultaResponse.model_validate_json(cuerpo).status == "error"


def test_bloqueo_de_egreso_permite_loopback_y_rechaza_dns_externo():
    sock = SimpleNamespace(family=socket.AF_INET)
    _proteger_red("socket.connect", (sock, ("127.0.0.1", 8765)))
    _proteger_red("socket.getaddrinfo", ("localhost", 8765))
    with pytest.raises(PermissionError, match="Egreso"):
        _proteger_red("socket.connect", (sock, ("192.0.2.5", 443)))
    with pytest.raises(PermissionError, match="Egreso"):
        _proteger_red("socket.sendto", (sock, ("192.0.2.5", 53)))
    with pytest.raises(PermissionError, match="Egreso"):
        _proteger_red("socket.getaddrinfo", ("ejemplo.example.test", 443))


def test_instalador_preserva_destino_ajeno(tmp_path):
    archivo = tmp_path / "existente.txt"
    archivo.write_text("conservar", encoding="utf-8")
    with pytest.raises(ErrorLocal, match="contiene archivos"):
        instalar(tmp_path, desarrollo=False)
    assert archivo.read_text(encoding="utf-8") == "conservar"



def test_comprobar_valida_dependencias_y_fuerza_perfil_local(tmp_path):
    resultado = _cli(tmp_path, "comprobar")
    assert resultado.returncode == 0, resultado.stderr
    assert "No broken requirements" in resultado.stdout
    assert "MockLLM activo y trazas externas desactivadas" in resultado.stdout
