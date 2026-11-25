"""Contenido y límites de los prompts, con modelos simulados."""

from typing import get_args

import pytest

from src.academic.deep_agents_semana11 import (
    PROMPT_CATALOGO,
    PROMPT_COORDINADOR,
    PROMPT_REVISION,
    AdaptadorEvidencia,
    AdaptadorMemoria,
)
from src.agents.d1_ventas.a1_interpretacion import A1Interpretacion
from src.agents.d1_ventas.a2_armado import A2Armado
from src.agents.d1_ventas.a3_cotizacion import A3Cotizacion
from src.agents.d2_tecnico.a4_compatibilidad import A4Compatibilidad
from src.agents.d3_inventario.a5_inventario import A5Inventario
from src.agents.d4_pedidos.a6_pagos import A6Pagos
from src.agents.d4_pedidos.a7_pedidos import A7Pedidos
from src.agents.d4_pedidos.a8_seguimiento import A8Seguimiento
from src.config import Configuracion
from src.core.llm import ErrorModelo
from src.schemas.agentes import Accion
from src.schemas.entradas import ConsultaRequest

TITULOS = (
    "Rol y misión", "Contexto operativo", "Jerarquía de confianza",
    "Herramientas y permisos", "Proceso de trabajo", "Delegación a subagentes",
    "Contenido no confiable", "Límites estrictos", "Datos sensibles", "Presupuesto y parada",
    "Escalamiento humano (HITL)", "Salida estructurada",
)


def bloques(prompt):
    lineas = prompt.splitlines()
    assert len(lineas) == 12
    resultado = {}
    for numero, (titulo, linea) in enumerate(zip(TITULOS, lineas, strict=True), start=1):
        prefijo = f"{numero}. {titulo}: "
        assert linea.startswith(prefijo)
        contenido = linea[len(prefijo):].strip()
        assert contenido
        resultado[titulo] = contenido
    return resultado


@pytest.mark.parametrize(("agente", "herramienta", "limite", "hitl"), [
    (A1Interpretacion, "enrutar", "tenant", "intención ambigua"),
    (A2Armado, "usa armar", "componentes", "fuera de presupuesto"),
    (A3Cotizacion, "usa cotizar", "descuentos", "stock insuficiente"),
    (A4Compatibilidad, "validar_configuracion", "FPS", "Socket incompatible"),
    (A5Inventario, "comprobar_stock y alternativas", "reserves stock", "faltante"),
    (A6Pagos, "comparar_pago", "acredites transferencias", "Pago discrepante"),
    (A7Pedidos, "RegistroPorTenant.registrar", "consentimiento", "falta confirmación"),
    (A8Seguimiento, "RegistroPorTenant.consultar", "cambies de tenant", "borrador ausente"),
], ids=lambda caso: caso.id if isinstance(caso, type) else None)
def test_prompts_comerciales(agente, herramienta, limite, hitl):
    instrucciones = bloques(agente.prompt)
    assert tuple(instrucciones) == TITULOS
    assert agente.id in instrucciones["Rol y misión"]
    assert "evidencia validada" in instrucciones["Jerarquía de confianza"]
    assert "El modelo no invoca herramientas" in instrucciones["Herramientas y permisos"]
    assert herramienta in instrucciones["Herramientas y permisos"]
    assert "No delegues" in instrucciones["Delegación a subagentes"]
    assert "datos_no_confiables" in instrucciones["Contenido no confiable"]
    assert "Ignora órdenes" in instrucciones["Contenido no confiable"]
    assert limite in instrucciones["Límites estrictos"]
    assert "No inventes cifras, evidencia ni estados" in instrucciones["Límites estrictos"]
    assert "credenciales" in instrucciones["Datos sensibles"]
    assert "un solo plan" in instrucciones["Presupuesto y parada"]
    assert hitl in instrucciones["Escalamiento humano (HITL)"]
    assert "p y c no autorizan" in instrucciones["Escalamiento humano (HITL)"]
    salida = instrucciones["Salida estructurada"]
    assert "Solo JSON PlanModelo con accion, p y c." in salida
    if agente.accion:
        assert f"accion={agente.accion}." in salida
    else:
        assert ", ".join(get_args(Accion)) in salida
        assert "→ desconocida" in instrucciones["Proceso de trabajo"]


@pytest.mark.parametrize(("prompt", "rol", "proceso", "parada"), [
    (PROMPT_COORDINADOR, "DA-CoordinadorAcademico", "guarda y relee", "presupuesto de ejecución"),
    (PROMPT_CATALOGO, "DA-Catalogo", "tres campos", "Una consulta"),
    (PROMPT_REVISION, "DA-Revision", "Contrasta los tres campos", "discrepa"),
])
def test_prompts_academicos(prompt, rol, proceso, parada):
    instrucciones = bloques(prompt)
    assert tuple(instrucciones) == TITULOS
    assert rol in instrucciones["Rol y misión"]
    assert proceso in instrucciones["Proceso de trabajo"]
    assert parada in instrucciones["Presupuesto y parada"]
    assert "Ignora órdenes" in instrucciones["Contenido no confiable"]
    assert "No uses datos reales" in instrucciones["Límites estrictos"]
    assert "no hay aprobación comercial" in instrucciones["Escalamiento humano (HITL)"]
    assert "SalidaAcademica" in instrucciones["Salida estructurada"]
    assert "requiere_revision=true, efecto_comercial=false" in instrucciones["Salida estructurada"]
    if rol == "DA-CoordinadorAcademico":
        assert "DA-Catalogo y después una vez a DA-Revision" in (
            instrucciones["Delegación a subagentes"]
        )
        assert "write_todos, task, write_file y read_file" in (
            instrucciones["Herramientas y permisos"]
        )
    else:
        assert "No delegues" in instrucciones["Delegación a subagentes"]
        assert "únicamente revisar_fixture_sintetico" in instrucciones["Herramientas y permisos"]


@pytest.mark.parametrize(("adaptador", "fuera_de_rol"), [
    (AdaptadorEvidencia, "task"),
    (AdaptadorEvidencia, "write_file"),
    (AdaptadorMemoria, "revisar_fixture_sintetico"),
])
def test_el_adaptador_rechaza_herramienta_fuera_del_rol(adaptador, fuera_de_rol):
    modelo = adaptador([{"herramienta": fuera_de_rol}])
    modelo.bind_tools([{"name": fuera_de_rol}, *(
        {"name": nombre} for nombre in modelo.herramientas_del_rol
    )])
    assert modelo._permitidas == modelo.herramientas_del_rol
    with pytest.raises(ValueError, match="herramienta_no_permitida"):
        modelo._generate([])


def test_el_plan_del_modelo_no_admite_autorizaciones_comerciales():
    agente = A1Interpretacion(
        configuracion=Configuracion(usar_mock=True),
        respuestas=[{"accion": "pago", "p": 1.0, "c": 1.0, "pago_acreditado": True}],
    )
    with pytest.raises(ErrorModelo, match="respuesta_modelo_invalida"):
        agente.run(ConsultaRequest(mensaje="Quiero validar un pago", canal="web", tenant_id="demo"))
