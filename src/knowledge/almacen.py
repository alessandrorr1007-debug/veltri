"""Almacén Chroma local con tenant obligatorio y snapshots citables."""

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.errors import NotFoundError
from filelock import FileLock

from src.knowledge.documentos import FUENTES, Fragmento
from src.knowledge.vectorizacion import (
    VERSION_VECTOR,
    tokens,
    validar_tenant,
    validar_texto_publico,
    vector,
)


class Almacen:
    """Cada tenant tiene colección y bloqueo propios; sin tenant global por defecto."""

    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta.resolve()
        self._ruta.mkdir(parents=True, exist_ok=True)
        (self._ruta / ".locks").mkdir(exist_ok=True)
        self._cliente = chromadb.PersistentClient(
            path=str(self._ruta), settings=Settings(anonymized_telemetry=False))

    def _nombre(self, tenant: str) -> str:
        validar_tenant(tenant)
        return "veltri_" + hashlib.sha256(tenant.encode()).hexdigest()[:40]

    def _bloqueo(self, tenant: str) -> FileLock:
        return FileLock(self._ruta / ".locks" / (self._nombre(tenant) + ".lock"), timeout=15)

    def _coleccion(self, tenant: str, crear: bool = False) -> Any:
        nombre = self._nombre(tenant)
        try:
            coleccion = self._cliente.get_collection(name=nombre, embedding_function=None)
        except NotFoundError:
            if not crear:
                return None
            coleccion = self._cliente.create_collection(
                name=nombre, embedding_function=None,
                metadata={"tenant": tenant, "vector": VERSION_VECTOR, "activo": "vacio"},
                configuration={"hnsw": {"space": "cosine"}})
        if (coleccion.metadata.get("tenant") != tenant
                or coleccion.metadata.get("vector") != VERSION_VECTOR):
            raise ValueError("Colección incompatible con el tenant o vectorización")
        return coleccion

    def reemplazar(self, tenant: str, fragmentos: list[Fragmento]) -> dict[str, Any]:
        """Publica snapshot tras escribirlo completo; reingesta elimina obsoletos."""
        validar_tenant(tenant)
        if not fragmentos or len(fragmentos) > 2000:
            raise ValueError("La ingesta requiere entre 1 y 2000 fragmentos")
        ids = [f.id for f in fragmentos]
        if len(ids) != len(set(ids)):
            raise ValueError("Fragmentos duplicados")
        for fragmento in fragmentos:
            fragmento.validar()
        ordenados = sorted(fragmentos, key=lambda f: f.id)
        contenido = json.dumps([asdict(f) for f in ordenados], ensure_ascii=False, sort_keys=True)
        snapshot = hashlib.sha256((VERSION_VECTOR + contenido).encode()).hexdigest()
        vectores = [vector(f.texto) for f in ordenados]
        with self._bloqueo(tenant):
            coleccion = self._coleccion(tenant, crear=True)
            for inicio in range(0, len(ordenados), 128):
                lote = ordenados[inicio:inicio + 128]
                coleccion.upsert(
                    ids=[snapshot + ":" + f.id for f in lote],
                    documents=[f.texto for f in lote],
                    embeddings=vectores[inicio:inicio + 128],
                    metadatas=[{"id": f.id, "fuente": f.fuente, "referencia": f.referencia,
                                "hash_fuente": f.hash_fuente, "naturaleza": f.naturaleza,
                                "tenant": tenant, "snapshot": snapshot} for f in lote])
            coleccion.modify(metadata={"tenant": tenant, "vector": VERSION_VECTOR,
                                       "activo": snapshot})
            coleccion.delete(where={"$and": [{"tenant": tenant}, {"snapshot": {"$ne": snapshot}}]})
        return {"fragmentos": len(ordenados), "snapshot": snapshot,
                "naturaleza": "demostracion_sintetica"}

    def contar(self, tenant: str) -> int:
        """Cuenta solo fragmentos activos del tenant solicitado."""
        validar_tenant(tenant)
        with self._bloqueo(tenant):
            coleccion = self._coleccion(tenant)
            if coleccion is None:
                return 0
            datos = coleccion.get(where={"$and": [{"tenant": tenant},
                                                  {"snapshot": coleccion.metadata["activo"]}]},
                                   include=[])
            return len(datos["ids"])

    def buscar(self, tenant: str, consulta: str, limite: int = 5,
               fuente: str | None = None) -> list[dict[str, Any]]:
        """Recupera contexto citado; distancia vectorial no es confianza ni permiso."""
        validar_tenant(tenant)
        validar_texto_publico(consulta)
        if type(limite) is not int or not 1 <= limite <= 20:
            raise ValueError("Límite inválido; debe ser entero entre 1 y 20")
        if len(consulta) > 2000 or (fuente is not None and fuente not in FUENTES):
            raise ValueError("Consulta o fuente inválida")
        embedding = vector(consulta)
        terminos = tokens(consulta)
        claves_exactas = {"catalogo:" + t.upper() for t in terminos
                         if re.fullmatch(r"(?:cpu|mb|gpu|ram|ssd|psu|case|cool)-[a-z0-9-]+", t)}
        with self._bloqueo(tenant):
            coleccion = self._coleccion(tenant)
            if coleccion is None:
                return []
            filtros = [{"tenant": tenant}, {"snapshot": coleccion.metadata["activo"]}]
            if fuente is not None:
                filtros.append({"fuente": fuente})
            where = {"$and": filtros}
            total = len(coleccion.get(where=where, include=[])["ids"])
            if total == 0:
                return []
            datos = coleccion.query(query_embeddings=[embedding], where=where,
                                     n_results=min(total, max(limite * 4, 20)),
                                     include=["documents", "metadatas", "distances"])
            candidatos = list(zip(datos["documents"][0], datos["metadatas"][0],
                                  datos["distances"][0], strict=True))
            if claves_exactas:
                exactos = coleccion.get(
                    where={"$and": filtros + [{"id": {"$in": sorted(claves_exactas)}}]},
                    include=["documents", "metadatas", "embeddings"])
                for texto, meta, emb in zip(exactos["documents"], exactos["metadatas"],
                                            exactos["embeddings"], strict=True):
                    distancia = 1 - sum(a * float(b) for a, b in zip(embedding, emb, strict=True))
                    candidatos.append((texto, meta, distancia))
            resultado = []
            vistos = set()
            for texto, meta, distancia in candidatos:
                if meta["tenant"] != tenant or meta["snapshot"] != coleccion.metadata["activo"]:
                    raise ValueError("Resultado fuera del ámbito solicitado")
                if meta["id"] in vistos or not terminos.intersection(tokens(texto)):
                    continue
                vistos.add(meta["id"])
                resultado.append({"id": meta["id"], "texto": texto,
                                  "fuente": meta["fuente"], "referencia": meta["referencia"],
                                  "hash_fuente": meta["hash_fuente"],
                                  "snapshot": meta["snapshot"], "distancia": distancia,
                                  "naturaleza": meta["naturaleza"]})
        return sorted(resultado, key=lambda r: (r["id"] not in claves_exactas,
                                                r["distancia"], r["id"]))[:limite]
