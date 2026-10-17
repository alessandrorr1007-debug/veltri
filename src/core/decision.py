"""Decisión determinista sobre resultados tipados; no usa ni instancia modelos."""

import hashlib
import json

from src.core.criterios import clasificar
from src.schemas.decision import (
    EvidenciaCotizacion,
    EvidenciaInformacion,
    EvidenciaPago,
    EvidenciaPedido,
    EvidenciaStock,
    EvidenciaTecnica,
    ResultadoDecision,
    SolicitudDecision,
)


def decide(solicitud: SolicitudDecision) -> ResultadoDecision:
    """Revalida evidencia; un invariante roto fuerza revisión sin importar p."""
    solicitud = SolicitudDecision.model_validate(solicitud.model_dump())
    evidencia = solicitud.evidencia
    bloqueos = []
    fuentes = []
    if isinstance(evidencia, EvidenciaInformacion):
        fuentes.extend(evidencia.fuentes)
    elif isinstance(evidencia, EvidenciaStock):
        fuentes.append(evidencia.resultado.fuente)
        bloqueos.extend("stock_insuficiente:" + f.sku for f in evidencia.resultado.faltantes)
    elif isinstance(evidencia, EvidenciaCotizacion):
        resultado = evidencia.resultado
        fuentes.extend(["data/catalogo.json", "data/compatibilidad.json"])
        bloqueos.extend(resultado.bloqueos)
        bloqueos.extend("stock_insuficiente:" + f.sku for f in resultado.stock.faltantes)
        bloqueos.extend(resultado.tecnico.pendientes)
        bloqueos.append("cotizacion_demo_sin_aprobacion")
    elif isinstance(evidencia, EvidenciaTecnica):
        fuentes.append(evidencia.resultado.fuente)
        bloqueos.extend(evidencia.resultado.conflictos + evidencia.resultado.pendientes)
        bloqueos.append("sin_aprobacion_tecnica_real")
    elif isinstance(evidencia, EvidenciaPago):
        fuentes.append("data/politicas.md")
        bloqueos.extend(evidencia.resultado.motivos)
        bloqueos.append("pago_no_conciliado")
    elif isinstance(evidencia, EvidenciaPedido):
        fuentes.extend(["data/catalogo.json", "data/politicas.md"])
        bloqueos.append("borrador_demo")
    else:
        raise ValueError("Evidencia no admitida")
    bloqueos = sorted(set(bloqueos))
    destino = clasificar(solicitud.p, bool(bloqueos))
    motivos = bloqueos or [{"ejecutar": "umbral_auto_sin_bloqueos",
                            "revision_humana": "puntaje_requiere_revision",
                            "escalar": "puntaje_bajo_escalar"}[destino]]
    canonica = json.dumps(solicitud.model_dump(mode="json"), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)
    return ResultadoDecision(opcion=solicitud.opcion, p=solicitud.p, c=solicitud.c,
                             origen_puntuacion=solicitud.origen_puntuacion, destino=destino,
                             hitl_requerido=destino != "ejecutar", bloqueos=bloqueos,
                             motivos=motivos, fuentes=sorted(set(fuentes)),
                             hash_evidencia=hashlib.sha256(canonica.encode()).hexdigest())
