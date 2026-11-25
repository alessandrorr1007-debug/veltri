"""Orquestador local LangGraph con seguridad previa y sin historial conversacional."""

from collections.abc import Callable, Hashable
from copy import deepcopy
from functools import partial
from time import monotonic
from typing import Any

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from pydantic import ValidationError

from src.agents.base import ErrorAgente
from src.agents.d1_ventas.a1_interpretacion import A1Interpretacion
from src.config import Configuracion, cargar_configuracion
from src.core.autonomia import (
    LIMITES_COMERCIALES,
    EjecucionInterrumpida,
    LimitesAutonomia,
    controlar_ejecucion,
    presupuesto_actual,
)
from src.core.decision import decide
from src.core.dlq import ColaBloqueos
from src.core.hitl import BandejaRevision
from src.core.llm import ErrorModelo
from src.core.observabilidad import observar, registrar_recursos, span
from src.core.seguridad import EntradaBloqueada, validar_entrada_modelo
from src.graph.nodes import Servicios, dominio, evaluar, recuperar, responder, validar_plan
from src.graph.state import EstadoFlujo
from src.knowledge.almacen import Almacen
from src.schemas.consulta import ConsultaResponse
from src.schemas.decision import SolicitudDecision
from src.schemas.flujo import ResultadoFlujo, SolicitudFlujo
from src.tools.catalogo import Catalogo
from src.tools.registro import RegistroPorTenant


def _contar_paso(nodo):
    def ejecutar(state: EstadoFlujo):
        presupuesto = presupuesto_actual.get()
        if presupuesto is not None:
            presupuesto.paso()
        return nodo(state)
    return ejecutar


def crear_grafo(servicios: Servicios):
    """Compila DAG acotado; sin checkpointer, caché ni modelo de texto libre en rutas."""
    constructor = StateGraph(EstadoFlujo)
    constructor.add_node("validar_plan", _contar_paso(validar_plan))
    constructor.add_node("decidir", _contar_paso(partial(evaluar, servicios=servicios)))
    constructor.add_node("responder", _contar_paso(responder))
    rutas: dict[Hashable, str] = {"decidir": "decidir", "informacion": "recuperar"}
    constructor.add_node("recuperar", _contar_paso(partial(recuperar, servicios=servicios)))
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
        constructor.add_node(nombre, _contar_paso(partial(dominio, servicios=servicios)))
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
        limites: LimitesAutonomia = LIMITES_COMERCIALES,
        reloj: Callable[[], float] = monotonic,
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
        self._limites = limites
        self._reloj = reloj
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

    @observar("consulta")
    def consultar(self, entrada: SolicitudFlujo | dict[str, Any]) -> ResultadoFlujo:
        """Seguridad y A1 fuera del estado; contexto de trazas desactivado incluso por entorno."""
        with controlar_ejecucion(self._limites, self._reloj) as presupuesto:
            salida = self._consultar(entrada)
            registrar_recursos("comercial", presupuesto.metricas(
                hitl=salida.respuesta.hitl_requerido, finalizacion=salida.respuesta.status,
            ))
            return salida

    def _interrumpir(self, tenant, estado, motivo):
        """Escala sin inferencia y proyecta solo resultados ya validados por el grafo."""
        revision = None
        if estado is not None and estado.revision_id is not None:
            revision = self.bandeja.obtener(tenant, estado.revision_id)
        if revision is None:
            solicitud = SolicitudDecision.model_validate({
                "opcion": "informar", "p": 0.0, "c": 0.0,
                "origen_puntuacion": "prueba_no_calibrada",
                "evidencia": {
                    "tipo": "limitacion", "motivos": [motivo], "fuentes": ["data/politicas.md"],
                },
            })
            revision = self.bandeja.encolar(tenant, solicitud).revision

        parcial = {"intencion": "desconocida", "fuentes": revision.decision.fuentes}
        extras = {}
        if estado is not None and estado.solicitud_decision is not None:
            decision = estado.decision or decide(estado.solicitud_decision)
            proyeccion = responder(estado.model_copy(update={"decision": decision}))["salida"]
            parcial = proyeccion.respuesta.model_dump()
            extras = proyeccion.model_dump(exclude={"respuesta", "decision", "revision_id"})
        respuesta = ConsultaResponse.model_validate({
            **parcial,
            "status": "revision_humana",
            "hitl_requerido": True,
            "mensaje": "Ejecución interrumpida; se requiere revisión humana.",
            "motivos": sorted({motivo, *parcial.get("motivos", []), *revision.decision.motivos}),
            "fuentes": sorted(set(parcial["fuentes"]) | set(revision.decision.fuentes)),
        })
        return ResultadoFlujo(
            respuesta=respuesta, decision=revision.decision, revision_id=revision.id, **extras,
        )

    def _consultar(self, entrada: SolicitudFlujo | dict[str, Any]) -> ResultadoFlujo:
        try:
            entrada = SolicitudFlujo.model_validate(
                entrada.model_dump() if isinstance(entrada, SolicitudFlujo) else entrada
            )
        except (ValidationError, ValueError, TypeError):
            return self._error("entrada_invalida")
        try:
            with span("seguridad"):
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
        estado = None
        presupuesto = presupuesto_actual.get()
        try:
            with tracing_context(enabled=False):
                plan = self._servicios.agente(A1Interpretacion).run(entrada.consulta).plan
                estado = EstadoFlujo(tenant_id=entrada.consulta.tenant_id, plan=plan,
                                    parametros=entrada.parametros)
                for valores in self._grafo.stream(
                    estado, stream_mode="values",
                    config={"callbacks": [], "recursion_limit": self._limites.iteraciones + 1},
                ):
                    estado = EstadoFlujo.model_validate(valores)
                presupuesto.segundos_restantes()
                return ResultadoFlujo.model_validate(estado.salida.model_dump())
        except GraphRecursionError:
            motivo = presupuesto.registrar_parada("limite_iteraciones")
            return self._interrumpir(entrada.consulta.tenant_id, estado, motivo)
        except EjecucionInterrumpida as error:
            return self._interrumpir(entrada.consulta.tenant_id, estado, error.motivo)
        except (ErrorModelo, ErrorAgente, ValidationError, ValueError):
            return self._error("ejecucion_no_disponible")
        except Exception:
            # Se conserva un fallo controlado; no se propagan trazas del backend al usuario.
            return self._error("fallo_interno")
