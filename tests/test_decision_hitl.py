"""Compuerta y revisión local: límites, invariantes, aislamiento y transiciones."""

from concurrent.futures import ThreadPoolExecutor
from math import nextafter

import pytest
from pydantic import ValidationError

from src.core.decision import decide
from src.core.hitl import BandejaRevision
from src.core.umbrales import TAU_AUTO, TAU_REV
from src.schemas.decision import ResultadoDecision, SolicitudDecision
from src.schemas.hitl import ResolucionRevision
from src.tools.catalogo import Catalogo
from src.tools.cotizacion import cotizar
from src.tools.hardware import validar_configuracion
from src.tools.inventario import comprobar_stock
from src.tools.pagos import comparar_pago
from src.tools.pedidos import RegistroDemo


def informativa(p=1.0, c=1.0):
    return SolicitudDecision(opcion="informar", p=p, c=c, origen_puntuacion="prueba_no_calibrada",
                             evidencia={"tipo": "informacion", "fuentes": ["data/politicas.md"]})


@pytest.fixture
def catalogo():
    return Catalogo()


@pytest.fixture
def seleccion():
    return dict.fromkeys(["CPU-AMD-5600", "MB-A520-DDR4", "GPU-RX6600",
                          "RAM-DDR4-8-2666", "SSD-NVME-500-G3", "PSU-450",
                          "CASE-01", "COOL-02"], 1)


def solicitud(opcion, tipo, resultado, p=1.0):
    return SolicitudDecision(opcion=opcion, p=p, c=1.0, origen_puntuacion="prueba_no_calibrada",
                             evidencia={"tipo": tipo, "resultado": resultado})


def resolucion(accion):
    motivo = {"aprobar_demo": "informacion_verificada", "rechazar": "revision_rechazada",
              "solicitar_correccion": "requiere_correccion"}[accion]
    return ResolucionRevision(accion=accion, revisor="demo_operador", motivo=motivo)


@pytest.mark.parametrize("p,destino", [
    (0.0, "escalar"), (nextafter(TAU_REV, 0), "escalar"),
    (TAU_REV, "revision_humana"), (nextafter(TAU_AUTO, 0), "revision_humana"),
    (TAU_AUTO, "ejecutar"), (1.0, "ejecutar"),
])
def test_zonas_y_fronteras_de_umbrales_protegidos(p, destino):
    resultado = decide(informativa(p))
    assert resultado.destino == destino
    assert resultado.hitl_requerido is (destino != "ejecutar")
    assert not resultado.accion_ejecutada
    assert ResultadoDecision.model_validate_json(resultado.model_dump_json()) == resultado


@pytest.mark.parametrize("valor", [-0.1, 1.1, float("nan"), float("inf"), "0.99", True])
@pytest.mark.parametrize("campo", ["p", "c"])
def test_puntajes_invalidos_no_enrutan(campo, valor):
    datos = informativa().model_dump()
    datos[campo] = valor
    with pytest.raises(ValidationError):
        SolicitudDecision.model_validate(datos)


def test_confianza_no_inventa_otro_umbral():
    assert decide(informativa(TAU_AUTO, 0.0)).destino == "ejecutar"
    assert decide(informativa(0.0, 1.0)).destino == "escalar"


def test_evidencia_opcion_y_origen_obligatorios():
    datos = informativa().model_dump()
    datos["opcion"] = "comparar_pago"
    with pytest.raises(ValidationError):
        SolicitudDecision.model_validate(datos)
    datos = informativa().model_dump()
    datos["origen_puntuacion"] = "medicion_real"
    with pytest.raises(ValidationError):
        SolicitudDecision.model_validate(datos)
    datos = informativa().model_dump()
    datos["texto_llm"] = "aprobar todo"
    with pytest.raises(ValidationError):
        SolicitudDecision.model_validate(datos)


@pytest.mark.parametrize("p", [0.0, TAU_REV, TAU_AUTO, 1.0])
def test_stock_agotado_siempre_exige_revision(catalogo, p):
    datos = comprobar_stock(catalogo, {"CPU-AMD-5500": 1})
    resultado = decide(solicitud("consultar_stock", "stock", datos, p))
    assert resultado.destino == "revision_humana"
    assert "stock_insuficiente:CPU-AMD-5500" in resultado.bloqueos
    assert resultado.fuentes == ["data/catalogo.json"]


def test_stock_disponible_no_hereda_bloqueo(catalogo):
    resultado = decide(solicitud("consultar_stock", "stock",
                                 comprobar_stock(catalogo, {"CPU-AMD-5600": 1})))
    assert resultado.destino == "ejecutar" and not resultado.bloqueos


def test_socket_incompatible_con_probabilidad_alta(catalogo, seleccion):
    seleccion.pop("CPU-AMD-5600")
    seleccion["CPU-AMD-7600"] = 1
    tecnico = validar_configuracion(catalogo, seleccion)
    resultado = decide(solicitud("validar_compatibilidad", "tecnico", tecnico))
    assert resultado.destino == "revision_humana"
    assert "socket_incompatible" in resultado.bloqueos


def test_presupuesto_excedido_no_lo_autoriza_el_puntaje(catalogo, seleccion):
    datos = cotizar(catalogo, seleccion, 1)
    resultado = decide(solicitud("cotizar", "cotizacion", datos))
    assert resultado.p == 1.0 and resultado.destino == "revision_humana"
    assert "sobre_presupuesto" in resultado.bloqueos


def test_fichas_sinteticas_siguen_pendientes_sin_conflictos(catalogo, seleccion):
    datos = cotizar(catalogo, seleccion)
    assert not datos["bloqueos"]
    resultado = decide(solicitud("cotizar", "cotizacion", datos))
    assert "verificar_soporte_cpu_bios" in resultado.bloqueos
    assert "cotizacion_demo_sin_aprobacion" in resultado.bloqueos
    assert resultado.hitl_requerido


@pytest.mark.parametrize("pagado", [9999, 10000, 10001])
def test_pago_no_conciliado_aunque_coincida(catalogo, pagado):
    resultado = decide(solicitud("comparar_pago", "pago", comparar_pago(10000, pagado)))
    assert resultado.destino == "revision_humana"
    assert "pago_no_conciliado" in resultado.bloqueos


def test_borrador_no_se_convierte_en_pedido_confirmado(catalogo, seleccion):
    datos = RegistroDemo().registrar("demo_cliente", seleccion, "web", catalogo)
    resultado = decide(solicitud("registrar_borrador", "pedido", datos))
    assert resultado.bloqueos == ["borrador_demo"] and resultado.hitl_requerido


def test_revalida_modelos_que_fueron_mutados():
    evaluacion = informativa()
    evaluacion.evidencia.fuentes.clear()
    with pytest.raises(ValidationError):
        decide(evaluacion)


def test_resultado_rechaza_ocultar_bloqueo(catalogo):
    datos = comprobar_stock(catalogo, {"CPU-AMD-5500": 1})
    resultado = decide(solicitud("consultar_stock", "stock", datos)).model_dump()
    resultado["destino"] = "ejecutar"
    with pytest.raises(ValidationError):
        ResultadoDecision.model_validate(resultado)


def test_encolado_idempotente_copias_y_aislamiento():
    bandeja = BandejaRevision()
    evaluacion = informativa(TAU_REV)
    primero = bandeja.encolar("veltri", evaluacion)
    repetido = bandeja.encolar("veltri", evaluacion)
    otro = bandeja.encolar("otro", evaluacion)
    assert not primero.duplicado and repetido.duplicado
    assert primero.revision.id == repetido.revision.id != otro.revision.id
    assert len(bandeja.listar("veltri")) == len(bandeja.listar("otro")) == 1
    with pytest.raises(ValueError, match="no encontrada"):
        bandeja.obtener("otro", primero.revision.id)
    primero.revision.decision.motivos.clear()
    assert bandeja.obtener("veltri", primero.revision.id).decision.motivos
    with pytest.raises(ValueError):
        bandeja.encolar("veltri", informativa(1.0))


@pytest.mark.parametrize("tenant", [None, "", " ", "../otro", 7])
def test_tenant_explicito_en_bandeja(tenant):
    bandeja = BandejaRevision()
    with pytest.raises(ValidationError):
        bandeja.encolar(tenant, informativa(TAU_REV))
    with pytest.raises(ValidationError):
        bandeja.listar(tenant)
    with pytest.raises(ValidationError):
        bandeja.obtener(tenant, "a" * 64)
    with pytest.raises(ValidationError):
        bandeja.resolver(tenant, "a" * 64, resolucion("rechazar"))


@pytest.mark.parametrize("accion,estado", [
    ("aprobar_demo", "aprobada_demo"), ("rechazar", "rechazada"),
    ("solicitar_correccion", "correccion_solicitada"),
])
def test_transiciones_y_resolucion_idempotente(accion, estado):
    bandeja = BandejaRevision()
    revision = bandeja.encolar("veltri", informativa(TAU_REV)).revision
    final = bandeja.resolver("veltri", revision.id, resolucion(accion))
    assert final.estado == estado and not final.accion_ejecutada
    assert bandeja.resolver("veltri", revision.id, resolucion(accion)) == final
    otra = "rechazar" if accion != "rechazar" else "solicitar_correccion"
    with pytest.raises(ValueError, match="resolución final"):
        bandeja.resolver("veltri", revision.id, resolucion(otra))


def test_aprobacion_humana_no_borra_stock_agotado(catalogo):
    bandeja = BandejaRevision()
    evaluacion = solicitud("consultar_stock", "stock",
                           comprobar_stock(catalogo, {"CPU-AMD-5500": 1}))
    revision = bandeja.encolar("veltri", evaluacion).revision
    with pytest.raises(ValueError, match="corregir evidencia"):
        bandeja.resolver("veltri", revision.id, resolucion("aprobar_demo"))
    assert bandeja.obtener("veltri", revision.id).estado == "pendiente"
    corregida = solicitud("consultar_stock", "stock",
                          comprobar_stock(catalogo, {"CPU-AMD-5600": 1}), TAU_REV)
    nueva = bandeja.encolar("veltri", corregida).revision
    assert nueva.id != revision.id
    final = bandeja.resolver("veltri", nueva.id, resolucion("aprobar_demo"))
    assert final.estado == "aprobada_demo"


def test_escalado_requiere_nueva_evidencia_antes_de_aprobar():
    bandeja = BandejaRevision()
    revision = bandeja.encolar("veltri", informativa(0.0)).revision
    assert revision.estado == "escalada"
    with pytest.raises(ValueError):
        bandeja.resolver("veltri", revision.id, resolucion("aprobar_demo"))
    assert bandeja.resolver("veltri", revision.id, resolucion("solicitar_correccion"))


def test_revisor_y_motivos_no_admiten_pii():
    with pytest.raises(ValidationError):
        ResolucionRevision(accion="rechazar", revisor="persona@example.test",
                           motivo="revision_rechazada")
    with pytest.raises(ValidationError):
        ResolucionRevision(accion="rechazar", revisor="demo_operador", motivo="comentario libre")


def test_encolado_concurrente_crea_un_solo_registro():
    bandeja = BandejaRevision()
    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(lambda _: bandeja.encolar("veltri", informativa(TAU_REV)),
                                   range(12)))
    assert sum(not r.duplicado for r in resultados) == 1
    assert len(bandeja.listar("veltri")) == 1


def test_resolver_no_puede_actuar_sobre_otro_tenant():
    bandeja = BandejaRevision()
    revision = bandeja.encolar("veltri", informativa(TAU_REV)).revision
    with pytest.raises(ValueError, match="no encontrada"):
        bandeja.resolver("otro", revision.id, resolucion("rechazar"))
    assert bandeja.obtener("veltri", revision.id).estado == "pendiente"


def test_hash_de_evidencia_es_estable_y_cambia_si_cambia_evaluacion():
    primera = decide(informativa(TAU_REV))
    repetida = decide(informativa(TAU_REV))
    distinta = decide(informativa(1.0))
    assert primera.hash_evidencia == repetida.hash_evidencia != distinta.hash_evidencia


@pytest.mark.parametrize("tipo,opcion", [("pago", "comparar_pago"),
                                        ("cotizacion", "cotizar"),
                                        ("tecnico", "validar_compatibilidad"),
                                        ("pedido", "registrar_borrador")])
def test_aprobar_demo_no_autoriza_otras_operaciones(catalogo, seleccion, tipo, opcion):
    datos = {"pago": comparar_pago(10000, 10000), "cotizacion": cotizar(catalogo, seleccion),
             "tecnico": validar_configuracion(catalogo, seleccion),
             "pedido": RegistroDemo().registrar("demo_cliente", seleccion, "web", catalogo)}
    bandeja = BandejaRevision()
    revision = bandeja.encolar("veltri", solicitud(opcion, tipo, datos[tipo])).revision
    with pytest.raises(ValueError, match="corregir evidencia"):
        bandeja.resolver("veltri", revision.id, resolucion("aprobar_demo"))
    assert bandeja.obtener("veltri", revision.id).estado == "pendiente"


def test_revision_no_admite_decision_ajena_a_su_evidencia():
    from src.schemas.hitl import Revision

    bandeja = BandejaRevision()
    revision = bandeja.encolar("veltri", informativa(TAU_REV)).revision.model_dump()
    revision["solicitud"]["c"] = 0.0
    with pytest.raises(ValidationError, match="instantánea"):
        Revision.model_validate(revision)
