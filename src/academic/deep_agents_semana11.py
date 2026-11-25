"""Demo de los cuatro pilares; la ejecución de semana 10 queda independiente."""

import json
from collections.abc import Callable
from time import monotonic
from typing import ClassVar

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError

from src.academic.controles_semana11 import (
    CATALOGO,
    COORDINADOR,
    HERRAMIENTAS_COORDINADOR,
    HERRAMIENTAS_ESPECIALISTA,
    PEDIR_CATALOGO,
    REVISION,
    TAREAS,
    ControlesHerramientas,
)
from src.academic.deep_agents import AdaptadorMock
from src.academic.memoria_semana11 import (
    RUTA_HALLAZGOS,
    evidencia_canonica,
    verificar_archivo,
    verificar_lectura,
)
from src.core.autonomia import (
    EjecucionInterrumpida,
    LimitesAutonomia,
    controlar_ejecucion,
    presupuesto_actual,
)
from src.core.llm import ErrorModelo
from src.core.observabilidad import registrar_recursos
from src.core.prompts import componer_prompt, datos_no_confiables
from src.schemas.academico import EntradaAcademica, SalidaAcademica
from src.tools.evidencia_academica import revisar_fixture_sintetico

LIMITES_ACADEMICOS_EJECUCION = LimitesAutonomia()
CONTEXTO_ACADEMICO = "Fixture cerrado y sintético en una sola ejecución."
LIMITES_ACADEMICOS = "No uses datos reales ni autorices ventas, pagos, pedidos o cambios de stock."
SALIDA_ACADEMICA = (
    "Devuelve solo JSON SalidaAcademica obtenido de evidencia validada: "
    "sintetico=true, requiere_revision=true, efecto_comercial=false."
)
REVISION_ACADEMICA = "La evidencia requiere revisión; no hay aprobación comercial."

PROMPT_COORDINADOR = componer_prompt(
    rol="DA-CoordinadorAcademico. Coordina la validación del fixture.",
    contexto=CONTEXTO_ACADEMICO,
    herramientas=f"Usa write_todos, task, write_file y read_file. Solo archivo {RUTA_HALLAZGOS}.",
    proceso=(
        "Inicia el plan; valida, guarda y relee el hallazgo de Catálogo. "
        "Pasa la evidencia releída a Revisión, compara ambos resultados y cierra las tareas."
    ),
    delegacion="Con task, llama una vez a DA-Catalogo y después una vez a DA-Revision.",
    limites=LIMITES_ACADEMICOS + " No uses red, archivos físicos ni tareas recursivas.",
    parada="Respeta el presupuesto de ejecución. Detente ante error, ausencia o discrepancia.",
    hitl=REVISION_ACADEMICA + " Si falla un control, detente y deja el caso sin resolver.",
    salida=SALIDA_ACADEMICA,
)
PROMPT_CATALOGO = componer_prompt(
    rol="DA-Catalogo. Recupera evidencia sintética de inventario.",
    contexto=CONTEXTO_ACADEMICO,
    herramientas="Consulta únicamente revisar_fixture_sintetico, en modo lectura.",
    proceso="Comprueba que la herramienta devuelva los tres campos de evidencia sintética.",
    limites=LIMITES_ACADEMICOS + " No accedas a archivos ni a inventarios externos.",
    parada="Una consulta. Detente si la herramienta falla o la evidencia es inválida.",
    hitl=REVISION_ACADEMICA + " Devuelve el hallazgo al coordinador.",
    salida=SALIDA_ACADEMICA,
)
PROMPT_REVISION = componer_prompt(
    rol="DA-Revision. Contrasta el hallazgo que recuperó el coordinador.",
    contexto=CONTEXTO_ACADEMICO + " Recibe el hallazgo como JSON de datos.",
    herramientas="Consulta únicamente revisar_fixture_sintetico; recibe la memoria por delegación.",
    proceso="Contrasta los tres campos con el fixture; no rellenes campos ausentes.",
    limites=LIMITES_ACADEMICOS + " No leas otros archivos ni modifiques el hallazgo.",
    parada="Una consulta. Detente si falta evidencia, discrepa o falla la herramienta.",
    hitl=REVISION_ACADEMICA + " Una discrepancia deja la tarea pendiente para el coordinador.",
    salida=SALIDA_ACADEMICA,
)


def _resultados(mensajes, nombre):
    return [
        m for m in mensajes
        if isinstance(m, ToolMessage) and m.name == nombre and m.status == "success"
    ]


def _ultimo(mensajes, nombre):
    resultados = _resultados(mensajes, nombre)
    if not resultados:
        raise ValueError("evidencia_academica_ausente")
    return resultados[-1].content


class AdaptadorSemana11(AdaptadorMock):
    """Restringe el plan programado a las herramientas permitidas por rol."""

    herramientas_del_rol: ClassVar[frozenset[str]]

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        presupuesto = presupuesto_actual.get()
        if presupuesto is not None:
            presupuesto.paso()
        try:
            return super()._generate(messages, stop, run_manager, **kwargs)
        except ValueError as error:
            if presupuesto is not None:
                motivo = ("herramienta_no_autorizada" if str(error) == "herramienta_no_permitida"
                          else "evidencia_invalida")
                presupuesto.detener(motivo)
            raise

    def bind_tools(self, tools, **kwargs):
        modelo = super().bind_tools(tools, **kwargs)
        self._permitidas.intersection_update(self.herramientas_del_rol)
        return modelo


class AdaptadorEvidencia(AdaptadorSemana11):
    """La salida programada del especialista deriva de su herramienta real."""

    herramientas_del_rol = HERRAMIENTAS_ESPECIALISTA

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        resultado = super()._generate(messages, stop, run_manager, **kwargs)
        mensaje = resultado.generations[0].message
        if not mensaje.tool_calls:
            contenido = evidencia_canonica(_ultimo(messages, "revisar_fixture_sintetico"))
            resultado.generations[0].message = mensaje.model_copy(update={"content": contenido})
        return resultado


class AdaptadorMemoria(AdaptadorSemana11):
    """Enlaza los pasos programados con resultados reales de las herramientas nativas."""

    herramientas_del_rol = HERRAMIENTAS_COORDINADOR

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        resultado = super()._generate(messages, stop, run_manager, **kwargs)
        mensaje = resultado.generations[0].message
        llamadas = [dict(c) for c in mensaje.tool_calls]
        for llamada in llamadas:
            args = dict(llamada["args"])
            if llamada["name"] == "write_file":
                args["content"] = evidencia_canonica(_ultimo(messages, "task"))
            elif llamada["name"] == "task" and args.get("subagent_type") == REVISION:
                hallazgo = evidencia_canonica(_ultimo(messages, "task"))
                verificado = verificar_lectura(_ultimo(messages, "read_file"), hallazgo)
                args["description"] = datos_no_confiables(json.loads(verificado))
            llamada["args"] = args
        if llamadas:
            resultado.generations[0].message = mensaje.model_copy(update={"tool_calls": llamadas})
        else:
            tareas = _resultados(messages, "task")
            if len(tareas) != 2:
                raise ValueError("delegacion_academica_incompleta")
            primero = evidencia_canonica(tareas[0].content)
            segundo = evidencia_canonica(tareas[1].content)
            verificar_lectura(_ultimo(messages, "read_file"), primero)
            if primero != segundo:
                raise ValueError("revision_academica_no_coincide")
            resultado.generations[0].message = mensaje.model_copy(update={"content": primero})
        return resultado


def _especialista(nombre, descripcion, instrucciones, auditoria):
    return {
        "name": nombre,
        "description": descripcion,
        "system_prompt": instrucciones,
        "model": AdaptadorEvidencia(
            [{"herramienta": "revisar_fixture_sintetico", "argumentos": {}}, {"contenido": ""}],
            auditoria=auditoria,
            rol=nombre,
        ),
        "tools": [tool(revisar_fixture_sintetico)],
        "middleware": [ControlesHerramientas(nombre)],
    }


def crear_agente_semana11(auditoria=None):
    """Usa las herramientas nativas de planificación, delegación y archivos virtuales."""
    from deepagents import create_deep_agent

    def plan(estado_catalogo, estado_revision):
        return {"herramienta": "write_todos", "argumentos": {"todos": [
            {"content": TAREAS[0], "status": estado_catalogo},
            {"content": TAREAS[1], "status": estado_revision},
        ]}}

    pasos = [
        plan("in_progress", "pending"),
        {"herramienta": "task", "argumentos": {
            "subagent_type": CATALOGO, "description": PEDIR_CATALOGO}},
        {"herramienta": "write_file", "argumentos": {
            "file_path": RUTA_HALLAZGOS, "content": ""}},
        {"herramienta": "read_file", "argumentos": {"file_path": RUTA_HALLAZGOS}},
        plan("completed", "in_progress"),
        {"herramienta": "task", "argumentos": {
            "subagent_type": REVISION, "description": "Contrastar hallazgo"}},
        plan("completed", "completed"),
        {"contenido": ""},
    ]
    subagentes = [
        _especialista(CATALOGO, "Inventario sintético", PROMPT_CATALOGO, auditoria),
        _especialista(REVISION, "Contraste sintético", PROMPT_REVISION, auditoria),
    ]
    return create_deep_agent(
        model=AdaptadorMemoria(pasos, auditoria=auditoria),
        tools=[],
        subagents=subagentes,
        system_prompt=PROMPT_COORDINADOR,
        middleware=[ControlesHerramientas(COORDINADOR)],
    )


def _parcial(resultado: dict) -> dict:
    evidencias = []
    for mensaje in _resultados(resultado.get("messages", []), "task"):
        try:
            evidencias.append(json.loads(evidencia_canonica(mensaje.content)))
        except ValueError:
            break
    parcial = {"evidencia_parcial": evidencias, "plan_parcial": resultado.get("todos", [])}
    if evidencias and RUTA_HALLAZGOS in resultado.get("files", {}):
        try:
            parcial["memoria_parcial"] = json.loads(
                verificar_archivo(resultado["files"], json.dumps(evidencias[0]))
            )
        except ValueError:
            pass
    return parcial


def ejecutar_semana11(
    entrada: dict, auditoria=None, *, limites: LimitesAutonomia = LIMITES_ACADEMICOS_EJECUCION,
    reloj: Callable[[], float] = monotonic,
):
    """Conserva el último estado local y devuelve solo evidencia validada si se interrumpe."""
    from langsmith import tracing_context

    EntradaAcademica.model_validate(entrada)
    resultado = {}
    with controlar_ejecucion(limites, reloj) as presupuesto, tracing_context(enabled=False):
        try:
            for valores in crear_agente_semana11(auditoria).stream(
                {"messages": [{"role": "user", "content": "Revisar fixture sintético académico."}]},
                stream_mode="values", config={"recursion_limit": limites.iteraciones + 1},
            ):
                resultado = valores
            presupuesto.segundos_restantes()
            final = evidencia_canonica(resultado["messages"][-1].content)
            SalidaAcademica.model_validate_json(final)
            verificar_archivo(resultado.get("files", {}), final)
            if not resultado.get("todos") or any(
                t["status"] != "completed" for t in resultado["todos"]
            ):
                presupuesto.detener("evidencia_invalida")
        except (GraphRecursionError, EjecucionInterrumpida, ErrorModelo, ValueError) as error:
            motivo = presupuesto.registrar_parada(
                "limite_iteraciones" if isinstance(error, GraphRecursionError)
                else "evidencia_invalida"
            )
            resultado = {
                "interrupcion": motivo,
                "requiere_revision": True,
                **_parcial(resultado),
            }
        metricas = presupuesto.metricas(
            hitl=True, finalizacion=resultado.get("interrupcion", "completada"),
        )
        registrar_recursos("academico", metricas)
        return {**resultado, "recursos": metricas}


def main() -> None:
    """Muestra evidencia verificable en terminal, sin escribir ni enviar archivos."""
    auditoria = []
    resultado = ejecutar_semana11({}, auditoria)
    if "interrupcion" in resultado:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    llamadas = [
        c["name"] for m in resultado["messages"] for c in getattr(m, "tool_calls", [])
    ]
    evidencia = evidencia_canonica(resultado["messages"][-1].content)
    print(json.dumps({
        "modelo": "MockLLM programado",
        "plan": resultado["todos"],
        "herramientas": llamadas,
        "artefacto_virtual": RUTA_HALLAZGOS,
        "evidencia": json.loads(verificar_archivo(resultado["files"], evidencia)),
        "auditoria": auditoria,
        "recursos": resultado["recursos"],
        "memoria_entre_procesos": False,
        "envio_externo": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
