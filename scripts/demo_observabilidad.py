"""Demo fija con MockLLM. Offline por defecto; no representa una traza en LangSmith."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Configuracion, cargar_observabilidad  # noqa: E402
from src.core.observabilidad import sesion_sintetica  # noqa: E402
from src.graph.workflow import Orquestador  # noqa: E402


class CapturaLocal:
    """Captura únicamente el contrato seguro emitido, sin SDK ni red."""

    def __init__(self):
        self.eventos = []

    def create_run(self, **datos):
        self.eventos.append({"operacion": "create", **datos})

    def update_run(self, run_id, **datos):
        self.eventos.append({"operacion": "update", "id": run_id, **datos})


def ejecutar_demo(config, cliente_local, *, diagnostico_http=None):
    """Única entrada trazable autorizada por este driver: stock sintético fijo."""
    orquestador = Orquestador(
        configuracion=Configuracion(),
        guiones={
            "A1": [{"accion": "stock", "p": 1.0, "c": 1.0}],
            "A5": [{"accion": "stock", "p": 1.0, "c": 1.0}],
        },
    )
    with sesion_sintetica(config, cliente_local=cliente_local, diagnostico_http=diagnostico_http):
        return orquestador.consultar({
            "consulta": {"mensaje": "Consultar stock de CPU-AMD-5500", "canal": "web",
                         "tenant_id": "veltri_demo_sintetica"},
            "parametros": {"tipo": "stock", "seleccion": {"CPU-AMD-5500": 1}},
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enviar", action="store_true",
                        help="Requiere autorización adicional y los dos opt-in en entorno")
    args = parser.parse_args()
    config = cargar_observabilidad()
    captura = None if args.enviar else CapturaLocal()
    if args.enviar and not (config.habilitada and config.permitir_envio_externo
                           and config.clave.get_secret_value()
                           and config.endpoint in {"https://api.smith.langchain.com",
                                                   "https://eu.api.smith.langchain.com"}
                           and config.proyecto == "veltri-semana10-demo"):
        parser.error("Envío deshabilitado o configuración incompleta; no se ejecutó la demo")
    diagnostico = []
    resultado = ejecutar_demo(config, captura, diagnostico_http=diagnostico)
    print(json.dumps({
        "modo": "envio_solicitado_no_verificado" if args.enviar else "captura_local_sin_envio",
        "modelo": "MockLLM", "status": resultado.respuesta.status,
        "hitl_requerido": resultado.respuesta.hitl_requerido,
        "eventos": captura.eventos if captura is not None else [],
        "diagnostico_http": diagnostico,
        "monitoreo_fallo": any(r["categoria"] != "exito" for r in diagnostico),
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
