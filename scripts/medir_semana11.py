"""Benchmark local de Veltri, con MockLLM, sockets externos bloqueados y Chroma temporal."""

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter, process_time
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
SELECCION = dict.fromkeys((
    "CPU-AMD-5600", "MB-A520-DDR4", "GPU-RX6600", "RAM-DDR4-8-2666",
    "SSD-NVME-500-G3", "PSU-450", "CASE-01", "COOL-02",
), 1)
TENANTS = {"medicion_a": "marcadoruno", "medicion_b": "marcadordos"}


def resumen(muestras: list[float]) -> dict:
    """Calcula p95 por rango más próximo sin interpolar series pequeñas."""
    orden = sorted(muestras)
    return {
        "n": len(orden), "p50_ms": round(median(orden), 3),
        "p95_ms": round(orden[ceil(len(orden) * .95) - 1], 3),
    }


def _tiempo(funcion, *args):
    inicio = perf_counter()
    resultado = funcion(*args)
    return (perf_counter() - inicio) * 1000, resultado


def medir(funcion: Callable, repeticiones: int, trabajadores: int = 1) -> dict:
    inicio, cpu = perf_counter(), process_time()
    if trabajadores == 1:
        muestras = [_tiempo(funcion, i)[0] for i in range(repeticiones)]
    else:
        with ThreadPoolExecutor(max_workers=trabajadores) as pool:
            muestras = list(pool.map(lambda i: _tiempo(funcion, i)[0], range(repeticiones)))
    pared = perf_counter() - inicio
    return {
        **resumen(muestras), "cpu_s": round(process_time() - cpu, 6),
        "pared_s": round(pared, 6), "operaciones_s": round(repeticiones / pared, 2),
    }


def _sin_red(original):
    def conectar(sock, direccion):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError("La medición solo admite ejecución local en proceso")
        return original(sock, direccion)
    return conectar


def _arranque() -> dict:
    inicio, cpu = perf_counter(), process_time()
    procesos = [
        _tiempo(subprocess.run, [sys.executable, str(Path(__file__).resolve()), "--arranque"])
        for _ in range(5)
    ]
    if any(proceso.returncode for _, proceso in procesos):
        raise RuntimeError("Falló el arranque local")
    return {**resumen([ms for ms, _ in procesos]),
            "pared_s": round(perf_counter() - inicio, 6), "cpu_lanzador_s": round(
                process_time() - cpu, 6,
            )}


def _comercial() -> dict:
    from fastapi.testclient import TestClient

    from src.api.main import app
    from src.core.observabilidad import recursos_recientes
    from src.schemas.consulta import ConsultaResponse

    tenants = tuple(TENANTS)
    with TestClient(app) as cliente:
        def consultar(i):
            sku = ("CPU-AMD-5600", "CPU-AMD-5500")[i % 2]
            respuesta = cliente.post("/consulta", json={
                "mensaje": "Consulta de stock", "canal": "web", "tenant_id": tenants[i % 2],
                "parametros": {"tipo": "stock", "seleccion": {sku: 1}},
            })
            respuesta.raise_for_status()
            salida = ConsultaResponse.model_validate(respuesta.json())
            assert salida.stock is not None and salida.stock.disponible == (i % 2 == 0)
            assert salida.hitl_requerido == (i % 2 > 0) and not salida.genera_proforma
            if i % 2:
                assert salida.stock.faltantes[0].sku == sku

        consultar(0)
        secuencial = medir(consultar, 40)
        concurrente = medir(consultar, 40, 4)
    metricas = [datos for _, datos in recursos_recientes()[-80:]]
    assert len(metricas) == 80 and all(d["modelos"] == 2 for d in metricas)
    return {"secuencial": secuencial, "concurrente": concurrente, "recursos_por_variante": {
        "stock_disponible": metricas[0], "stock_agotado": metricas[1],
    }}


def _agentes() -> dict:
    from src.core.autonomia import LIMITES_COMERCIALES, controlar_ejecucion
    from src.tools.catalogo import Catalogo
    from src.tools.registro import RegistroPorTenant
    from tests.test_agentes import agente, ejecutar, entradas

    catalogo, registro = Catalogo(), RegistroPorTenant()
    solicitudes = entradas(SELECCION)
    borrador = ejecutar(6, agente(6), solicitudes[6], catalogo, registro)
    solicitudes[7] = solicitudes[7].model_copy(update={"clave": borrador.resultado.pedido.clave})
    def medir_agente(indice, solicitud):
        instancia = agente(indice, repeticiones=21)
        muestras = []

        def consultar(_):
            with controlar_ejecucion(LIMITES_COMERCIALES) as presupuesto:
                salida = ejecutar(indice, instancia, solicitud, catalogo, registro)
                muestras.append(presupuesto.metricas(hitl=False))
                assert salida.agente == f"A{indice + 1}"

        consultar(0)
        return {**medir(consultar, 20), "recursos": muestras[-1]}

    return {f"A{i + 1}": medir_agente(i, solicitud) for i, solicitud in enumerate(solicitudes)}


def _academico() -> dict:
    from src.academic.controles_semana11 import ControlesHerramientas
    from src.academic.deep_agents_semana11 import AdaptadorSemana11, ejecutar_semana11

    por_rol = defaultdict(list)
    delegaciones = defaultdict(list)
    recursos = []
    generar = AdaptadorSemana11._generate
    despachar = ControlesHerramientas.wrap_tool_call

    def cronometrar(self, *args, **kwargs):
        inicio = perf_counter()
        salida = generar(self, *args, **kwargs)
        por_rol[self._rol].append((perf_counter() - inicio) * 1000)
        return salida

    def consultar(_):
        respuesta = ejecutar_semana11({})
        assert "interrupcion" not in respuesta
        recursos.append(respuesta["recursos"])

    def cronometrar_despacho(self, request, handler):
        inicio = perf_counter()
        salida = despachar(self, request, handler)
        if request.tool_call["name"] == "task":
            rol = request.tool_call["args"]["subagent_type"]
            delegaciones[rol].append((perf_counter() - inicio) * 1000)
        return salida

    consultar(0)
    with (
        patch.object(AdaptadorSemana11, "_generate", cronometrar),
        patch.object(ControlesHerramientas, "wrap_tool_call", cronometrar_despacho),
    ):
        medicion = medir(consultar, 5)
    return {
        **medicion, "modelo_por_rol": {rol: resumen(ms) for rol, ms in por_rol.items()},
        "delegacion_por_rol": {rol: resumen(ms) for rol, ms in delegaciones.items()},
        "recursos": recursos[-1],
    }


def _rag(ruta: Path) -> dict:
    from src.knowledge.almacen import Almacen
    from src.knowledge.documentos import Fragmento, construir_documentos

    almacen = Almacen(ruta)
    tenants = tuple(TENANTS)
    indice = {}
    for tenant, marcador in TENANTS.items():
        fuente = "data/politicas.md"
        documento = Fragmento(
            marcador, marcador, fuente, fuente + "#" + marcador,
            hashlib.sha256(marcador.encode()).hexdigest(),
        )
        indice[tenant] = almacen.reemplazar(
            tenant, [*construir_documentos(tenant), documento],
        )["fragmentos"]

    def consultar(i):
        tenant, ajeno = tenants[i % 2], tenants[(i + 1) % 2]
        propios = almacen.buscar(tenant, TENANTS[tenant])
        assert [r["id"] for r in propios] == [TENANTS[tenant]]
        assert not almacen.buscar(tenant, TENANTS[ajeno])

    consultar(0)
    secuencial = medir(consultar, 40)
    concurrente = medir(consultar, 40, 4)
    archivos = [p.stat() for p in ruta.rglob("*") if p.is_file()]
    return {
        "fragmentos": indice, "consultas_por_operacion": 2,
        "secuencial": secuencial, "concurrente": concurrente,
        "bytes_indice": sum(f.st_size for f in archivos),
        "bytes_asignados_indice": sum(f.st_blocks * 512 for f in archivos),
        "violaciones": 0,
    }


def medir_local() -> dict:
    import resource

    uso_antes, inicio = resource.getrusage(resource.RUSAGE_CHILDREN), process_time()
    arranque = _arranque()
    uso_despues = resource.getrusage(resource.RUSAGE_CHILDREN)
    arranque["cpu_hijos_s"] = round(
        uso_despues.ru_utime + uso_despues.ru_stime - uso_antes.ru_utime - uso_antes.ru_stime, 6,
    )
    with TemporaryDirectory() as carpeta:
        http = _comercial()
        agentes = _agentes()
        academico = _academico()
        rag = _rag(Path(carpeta))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    objetivos = {
        "arranque_p95_ms": (arranque["p95_ms"], 4000),
        "http_secuencial_p95_ms": (http["secuencial"]["p95_ms"], 100),
        "http_concurrente_p95_ms": (http["concurrente"]["p95_ms"], 200),
        "rag_concurrente_p95_ms": (rag["concurrente"]["p95_ms"], 250),
        "rss_pico_mib": (rss / 1024, 400),
        "indice_bytes": (rag["bytes_indice"], 16 * 1024 * 1024),
        "violaciones_aislamiento": (rag["violaciones"], 0),
    }
    return {
        "entorno": {
            "python": platform.python_version(), "plataforma": platform.platform(),
            "cpu_visibles": os.cpu_count(), "cpu_afinidad": len(os.sched_getaffinity(0)),
        },
        "objetivos_locales_propuestos": {
            nombre: {"maximo": maximo, "cumple": valor <= maximo}
            for nombre, (valor, maximo) in objetivos.items()
        },
        "arranque": arranque, "http": http, "agentes": agentes, "academico": academico,
        "rag": rag, "recursos_proceso": {
            "cpu_s": round(process_time() - inicio, 6),
            "rss_pico_mib": round(rss / 1024, 3),
            "bytes_corpus": sum(p.stat().st_size for p in (RAIZ / "data").glob("*") if p.is_file()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arranque", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    os.environ.update(USE_MOCK_LLM="1", VELTRI_TRACING_ENABLED="0",
                      VELTRI_TRACING_ALLOW_EXTERNAL="0", LANGSMITH_TRACING="false",
                      LANGCHAIN_TRACING_V2="false")
    if sys.platform != "linux":
        parser.error("El perfil de CPU, RSS y bloques asignados está definido para Linux")
    with patch.object(socket.socket, "connect", _sin_red(socket.socket.connect)):
        if args.arranque:
            from src.api.main import app

            assert app.state.orquestador._servicios.configuracion.usar_mock
        else:
            print(json.dumps(medir_local(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
