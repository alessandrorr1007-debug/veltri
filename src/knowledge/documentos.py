"""Fragmentación de las tres fuentes permitidas, sin leer pedidos ni mensajes."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.knowledge.vectorizacion import validar_tenant, validar_texto_publico

DATOS = Path(__file__).resolve().parents[2] / "data"
FUENTES = {"data/catalogo.json", "data/compatibilidad.json", "data/politicas.md"}


@dataclass(frozen=True)
class Fragmento:
    """Documento citable con metadatos de procedencia, nunca una instrucción."""

    id: str
    texto: str
    fuente: str
    referencia: str
    hash_fuente: str
    naturaleza: str = "demostracion_sintetica"

    def validar(self) -> None:
        """Revisa límites y fuentes sin aceptar enlaces o rutas arbitrarias."""
        if (self.fuente not in FUENTES or not self.referencia.startswith(self.fuente + "#")
                or not re.fullmatch(r"[a-zA-Z0-9:_-]{1,180}", self.id)
                or not re.fullmatch(r"[a-f0-9]{64}", self.hash_fuente)
                or self.naturaleza != "demostracion_sintetica"):
            raise ValueError("Metadatos de fragmento inválidos")
        for campo in (self.texto, self.referencia):
            validar_texto_publico(campo)


def construir_documentos(tenant: str, ruta: Path = DATOS) -> list[Fragmento]:
    """Lee únicamente fuentes de datos públicas; tenant requerido por interfaz."""
    validar_tenant(tenant)
    fragmentos = []

    def agregar(id_: str, contenido: str, nombre: str, ancla: str, hash_: str) -> None:
        fragmento = Fragmento(id_, contenido, "data/" + nombre,
                              f"data/{nombre}#{ancla}", hash_)
        fragmento.validar()
        fragmentos.append(fragmento)

    for nombre in ("catalogo.json", "compatibilidad.json", "politicas.md"):
        archivo = ruta / nombre
        if archivo.is_symlink() or archivo.stat().st_size > 2_000_000:
            raise ValueError("Las fuentes no pueden ser enlaces simbólicos")
        texto = archivo.read_text(encoding="utf-8-sig")
        validar_texto_publico(texto, maximo=2_000_000)
        hash_ = hashlib.sha256(archivo.read_bytes()).hexdigest()
        if nombre == "politicas.md":
            seccion = "introduccion"
            for numero, bloque in enumerate(re.split(r"\n\s*\n", texto.strip()), 1):
                if bloque.startswith("#"):
                    seccion = bloque.splitlines()[0].lstrip("# ")
                agregar(f"politica:{numero}", f"Sección: {seccion}\n{bloque}", nombre,
                        f"bloque-{numero}", hash_)
            continue
        datos = json.loads(texto)
        if datos.get("naturaleza") != "demostracion_sintetica":
            raise ValueError("Solo se admite el corpus sintético de demostración")
        aviso = datos["aviso"]
        if nombre == "catalogo.json":
            for producto in datos["productos"]:
                sku = producto["sku"]
                agregar("catalogo:" + sku,
                        aviso + "\n" + json.dumps(producto, ensure_ascii=False, sort_keys=True),
                        nombre, sku, hash_)
        else:
            for relacion in datos["relaciones_cpu_placa"]:
                par = relacion["cpu_sku"] + ":" + relacion["placa_sku"]
                agregar("compatibilidad:" + par,
                        aviso + "\n" + json.dumps(relacion, ensure_ascii=False, sort_keys=True),
                        nombre, par, hash_)
            for clave in ("sockets", "ram", "refrigeracion", "potencia", "montaje", "evidencia"):
                agregar("compatibilidad:" + clave,
                        aviso + "\n" + clave + ": "
                        + json.dumps(datos[clave], ensure_ascii=False, sort_keys=True),
                        nombre, clave, hash_)
    ids = [f.id for f in fragmentos]
    if len(ids) != len(set(ids)):
        raise ValueError("Identificadores de fragmento duplicados")
    return fragmentos
