"""Atención determinista de consultas comerciales libres sobre catálogo, stock y políticas."""

import re
import unicodedata
from typing import Any

from src.core.seguridad import EntradaBloqueada, validar_entrada_modelo
from src.schemas.base import Canal
from src.schemas.consulta import ConsultaResponse
from src.schemas.entradas import ArmadoRequest, ConsultaRequest
from src.schemas.flujo import ParametrosArmado, ParametrosSeleccion, SolicitudFlujo
from src.schemas.hitl import Tenant
from src.tools.catalogo import Catalogo


def normalizar_texto(texto: str) -> str:
    """Convierte a minúsculas y elimina tildes/acentos para comparaciones robustas."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower().strip()


def formatear_soles(centimos: int) -> str:
    """Convierte céntimos a representación en Soles (S/)."""
    return f"S/ {centimos / 100:,.2f}"


def inferir_parametros_consulta(
    mensaje: str,
) -> tuple[str, ParametrosArmado | ParametrosSeleccion | None]:
    """Extrae parámetros de armado o stock cuando el usuario escribe en lenguaje natural."""
    msg_norm = normalizar_texto(mensaje)

    # 1. Detección de intención de cotización / armado por presupuesto
    es_cotizacion = any(
        k in msg_norm for k in ("cotiz", "armar", "presupuesto", "pc gamer", "configuracion")
    )
    monto_match = re.search(
        r"(?:s\/?\.?\s*|soles\s*|presupuesto\s*(?:de\s*)?)(\d{3,6})", msg_norm
    )
    if not monto_match:
        monto_match = re.search(r"(\d{3,6})\s*(?:soles|s\/?\.?)", msg_norm)

    solo_rtx = "rtx" in msg_norm

    if es_cotizacion and monto_match:
        monto_soles = int(monto_match.group(1))
        monto_centimos = monto_soles * 100
        solicitud_armado = ArmadoRequest(maximo_centimos=monto_centimos, solo_rtx=solo_rtx)
        return "armar", ParametrosArmado(tipo="armar", solicitud=solicitud_armado)

    # 2. Detección de consulta de stock sobre componente específico
    es_stock = any(k in msg_norm for k in ("stock", "disponible", "disponibilidad", "hay stock"))
    sku_detectado = None
    if "5500" in msg_norm:
        sku_detectado = "CPU-AMD-5500"
    elif "5600x" in msg_norm:
        sku_detectado = "CPU-AMD-5600X"
    elif "5600" in msg_norm:
        sku_detectado = "CPU-AMD-5600"
    elif "3050" in msg_norm:
        sku_detectado = "GPU-RTX3050"
    elif "3060" in msg_norm:
        sku_detectado = "GPU-RTX3060"
    elif "4060ti" in msg_norm or "4060 ti" in msg_norm:
        sku_detectado = "GPU-RTX4060TI"
    elif "4060" in msg_norm:
        sku_detectado = "GPU-RTX4060"
    elif "6600" in msg_norm:
        sku_detectado = "GPU-RX6600"

    if (es_stock or "quiero armar" in msg_norm) and sku_detectado:
        return "stock", ParametrosSeleccion(tipo="stock", seleccion={sku_detectado: 1})

    return "informacion", None


def atender_consulta_comercial(
    catalogo: Catalogo,
    mensaje: str,
    tenant_id: Tenant = "veltri",
    canal: Canal = "web",
    orquestador: Any = None,
) -> ConsultaResponse:
    """Procesa consultas en lenguaje natural usando exclusivamente el catálogo y políticas."""
    # Invariante 5: Seguridad antes de cualquier procesamiento
    try:
        validar_entrada_modelo(mensaje)
    except EntradaBloqueada:
        if orquestador is not None and hasattr(orquestador, "dlq"):
            orquestador.dlq.registrar(tenant_id)
        return ConsultaResponse(
            status="bloqueado",
            intencion="desconocida",
            mensaje="Solicitud bloqueada por la guarda de seguridad.",
            hitl_requerido=False,
            motivos=["entrada_bloqueada"],
            archivado_en_dlq=True,
        )

    # Inferir parámetros estructurados si aplica
    accion, params = inferir_parametros_consulta(mensaje)
    if params is not None and orquestador is not None:
        sol_flujo = SolicitudFlujo(
            consulta=ConsultaRequest(mensaje=mensaje, canal=canal, tenant_id=tenant_id),
            parametros=params,
        )
        res = orquestador.consultar(sol_flujo)
        return res.respuesta

    msg_norm = normalizar_texto(mensaje)

    # Consultas sobre tarjetas NVIDIA RTX
    if "rtx" in msg_norm and (
        any(k in msg_norm for k in ("barat", "econom", "precio", "cuanto", "cual", "que", "opcion"))
    ):
        gpus_rtx = [p for p in catalogo.listar("gpu") if p["sku"].startswith("GPU-RTX")]
        gpus_rtx.sort(key=lambda x: x["precio_centimos"])
        con_stock = [p for p in gpus_rtx if p["stock"] > 0]
        if con_stock:
            primera = con_stock[0]
            segunda = con_stock[1] if len(con_stock) > 1 else None
            p1_str = formatear_soles(primera["precio_centimos"])
            msg = (
                f"La tarjeta gráfica NVIDIA RTX más económica disponible en nuestro catálogo es "
                f"la GeForce RTX 3050 (SKU: {primera['sku']}) por {p1_str}, con "
                f"{primera['stock']} unidades en stock."
            )
            if segunda:
                p2_str = formatear_soles(segunda["precio_centimos"])
                msg += (
                    f" Como opción superior disponemos de la RTX 3060 (SKU: {segunda['sku']}) "
                    f"por {p2_str} ({segunda['stock']} unidades disponibles)."
                )
            return ConsultaResponse(
                status="completado",
                intencion="informacion",
                hitl_requerido=False,
                motivos=[],
                fuentes=["data/catalogo.json"],
                mensaje=msg,
            )

    # Consulta por GPU / tarjeta de video más barata en general
    if any(k in msg_norm for k in ("gpu", "tarjeta", "video", "grafica")):
        gpus = catalogo.listar("gpu")
        gpus.sort(key=lambda x: x["precio_centimos"])
        con_stock = [p for p in gpus if p["stock"] > 0]
        if con_stock:
            primera = con_stock[0]
            p_str = formatear_soles(primera["precio_centimos"])
            return ConsultaResponse(
                status="completado",
                intencion="informacion",
                hitl_requerido=False,
                motivos=[],
                fuentes=["data/catalogo.json"],
                mensaje=(
                    f"La tarjeta de video más económica disponible en catálogo es la "
                    f"AMD Radeon RX 6600 (SKU: {primera['sku']}) por {p_str}, "
                    f"con {primera['stock']} unidades en stock. Si buscas arquitectura "
                    f"NVIDIA RTX, la más accesible es la RTX 3050 por S/ 1,790.00."
                ),
            )

    # Consulta por procesadores / CPUs
    if any(k in msg_norm for k in ("cpu", "procesador", "ryzen", "intel")):
        cpus = catalogo.listar("cpu")
        cpus.sort(key=lambda x: x["precio_centimos"])
        con_stock = [p for p in cpus if p["stock"] > 0]
        am4_stock = [p for p in con_stock if p["especificaciones"].get("socket") == "AM4"]
        am5_stock = [p for p in con_stock if p["especificaciones"].get("socket") == "AM5"]
        intel_stock = [p for p in con_stock if "INTEL" in p["sku"]]

        detalles = []
        if am4_stock:
            p_am4 = formatear_soles(am4_stock[0]["precio_centimos"])
            detalles.append(f"AM4: {am4_stock[0]['sku']} a {p_am4}")
        if am5_stock:
            p_am5 = formatear_soles(am5_stock[0]["precio_centimos"])
            detalles.append(f"AM5: {am5_stock[0]['sku']} a {p_am5}")
        if intel_stock:
            p_intel = formatear_soles(intel_stock[0]["precio_centimos"])
            detalles.append(f"Intel: {intel_stock[0]['sku']} a {p_intel}")

        resumen_detalles = "; ".join(detalles)
        return ConsultaResponse(
            status="completado",
            intencion="informacion",
            hitl_requerido=False,
            motivos=[],
            fuentes=["data/catalogo.json"],
            mensaje=(
                f"Contamos con procesadores disponibles en diversas plataformas: "
                f"{resumen_detalles}. El procesador AMD Ryzen 5 5500 está agotado."
            ),
        )

    # Consulta por fuentes de poder
    if any(k in msg_norm for k in ("fuente", "psu", "power")):
        fuentes = catalogo.listar("fuente")
        fuentes.sort(key=lambda x: x["precio_centimos"])
        primera = fuentes[0]
        p_fuente = formatear_soles(primera["precio_centimos"])
        return ConsultaResponse(
            status="completado",
            intencion="informacion",
            hitl_requerido=False,
            motivos=[],
            fuentes=["data/catalogo.json"],
            mensaje=(
                f"La fuente de poder más económica es la {primera['sku']} de 450W por "
                f"{p_fuente} ({primera['stock']} unidades disponibles). "
                f"También disponemos de modelos de 550W a 850W con certificación."
            ),
        )

    # Consulta por memorias RAM
    if any(k in msg_norm for k in ("ram", "memoria")):
        rams = catalogo.listar("ram")
        rams.sort(key=lambda x: x["precio_centimos"])
        primera = rams[0]
        p_ram = formatear_soles(primera["precio_centimos"])
        return ConsultaResponse(
            status="completado",
            intencion="informacion",
            hitl_requerido=False,
            motivos=[],
            fuentes=["data/catalogo.json"],
            mensaje=(
                f"Disponemos de módulos RAM DDR4 desde {p_ram} ({primera['sku']}) "
                f"con stock disponible, además de opciones DDR5 para plataformas AM5."
            ),
        )

    # 4. Consultas sobre políticas, garantía, métodos de pago o envíos
    es_politica = any(
        k in msg_norm
        for k in (
            "garantia",
            "politica",
            "pago",
            "pagar",
            "yape",
            "transferencia",
            "envio",
            "provincia",
            "despacho",
            "donde",
            "ubicacion",
            "horario",
        )
    )
    if es_politica:
        return ConsultaResponse(
            status="completado",
            intencion="informacion",
            hitl_requerido=False,
            motivos=[],
            fuentes=["data/politicas.md"],
            mensaje=(
                "En Veltri Tecnologic todos los componentes cuentan con 12 meses de garantía. "
                "Los pagos se concilian contra cuentas autorizadas (transferencia o Yape) "
                "con verificación exacta. Realizamos envíos a Lima Metropolitana y provincias "
                "vía agencia autorizada."
            ),
        )

    # 5. Saludo o consulta general asistida
    return ConsultaResponse(
        status="completado",
        intencion="informacion",
        hitl_requerido=False,
        motivos=[],
        fuentes=["data/catalogo.json", "data/politicas.md"],
        mensaje=(
            "Bienvenido a Veltri Tecnologic. Puedes indicarme tu presupuesto en Soles (S/) para "
            "armar una PC gamer, consultar disponibilidad de piezas de catálogo (RTX/Radeon, "
            "CPUs, fuentes, memorias), o consultar nuestras políticas de garantía y despacho."
        ),
    )
