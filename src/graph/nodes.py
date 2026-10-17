"""Nodos sobre agentes existentes: resultados deterministas, decisión y presentación."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from src.agents.d1_ventas.a2_armado import A2Armado
from src.agents.d1_ventas.a3_cotizacion import A3Cotizacion
from src.agents.d2_tecnico.a4_compatibilidad import A4Compatibilidad
from src.agents.d3_inventario.a5_inventario import A5Inventario
from src.agents.d4_pedidos.a6_pagos import A6Pagos
from src.agents.d4_pedidos.a7_pedidos import A7Pedidos
from src.agents.d4_pedidos.a8_seguimiento import A8Seguimiento
from src.config import Configuracion
from src.core.criterios import clasificar
from src.core.decision import decide
from src.core.hitl import BandejaRevision
from src.graph.state import EstadoFlujo
from src.knowledge.almacen import Almacen
from src.schemas.agentes import (
    EntradaArmado,
    EntradaCotizacion,
    EntradaPago,
    EntradaPedido,
    EntradaSeguimiento,
    EntradaSeleccion,
)
from src.schemas.consulta import ConsultaResponse
from src.schemas.decision import SolicitudDecision
from src.schemas.flujo import CitaRecuperada, ResultadoFlujo
from src.tools.catalogo import Catalogo
from src.tools.registro import RegistroPorTenant


@dataclass
class Servicios:
    """Dependencias explícitas: no se escriben en el estado o trazas del grafo."""

    configuracion: Configuracion
    guiones: dict[str, list[dict[str, Any]]]
    catalogo: Catalogo
    registro: RegistroPorTenant
    bandeja: BandejaRevision
    almacen: Almacen | None

    def agente(self, clase):
        """Fixtures aislados por invocación; sin historial compartido del modelo."""
        return clase(
            configuracion=self.configuracion, respuestas=deepcopy(self.guiones.get(clase.id, []))
        )


def limitacion(estado: EstadoFlujo, motivo: str, fuentes=None) -> SolicitudDecision:
    """Un impedimento del flujo se convierte en evidencia que fuerza revisión."""
    return SolicitudDecision(
        opcion="informar",
        p=estado.plan.p,
        c=estado.plan.c,
        origen_puntuacion="prueba_no_calibrada",
        evidencia={
            "tipo": "limitacion",
            "motivos": [motivo],
            "fuentes": fuentes or ["data/politicas.md"],
        },
    )


def validar_plan(estado: EstadoFlujo) -> dict[str, Any]:
    """Deriva ruta solo de enums validados y verifica parámetros antes de efectos."""
    if clasificar(estado.plan.p, False) != "ejecutar":
        solicitud = SolicitudDecision(
            opcion="informar",
            p=estado.plan.p,
            c=estado.plan.c,
            origen_puntuacion="prueba_no_calibrada",
            evidencia={"tipo": "informacion", "fuentes": ["data/politicas.md"]},
        )
        return {"ruta": "decidir", "solicitud_decision": solicitud}
    if estado.plan.accion == "desconocida":
        motivo = "intencion_desconocida"
    elif estado.parametros is None:
        motivo = "parametros_requeridos"
    elif estado.parametros.tipo != estado.plan.accion:
        motivo = "parametros_no_corresponden"
    else:
        return {"ruta": estado.plan.accion}
    return {"ruta": "decidir", "solicitud_decision": limitacion(estado, motivo)}


def dominio(estado: EstadoFlujo, servicios: Servicios) -> dict[str, Any]:
    """Invoca un único dominio con parámetros del llamador, nunca del modelo."""
    params = estado.parametros
    tenant = estado.tenant_id
    comunes = {"tenant_id": tenant}
    accion = estado.ruta
    extras = {}
    if accion == "armar":
        salida = servicios.agente(A2Armado).run(
            EntradaArmado(**comunes, solicitud=params.solicitud), servicios.catalogo
        )
        extras["minimo_catalogo_centimos"] = salida.resultado.minimo_catalogo_centimos
        if salida.resultado.cotizacion is None:
            return {
                **extras,
                "solicitud_decision": limitacion(
                    estado,
                    "sin_configuracion_en_rango",
                    ["data/catalogo.json", "data/compatibilidad.json"],
                ),
            }
        payload = salida.resultado.cotizacion
        opcion, tipo, evidencia = "cotizar", "cotizacion", payload
    elif accion == "cotizar":
        salida = servicios.agente(A3Cotizacion).run(
            EntradaCotizacion(**comunes, solicitud=params.solicitud), servicios.catalogo
        )
        payload = salida.resultado
        opcion, tipo, evidencia = "cotizar", "cotizacion", payload
    elif accion == "compatibilidad":
        salida = servicios.agente(A4Compatibilidad).run(
            EntradaSeleccion(**comunes, seleccion=params.seleccion), servicios.catalogo
        )
        payload = salida.resultado
        opcion, tipo, evidencia = "validar_compatibilidad", "tecnico", payload
    elif accion == "stock":
        salida = servicios.agente(A5Inventario).run(
            EntradaSeleccion(**comunes, seleccion=params.seleccion), servicios.catalogo
        )
        payload = salida.resultado
        extras["alternativas"] = payload.alternativas
        opcion, tipo, evidencia = "consultar_stock", "stock", payload.stock
    elif accion == "pago":
        salida = servicios.agente(A6Pagos).run(EntradaPago(**comunes, solicitud=params.solicitud))
        payload = salida.resultado
        opcion, tipo, evidencia = "comparar_pago", "pago", payload
    elif accion == "pedido":
        salida = servicios.agente(A7Pedidos).run(
            EntradaPedido(
                **comunes, solicitud=params.solicitud, confirmar_borrador=params.confirmar_borrador
            ),
            servicios.catalogo,
            servicios.registro,
        )
        payload = salida.resultado
        opcion, tipo, evidencia = "registrar_borrador", "pedido", payload
    elif accion == "seguimiento":
        salida = servicios.agente(A8Seguimiento).run(
            EntradaSeguimiento(**comunes, clave=params.clave), servicios.registro
        )
        motivo = (
            "seguimiento_solo_demo" if salida.resultado.encontrado else "borrador_no_encontrado"
        )
        return {
            "seguimiento": salida.resultado,
            "solicitud_decision": limitacion(
                estado, motivo, ["data/catalogo.json", "data/politicas.md"]
            ),
        }
    else:
        raise ValueError("Ruta de dominio inválida")
    solicitud = SolicitudDecision(
        opcion=opcion,
        p=min(estado.plan.p, salida.plan.p),
        c=min(estado.plan.c, salida.plan.c),
        origen_puntuacion="prueba_no_calibrada",
        evidencia={"tipo": tipo, "resultado": evidencia.model_dump()},
    )
    return {**extras, "payload": payload, "solicitud_decision": solicitud}


def recuperar(estado: EstadoFlujo, servicios: Servicios) -> dict[str, Any]:
    """Temas enumerados a contexto citado; ningún fragmento se ejecuta o se envía al LLM."""
    if servicios.almacen is None:
        return {"solicitud_decision": limitacion(estado, "conocimiento_no_disponible")}
    tema = estado.parametros.tema
    consultas = {
        "politicas": ("políticas cotización", "data/politicas.md"),
        "pagos": ("pago discrepante revisión", "data/politicas.md"),
        "stock": ("stock revisión humana", "data/politicas.md"),
        "compatibilidad": ("socket ram refrigeracion", "data/compatibilidad.json"),
    }
    consulta, fuente = consultas[tema]
    resultados = servicios.almacen.buscar(estado.tenant_id, consulta, limite=3, fuente=fuente)
    if not resultados:
        return {"solicitud_decision": limitacion(estado, "conocimiento_no_disponible")}
    citas = [
        CitaRecuperada(**{k: r[k] for k in ("fuente", "referencia", "hash_fuente", "snapshot")})
        for r in resultados
    ]
    solicitud = SolicitudDecision(
        opcion="informar",
        p=estado.plan.p,
        c=estado.plan.c,
        origen_puntuacion="prueba_no_calibrada",
        evidencia={"tipo": "informacion", "fuentes": sorted({r["fuente"] for r in resultados})},
    )
    return {"citas": citas, "solicitud_decision": solicitud}


def evaluar(estado: EstadoFlujo, servicios: Servicios) -> dict[str, Any]:
    """Aplica invariantes y registra revisión o escalado sin aprobar negocio."""
    decision = decide(estado.solicitud_decision)
    revision_id = None
    if decision.hitl_requerido:
        revision_id = servicios.bandeja.encolar(
            estado.tenant_id, estado.solicitud_decision
        ).revision.id
    return {"decision": decision, "revision_id": revision_id}


def responder(estado: EstadoFlujo) -> dict[str, Any]:
    """Proyecta resultados a ConsultaResponse; no redacta hechos con el modelo."""
    decision = estado.decision
    payload = estado.payload
    motivos = set(decision.motivos) if decision.hitl_requerido else set()
    valores = {
        "status": "revision_humana" if decision.hitl_requerido else "completado",
        "intencion": "informacion",
        "hitl_requerido": decision.hitl_requerido,
        "motivos": sorted(motivos),
        "fuentes": decision.fuentes,
        "mensaje": "Resultado de demostración; consulta fuentes y evidencia antes de operar.",
    }
    if payload is not None:
        campo, intencion = {
            "armar": ("cotizacion", "cotizacion"),
            "cotizar": ("cotizacion", "cotizacion"),
            "compatibilidad": ("tecnico", "compatibilidad"),
            "stock": ("stock", "stock"),
            "pago": ("pago", "pago"),
            "pedido": ("pedido", "pedido"),
        }[estado.ruta]
        if estado.ruta == "stock":
            payload = payload.stock
            if not payload.disponible:
                motivos.add("stock_insuficiente")
        valores.update({"intencion": intencion, campo: payload, "motivos": sorted(motivos)})
    elif not estado.citas:
        valores["intencion"] = "desconocida"
        valores["mensaje"] = "Se requiere aclaración o revisión; no se generó una proforma."
    respuesta = ConsultaResponse.model_validate(valores)
    salida = ResultadoFlujo(
        respuesta=respuesta,
        decision=decision,
        revision_id=estado.revision_id,
        alternativas=estado.alternativas,
        minimo_catalogo_centimos=estado.minimo_catalogo_centimos,
        seguimiento=estado.seguimiento,
        citas=estado.citas,
    )
    return {"respuesta": respuesta, "salida": salida}
