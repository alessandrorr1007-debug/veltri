"""Spans mínimos para una demo sintética de confianza; sin capturar argumentos."""

import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Iterator
from uuid import UUID, uuid4

from langsmith import Client, tracing_context

from src.config import ConfiguracionObservabilidad
from src.core.diagnostico_http import TransporteDiagnostico

NOMBRES = frozenset(
    {"consulta", "seguridad", "validar_plan", "dominio", "recuperar", "decidir", "responder"}
    | {f"A{i}.plan_mock" for i in range(1, 9)}
    | {"herramienta", "comprobar_stock", "armar", "cotizar", "validar_configuracion",
       "comparar_pago", "registrar", "consultar"}
)


@dataclass(frozen=True)
class Sesion:
    """Solo transporte y correlación; sin solicitudes ni estado comercial."""

    cliente: Any
    proyecto: str


_sesion: ContextVar[Sesion | None] = ContextVar("veltri_observacion", default=None)
_padre: ContextVar[tuple[UUID, str, UUID] | None] = ContextVar("veltri_span", default=None)


def _cliente_externo(config: ConfiguracionObservabilidad):
    """No se llama sin los dos opt-in; no autodetecta destino o claves del entorno."""
    if any(k.startswith(("LANGSMITH_RUNS_", "LANGSMITH_AGENT_", "LANGSMITH_OTEL_",
                         "LANGCHAIN_RUNS_", "LANGCHAIN_AGENT_"))
           and v for k, v in os.environ.items()):
        raise ValueError("Configuracion SDK adicional no admitida para la demo")
    return Client(
        api_url=config.endpoint,
        api_key=config.clave.get_secret_value(),
        auto_batch_tracing=False,
        hide_inputs=True,
        hide_outputs=True,
        hide_metadata=lambda _: {"synthetic": True, "model_mode": "mock", "scenario": "stock_demo"},
        omit_traced_runtime_info=True,
        timeout_ms=2000,
        tracing_mode="langsmith",
        otel_enabled=False,
        tracing_sampling_rate=1.0,
        session=TransporteDiagnostico(),
    )


@contextmanager
def sesion_sintetica(
    config: ConfiguracionObservabilidad, *, cliente_local=None, usar_mock: bool = True,
    diagnostico_http: list | None = None,
) -> Iterator[None]:
    """Solo llamadores de confianza con fixtures; no exponer como parámetro de API.

    cliente_local es un capturador offline. El envío exige autorización adicional,
    flag externo y destino válido. No clasifica ni anonimiza entradas arbitrarias.
    """
    cliente = None
    if config.habilitada and usar_mock and config.proyecto == "veltri-semana10-demo":
        cliente = cliente_local
        if cliente is None and config.permitir_envio_externo:
            if (
                config.endpoint in {"https://api.smith.langchain.com", "https://eu.api.smith.langchain.com"}
                and config.proyecto == "veltri-semana10-demo"
                and config.clave.get_secret_value()
            ):
                try:
                    cliente = _cliente_externo(config)
                except Exception:
                    cliente = None
    token = _sesion.set(Sesion(cliente, config.proyecto) if cliente is not None else None)
    padre_token = _padre.set(None)
    try:
        with tracing_context(enabled=False):
            yield
    finally:
        _padre.reset(padre_token)
        _sesion.reset(token)
        if cliente is not None and diagnostico_http is not None:
            transporte = getattr(cliente, "session", None)
            if isinstance(transporte, TransporteDiagnostico):
                diagnostico_http.extend(dict(r) for r in transporte.registros)


@contextmanager
def span(nombre: str) -> Iterator[None]:
    """Nombres cerrados, cuerpos vacíos y errores fijos; nunca reintenta negocio."""
    sesion = _sesion.get()
    if sesion is None or nombre not in NOMBRES:
        yield
        return
    padre = _padre.get()
    run_id = uuid4()
    raiz = padre[2] if padre else run_id
    inicio = datetime.now(timezone.utc)
    orden = inicio.strftime("%Y%m%dT%H%M%S%fZ") + str(run_id)
    if padre:
        orden = padre[1] + "." + orden
    try:
        sesion.cliente.create_run(
            id=run_id, name=nombre, run_type="chain", inputs={},
            project_name=sesion.proyecto, start_time=inicio,
            trace_id=raiz, parent_run_id=padre[0] if padre else None,
            dotted_order=orden,
            extra={"metadata": {"synthetic": True, "model_mode": "mock", "scenario": "stock_demo"}},
        )
    except Exception:
        # Si no se pudo registrar el padre, tampoco generar hijos huérfanos.
        token = _sesion.set(None)
        try:
            yield
        finally:
            _sesion.reset(token)
        return
    token = _padre.set((run_id, orden, raiz))
    fallo = False
    try:
        yield
    except BaseException:
        fallo = True
        raise
    finally:
        _padre.reset(token)
        try:
            sesion.cliente.update_run(
                run_id, end_time=datetime.now(timezone.utc), outputs={},
                error="operation_failed" if fallo else None,
                trace_id=raiz, dotted_order=orden,
                # El SDK 0.14.11 serializa None si no recibe este contexto.
                name=nombre, run_type="chain", start_time=inicio,
                parent_run_id=padre[0] if padre else None,
                session_name=sesion.proyecto, tags=[],
                extra={"metadata": {
                    "synthetic": True, "model_mode": "mock", "scenario": "stock_demo",
                }},
            )
        except Exception:
            pass


def observar(nombre: str):
    """Decorador sin introspección ni serialización de args, kwargs o resultados."""
    def decorar(funcion):
        @wraps(funcion)
        def ejecutar(*args, **kwargs):
            with tracing_context(enabled=False), span(nombre):
                return funcion(*args, **kwargs)
        return ejecutar
    return decorar
