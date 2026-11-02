"""Lanzador de autorización de un solo uso; no ejecutarlo sin permiso de envío."""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import UUID

from urllib3.util.retry import Retry

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.demo_observabilidad import ejecutar_demo  # noqa: E402
from src.config import cargar_observabilidad  # noqa: E402
from src.core import observabilidad as obs  # noqa: E402
from src.core.diagnostico_http import (  # noqa: E402
    ErrorTransporteSeguro,
    TransporteDiagnostico,
)
from src.core.llm import MockLLM  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
REGISTRO = RAIZ / "docs/evidencias/semana10-fase43/ejecucion-unica.json"
META = {"synthetic": True, "model_mode": "mock", "scenario": "stock_demo"}
NOMBRES = {"consulta", "seguridad", "A1.plan_mock", "validar_plan", "dominio",
           "A5.plan_mock", "comprobar_stock", "decidir", "responder"}
FLAGS = {"VELTRI_TRACING_ENABLED": "0", "VELTRI_TRACING_ALLOW_EXTERNAL": "0",
         "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false"}


class DetenerIntento(BaseException):
    """Detiene el procedimiento, incluso si el SDK intenta ocultar el fallo."""


def validar_cuerpo(cuerpo, method):
    """Lista cerrada del wire format: ni args ni resultados comerciales."""
    permitidos = {"id", "name", "run_type", "inputs", "outputs", "start_time", "end_time",
                  "parent_run_id", "trace_id", "dotted_order", "session_name", "session_id",
                  "extra", "tags", "error"}
    if not isinstance(cuerpo, dict) or set(cuerpo) - permitidos:
        raise ErrorTransporteSeguro("payload_no_permitido")
    if cuerpo.get("session_name") != "veltri-semana10-demo":
        raise ErrorTransporteSeguro("proyecto_no_permitido")
    if cuerpo.get("session_id") is not None:
        raise ErrorTransporteSeguro("proyecto_no_permitido")
    if cuerpo.get("name") not in NOMBRES or cuerpo.get("run_type") != "chain":
        raise ErrorTransporteSeguro("operacion_no_permitida")
    if cuerpo.get("extra") != {"metadata": META} or cuerpo.get("tags") not in (None, []):
        raise ErrorTransporteSeguro("metadata_no_permitida")
    for campo in ("inputs", "outputs"):
        if cuerpo.get(campo) not in (None, {}):
            raise ErrorTransporteSeguro("cuerpo_no_vacio")
    if cuerpo.get("error") not in (None, "operation_failed"):
        raise ErrorTransporteSeguro("error_no_permitido")
    for campo in ("id", "trace_id", "parent_run_id"):
        if cuerpo.get(campo) is not None:
            UUID(cuerpo[campo])
    for campo in ("start_time", "end_time"):
        if cuerpo.get(campo):
            if datetime.fromisoformat(cuerpo[campo]).tzinfo is None:
                raise ErrorTransporteSeguro("tiempo_no_valido")
    segmentos = cuerpo["dotted_order"].split(".")
    for segmento in segmentos:
        tiempo, identificador = segmento.split("Z")
        datetime.strptime(tiempo, "%Y%m%dT%H%M%S%f")
        UUID(identificador)
    if segmentos[-1].split("Z")[-1] != cuerpo["id"]:
        raise ErrorTransporteSeguro("orden_no_valido")
    if segmentos[0].split("Z")[-1] != cuerpo["trace_id"]:
        raise ErrorTransporteSeguro("orden_no_valido")
    if method == "POST" and cuerpo.get("inputs") != {}:
        raise ErrorTransporteSeguro("inputs_no_vacios")
    if method == "PATCH" and cuerpo.get("outputs") != {}:
        raise ErrorTransporteSeguro("outputs_no_vacios")


class TransporteUnico(TransporteDiagnostico):
    """Control final de cuerpos antes del socket, presupuesto y manifiesto sintético."""

    def __init__(self):
        super().__init__()
        self.altas = {}
        self.cierres = set()
        self.escritura_habilitada = True
        self.lecturas = set()

    def _destino(self, request) -> tuple[str, str]:
        url = urlsplit(request.url)
        if (url.scheme != "https" or url.netloc != "api.smith.langchain.com"
                or url.query or url.fragment):
            raise ErrorTransporteSeguro("destino_no_permitido")
        if request.method == "GET" and url.path.startswith("/sessions/"):
            UUID(url.path.removeprefix("/sessions/"))
            return "/sessions/{project_id}", "verificar_proyecto"
        return super()._destino(request)

    def send(self, request, **kwargs):
        if self.primer_fallo is not None:
            raise DetenerIntento("primer_fallo_conservado")
        cuerpo = None
        try:
            self._destino(request)
            if request.method in {"POST", "PATCH"}:
                if not self.escritura_habilitada:
                    raise ErrorTransporteSeguro("presupuesto_agotado")
                cuerpo = json.loads(request.body)
                validar_cuerpo(cuerpo, request.method)
                run_id = cuerpo["id"]
                if request.method == "POST":
                    if run_id in self.altas or len(self.altas) >= 9:
                        raise ErrorTransporteSeguro("alta_duplicada")
                    padre = cuerpo.get("parent_run_id")
                    if padre and padre not in self.altas:
                        raise ErrorTransporteSeguro("padre_no_creado")
                    if not padre and self.altas:
                        raise ErrorTransporteSeguro("segunda_raiz")
                else:
                    if run_id not in self.altas or run_id in self.cierres:
                        raise ErrorTransporteSeguro("cierre_duplicado")
                    if urlsplit(request.url).path != "/runs/" + run_id:
                        raise ErrorTransporteSeguro("id_no_corresponde")
                    for campo in (
                        "trace_id", "parent_run_id", "name", "dotted_order", "start_time",
                    ):
                        if cuerpo.get(campo) != self.altas[run_id].get(campo):
                            raise ErrorTransporteSeguro("contexto_no_corresponde")
                    if datetime.fromisoformat(cuerpo["end_time"]) < datetime.fromisoformat(
                        cuerpo["start_time"]
                    ):
                        raise ErrorTransporteSeguro("tiempo_no_valido")
            else:
                if self.escritura_habilitada or request.url in self.lecturas:
                    raise ErrorTransporteSeguro("lectura_no_permitida")
                if len(self.lecturas) >= 10:
                    raise ErrorTransporteSeguro("presupuesto_agotado")
                self.lecturas.add(request.url)
        except Exception:
            self._registrar("OTRO", "/ruta_validada", None, "configuracion", "validar_payload")
            raise DetenerIntento("validacion_local_fallida") from None
        try:
            response = super().send(request, **kwargs)
        except ErrorTransporteSeguro:
            raise DetenerIntento("http_fallido") from None
        if request.method == "POST" and cuerpo is not None:
            # Solo los atributos cerrados ya validados, nunca headers ni cuerpos originales.
            self.altas[cuerpo["id"]] = cuerpo
        elif request.method == "PATCH" and cuerpo is not None:
            self.cierres.add(cuerpo["id"])
        return response


def _guardar(path, estado):
    path.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lanzar(config, registro=REGISTRO, *, clave_rotada_confirmada=False,
           transporte=None, pausa_verificacion=3):
    """No reutilizar el registro: creación exclusiva consume una autorización."""
    if not clave_rotada_confirmada:
        raise ValueError("rotacion_no_confirmada")
    if not (config.clave.get_secret_value().strip() and not config.habilitada
            and not config.permitir_envio_externo and config.proyecto == "veltri-semana10-demo"
            and config.endpoint == "https://api.smith.langchain.com"):
        raise ValueError("configuracion_no_preparada")
    registro.parent.mkdir(parents=True, exist_ok=True)
    estado = {"estado": "autorizacion_consumida", "intentos_demo": 0,
              "inicio_utc": datetime.now(timezone.utc).isoformat(), "run_id_verificado": None,
              "spans_verificados": [], "optin_final_apagado": False}
    with registro.open("x", encoding="utf-8") as archivo:
        json.dump(estado, archivo)
    transporte = transporte if transporte is not None else TransporteUnico()
    sdk_original = obs.Client
    clientes = []
    logging_level = logging.root.manager.disable

    class ClienteSinReintentos(sdk_original):
        def request_with_retries(self, *args, **kwargs):
            kwargs["stop_after_attempt"] = 1
            return super().request_with_retries(*args, **kwargs)

    def cliente_controlado(**kwargs):
        kwargs["session"] = transporte
        cliente = ClienteSinReintentos(**kwargs, retry_config=Retry(total=0, redirect=0))
        clientes.append(cliente)
        return cliente

    from src.agents.base import BaseAgent
    plan_original = BaseAgent._plan

    def plan_mock(agente, datos):
        if not isinstance(agente._llm, MockLLM):
            raise DetenerIntento("modelo_no_mock")
        return plan_original(agente, datos)

    try:
        logging.disable(logging.CRITICAL)
        os.environ.update({**FLAGS, "VELTRI_TRACING_ENABLED": "1",
                           "VELTRI_TRACING_ALLOW_EXTERNAL": "1",
                           "VELTRI_TRACING_SYNTHETIC_ONLY": "1", "USE_MOCK_LLM": "1"})
        activa = config.model_copy(update={"habilitada": True, "permitir_envio_externo": True})
        estado["optin_previo_envio"] = {"habilitada": True, "externo": True, "solo_sintetico": True}
        estado["intentos_demo"] = 1
        _guardar(registro, estado)
        with (patch.object(obs, "Client", cliente_controlado),
              patch.object(BaseAgent, "_plan", plan_mock)):
            salida = ejecutar_demo(activa, None)
        transporte.escritura_habilitada = False
        os.environ.update(FLAGS)
        if len(transporte.altas) != 9 or len(transporte.cierres) != 9:
            raise DetenerIntento("traza_local_incompleta")
        estado["resultado_comercial"] = salida.respuesta.status
        estado["hitl_requerido"] = salida.respuesta.hitl_requerido
        estado["altas_aceptadas"] = len(transporte.altas)
        estado["cierres_aceptados"] = len(transporte.cierres)
        if pausa_verificacion:
            time.sleep(pausa_verificacion)
        raiz = next(r for r in transporte.altas.values() if r.get("parent_run_id") is None)
        proyecto = None
        for alta in transporte.altas.values():
            response = transporte.get(
                config.endpoint + "/runs/" + alta["id"],
                headers={"x-api-key": config.clave.get_secret_value()}, timeout=10,
            )
            remoto = response.json()
            for campo in ("id", "name", "trace_id", "parent_run_id", "dotted_order"):
                if remoto.get(campo) != alta.get(campo):
                    raise DetenerIntento("verificacion_no_coincide")
            if remoto.get("inputs") not in (None, {}) or remoto.get("outputs") not in (None, {}):
                raise DetenerIntento("cuerpo_remoto_no_vacio")
            if (remoto.get("extra") or {}).get("metadata") != META or remoto.get("error"):
                raise DetenerIntento("metadata_o_error_remoto")
            inicio = datetime.fromisoformat(remoto["start_time"].replace("Z", "+00:00"))
            fin = datetime.fromisoformat(remoto["end_time"].replace("Z", "+00:00"))
            if fin < inicio:
                raise DetenerIntento("tiempo_remoto_no_valido")
            estado["spans_verificados"].append({
                "id": remoto["id"], "name": remoto["name"],
                "parent_run_id": remoto.get("parent_run_id"), "trace_id": remoto["trace_id"],
                "duracion_segundos": (fin - inicio).total_seconds(), "inputs": {}, "outputs": {},
                "metadata": META,
            })
            if remoto["id"] == raiz["id"]:
                proyecto = str(UUID(remoto["session_id"]))
        if proyecto is None:
            raise DetenerIntento("proyecto_remoto_no_verificado")
        response = transporte.get(config.endpoint + "/sessions/" + proyecto,
                                 headers={"x-api-key": config.clave.get_secret_value()}, timeout=10)
        if response.json().get("name") != config.proyecto:
            raise DetenerIntento("proyecto_remoto_no_coincide")
        estado["run_id_verificado"] = raiz["id"]
        estado["estado"] = "traza_remota_verificada"
    except BaseException as error:
        estado["estado"] = "detenido_sin_reintento"
        estado["categoria_fallo"] = (
            "http" if transporte.primer_fallo else
            "verificacion_o_ejecucion"
        )
        # Nunca serializar str(error), repr(error), response o traceback.
        del error
    finally:
        transporte.escritura_habilitada = False
        os.environ.update(FLAGS)
        estado["optin_final_apagado"] = all(os.environ[k] == v for k, v in FLAGS.items())
        estado["diagnostico_http"] = transporte.registros
        estado["primer_fallo"] = transporte.primer_fallo
        estado["fin_utc"] = datetime.now(timezone.utc).isoformat()
        _guardar(registro, estado)
        transporte.close()
        for cliente in clientes:
            cliente.close()
        logging.disable(logging_level)
    return estado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enviar-autorizado", action="store_true")
    parser.add_argument("--rotacion-confirmada", action="store_true")
    args = parser.parse_args()
    if not args.enviar_autorizado or not args.rotacion_confirmada:
        parser.error("Se requieren autorización expresa y confirmación de rotación")
    try:
        resultado = lanzar(cargar_observabilidad(), clave_rotada_confirmada=True)
    except FileExistsError:
        print('{"estado":"bloqueado_autorizacion_consumida"}')
        return 1
    except Exception:
        print('{"estado":"configuracion_invalida_sin_envio"}')
        return 1
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado["estado"] == "traza_remota_verificada" else 1


if __name__ == "__main__":
    raise SystemExit(main())
