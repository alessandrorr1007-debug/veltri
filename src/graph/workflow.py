"""Orquestador local LangGraph con seguridad previa y sin historial conversacional."""

from copy import deepcopy
from functools import partial
from typing import Any

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from pydantic import ValidationError

from src.agents.base import ErrorAgente
from src.agents.d1_ventas.a1_interpretacion import A1Interpretacion
from src.config import Configuracion, cargar_configuracion
from src.core.dlq import ColaBloqueos
from src.core.hitl import BandejaRevision
from src.core.llm import ErrorModelo
from src.core.seguridad import EntradaBloqueada, validar_entrada_modelo
from src.graph.nodes import Servicios, dominio, evaluar, recuperar, responder, validar_plan
from src.graph.state import EstadoFlujo
from src.knowledge.almacen import Almacen
from src.schemas.consulta import ConsultaResponse
from src.schemas.flujo import ResultadoFlujo, SolicitudFlujo
from src.tools.catalogo import Catalogo
from src.tools.registro import RegistroPorTenant


def crear_grafo(servicios: Servicios):
    """Compila DAG acotado; sin checkpointer, caché ni modelo de texto libre en rutas."""
    constructor = StateGraph(EstadoFlujo)
    constructor.add_node("validar_plan", validar_plan)
    constructor.add_node("decidir", partial(evaluar, servicios=servicios))
    constructor.add_node("responder", responder)
    rutas = {"decidir": "decidir", "informacion": "recuperar"}
    constructor.add_node("recuperar", partial(recuperar, servicios=servicios))
    constructor.add_edge("recuperar", "decidir")
    for accion, nombre in [
        ("armar", "a2_armado"),
        ("cotizar", "a3_cotizacion"),
        ("compatibilidad", "a4_compatibilidad"),
        ("stock", "a5_inventario"),
        ("pago", "a6_pagos"),
        ("pedido", "a7_pedidos"),
        ("seguimiento", "a8_seguimiento"),
    ]:
        constructor.add_node(nombre, partial(dominio, servicios=servicios))
        constructor.add_edge(nombre, "decidir")
        rutas[accion] = nombre
    constructor.add_edge(START, "validar_plan")
    constructor.add_conditional_edges("validar_plan", lambda estado: estado.ruta, rutas)
    constructor.add_edge("decidir", "responder")
    constructor.add_edge("responder", END)
    return constructor.compile()


class Orquestador:
    """Fachada sin API: valida antes del grafo y devuelve contratos, nunca excepciones crudas."""

    def __init__(
        self,
        *,
        guiones: dict[str, list[dict[str, Any]]],
        configuracion: Configuracion | None = None,
        catalogo: Catalogo | None = None,
        registro: RegistroPorTenant | None = None,
        bandeja: BandejaRevision | None = None,
        dlq: ColaBloqueos | None = None,
        almacen: Almacen | None = None,
    ) -> None:
        self._servicios = Servicios(
            configuracion or cargar_configuracion(),
            deepcopy(guiones),
            catalogo or Catalogo(),
            registro or RegistroPorTenant(),
            bandeja or BandejaRevision(),
            almacen,
        )
        self.dlq = dlq if dlq is not None else ColaBloqueos()
        self.bandeja = self._servicios.bandeja
        self._grafo = crear_grafo(self._servicios)

    def _error(self, codigo: str) -> ResultadoFlujo:
        return ResultadoFlujo(
            respuesta=ConsultaResponse(
                status="error",
                intencion="desconocida",
                mensaje="No se pudo procesar la solicitud; revisa los parámetros o solicita ayuda.",
                hitl_requerido=False,
                motivos=[codigo],
            )
        )

    def consultar(self, entrada: SolicitudFlujo | dict[str, Any]) -> ResultadoFlujo:
        """Seguridad y A1 fuera del estado; contexto de trazas desactivado incluso por entorno."""
        try:
            entrada = SolicitudFlujo.model_validate(
                entrada.model_dump() if isinstance(entrada, SolicitudFlujo) else entrada
            )
        except (ValidationError, ValueError, TypeError):
            return self._error("entrada_invalida")
        try:
            validar_entrada_modelo(entrada.consulta.mensaje)
        except EntradaBloqueada:
            evento = self.dlq.registrar(entrada.consulta.tenant_id)
            return ResultadoFlujo(
                evento_dlq_id=evento.id,
                respuesta=ConsultaResponse(
                    status="bloqueado",
                    intencion="desconocida",
                    mensaje="Solicitud bloqueada por la guarda de seguridad.",
                    hitl_requerido=False,
                    motivos=["entrada_bloqueada"],
                    archivado_en_dlq=True,
                ),
            )
        if not self._servicios.configuracion.usar_mock:
            return self._error("modo_real_pendiente_de_calibracion")
        try:
            with tracing_context(enabled=False):
                plan = self._servicios.agente(A1Interpretacion).run(entrada.consulta).plan
                resultado = self._grafo.invoke(
                    {
                        "tenant_id": entrada.consulta.tenant_id,
                        "plan": plan,
                        "parametros": entrada.parametros,
                    },
                    config={"callbacks": [], "recursion_limit": 12},
                )
                salida = resultado["salida"]
                return ResultadoFlujo.model_validate(salida.model_dump())
        except (ErrorModelo, ErrorAgente, ValidationError, ValueError):
            return self._error("ejecucion_no_disponible")
        except Exception:
            # Se conserva un fallo controlado; no se propagan trazas del backend al usuario.
            return self._error("fallo_interno")
