"""Validación local de artefactos sintéticos para la demo de semana 11."""

import json
from collections.abc import Mapping

RUTA_HALLAZGOS = "/hallazgos.json"
CAMPOS = {"sintetico", "requiere_revision", "efecto_comercial"}


def texto_mensaje(contenido: object) -> str:
    """Acepta texto de herramientas o bloques de texto, no otros tipos de contenido."""
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list) and contenido and all(
        isinstance(bloque, dict)
        and bloque.get("type") == "text"
        and isinstance(bloque.get("text"), str)
        for bloque in contenido
    ):
        return "\n".join(bloque["text"] for bloque in contenido)
    raise ValueError("contenido_academico_invalido")


def evidencia_canonica(contenido: object) -> str:
    """Valida el contrato cerrado; impide guardar datos o efectos comerciales."""
    try:
        datos = json.loads(texto_mensaje(contenido))
    except (ValueError, TypeError):
        raise ValueError("evidencia_academica_invalida") from None
    if (
        not isinstance(datos, dict)
        or set(datos) != CAMPOS
        or datos["sintetico"] is not True
        or datos["requiere_revision"] is not True
        or datos["efecto_comercial"] is not False
    ):
        raise ValueError("evidencia_academica_invalida")
    return json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verificar_lectura(contenido: object, esperado: str) -> str:
    """Comprueba que la herramienta devolvió el artefacto esperado, no solo un éxito."""
    canonico = evidencia_canonica(esperado)
    if canonico not in texto_mensaje(contenido):
        raise ValueError("lectura_academica_no_coincide")
    return canonico


def verificar_archivo(archivos: Mapping, esperado: str) -> str:
    """Comprueba el contenido del archivo virtual retenido en el estado del grafo."""
    if not isinstance(archivos, Mapping) or RUTA_HALLAZGOS not in archivos:
        raise ValueError("artefacto_academico_ausente")
    archivo = archivos[RUTA_HALLAZGOS]
    if not isinstance(archivo, Mapping):
        raise ValueError("artefacto_academico_invalido")
    contenido = archivo.get("content")
    if isinstance(contenido, list) and all(isinstance(linea, str) for linea in contenido):
        contenido = "\n".join(contenido)
    canonico = evidencia_canonica(contenido)
    if canonico != evidencia_canonica(esperado):
        raise ValueError("artefacto_academico_no_coincide")
    return canonico
