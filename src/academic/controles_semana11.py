"""Control en el despacho de herramientas del grafo académico."""

import json

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage

from src.academic.memoria_semana11 import RUTA_HALLAZGOS, evidencia_canonica
from src.core.autonomia import presupuesto_actual
from src.core.prompts import datos_no_confiables

COORDINADOR = "coordinador"
CATALOGO = "DA-Catalogo"
REVISION = "DA-Revision"
TAREAS = ("Recuperar y conservar evidencia", "Contrastar evidencia y cerrar")
PEDIR_CATALOGO = "Consultar fixture sintético"
HERRAMIENTAS_COORDINADOR = frozenset({"write_todos", "task", "write_file", "read_file"})
HERRAMIENTAS_ESPECIALISTA = frozenset({"revisar_fixture_sintetico"})


def _validar_argumentos(nombre: str, args: dict) -> None:
    if nombre == "task":
        if args.keys() != {"subagent_type", "description"}:
            raise ValueError
        destino, descripcion = args["subagent_type"], args["description"]
        if destino == CATALOGO and descripcion == PEDIR_CATALOGO:
            return
        if destino != REVISION or not isinstance(descripcion, str):
            raise ValueError
        datos = json.loads(descripcion)
        if not isinstance(datos, dict) or datos.keys() != {"datos_no_confiables"}:
            raise ValueError
        evidencia = evidencia_canonica(json.dumps(datos["datos_no_confiables"]))
        if descripcion != datos_no_confiables(json.loads(evidencia)):
            raise ValueError
    elif nombre == "write_todos":
        if args.keys() != {"todos"} or not isinstance(args["todos"], list):
            raise ValueError
        todos = args["todos"]
        if len(todos) != len(TAREAS):
            raise ValueError
        for tarea, todo in zip(TAREAS, todos, strict=True):
            if (
                not isinstance(todo, dict) or todo.keys() != {"content", "status"}
                or todo["content"] != tarea
                or todo["status"] not in ("pending", "in_progress", "completed")
            ):
                raise ValueError
    elif nombre in ("write_file", "read_file"):
        claves = {"file_path", "content"} if nombre == "write_file" else {"file_path"}
        if args.keys() != claves or args["file_path"] != RUTA_HALLAZGOS:
            raise ValueError
        if nombre == "write_file":
            evidencia_canonica(args["content"])
    elif args:
        raise ValueError


class ControlesHerramientas(AgentMiddleware):
    """Comprueba el rol real y los argumentos antes de entrar a cada herramienta."""

    def __init__(self, rol: str):
        self.ruta = (COORDINADOR,) if rol == COORDINADOR else (COORDINADOR, rol)
        self.permitidas = (
            HERRAMIENTAS_COORDINADOR if rol == COORDINADOR else HERRAMIENTAS_ESPECIALISTA
        )

    def wrap_tool_call(self, request, handler):
        presupuesto = presupuesto_actual.get()
        if presupuesto is None:
            raise RuntimeError("presupuesto_academico_requerido")
        presupuesto.paso()
        llamada = request.tool_call
        nombre, args = llamada["name"], llamada["args"]
        if nombre == "task" and args.get("subagent_type") in self.ruta:
            presupuesto.detener("delegacion_circular")
        if nombre not in self.permitidas:
            presupuesto.detener("herramienta_no_autorizada")
        try:
            _validar_argumentos(nombre, args)
        except (ValueError, TypeError):
            presupuesto.detener("argumentos_no_autorizados")
        delegacion = (self.ruta, args["subagent_type"]) if nombre == "task" else None
        presupuesto.herramienta(delegacion=delegacion)
        resultado = handler(request)
        if isinstance(resultado, ToolMessage) and resultado.status == "error":
            presupuesto.detener("evidencia_invalida")
        return resultado
