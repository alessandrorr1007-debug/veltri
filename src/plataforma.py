"""Persistencia comercial local. Las identidades se resuelven en el servidor."""

import base64
import binascii
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import struct
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from pydantic import Field, JsonValue, field_validator

from src.core.hitl import BandejaRevision, resolver_revision
from src.knowledge.documentos import construir_documentos
from src.knowledge.vectorizacion import validar_tenant, validar_texto_publico
from src.schemas.base import Contrato
from src.schemas.hitl import Revision
from src.tools.catalogo import Catalogo
from src.tools.pedidos import RegistroDemo

Rol = Literal["administrador", "operador", "cliente"]
Identificador = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")]
Color = Annotated[str, Field(pattern=r"^#[a-fA-F0-9]{6}$")]
Etiqueta = Annotated[str, Field(min_length=1, max_length=100)]


class Empresa(Contrato):
    nombre: Etiqueta
    descripcion: Annotated[str, Field(min_length=1, max_length=500)]
    logo: Annotated[str, Field(min_length=1, max_length=4)]
    logo_png: Annotated[str, Field(max_length=43_692)] | None = None
    color: Color
    color_secundario: Color = "#475569"
    servicios: Annotated[list[Etiqueta], Field(max_length=12)]
    politicas: Annotated[str, Field(min_length=1, max_length=4000)]
    activa: bool = True

    @field_validator("logo_png")
    @classmethod
    def validar_logo(cls, valor):
        if valor is None:
            return None
        try:
            png = base64.b64decode(valor, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("Se requiere un PNG local codificado") from None
        if (not 33 <= len(png) <= 32_768
                or not png.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
                or not png.endswith(b"\x00\x00\x00\x00IEND\xaeB\x60\x82")
                or not all(1 <= d <= 256 for d in struct.unpack(">II", png[16:24]))):
            raise ValueError("Logo PNG inválido, admite hasta 256 × 256 y 32 KiB")
        return valor


class Producto(Contrato):
    categoria: Literal["gpu", "cpu", "placa", "ram", "ssd", "fuente", "gabinete", "refrigeracion"]
    precio_centimos: Annotated[int, Field(strict=True, gt=0, le=100_000_000)]
    stock: Annotated[int, Field(strict=True, ge=0, le=1_000_000)]
    nombre: Etiqueta
    especificaciones: dict[str, JsonValue]


@dataclass(frozen=True)
class Acceso:
    usuario: str
    tenant: str
    rol: str

    @property
    def gestor(self) -> bool:
        return self.rol in ("general", "administrador")


class Plataforma:
    def __init__(self, ruta: Path, almacen):
        self.ruta = ruta
        self._intentos_login = Lock()
        self._fallos_login: list[float] = []
        self._fichas = {p["categoria"]: p["especificaciones"] for p in Catalogo().listar()}
        self.almacen = almacen
        ruta.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        ruta.touch(mode=0o600, exist_ok=True)
        with self.db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS empresas (
                    id TEXT PRIMARY KEY, datos TEXT NOT NULL, activa INTEGER NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 1, indexada INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS usuarios (
                    id TEXT PRIMARY KEY, clave BLOB NOT NULL, sal BLOB NOT NULL,
                    general INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS miembros (
                    tenant TEXT REFERENCES empresas, usuario TEXT REFERENCES usuarios,
                    rol TEXT NOT NULL, PRIMARY KEY (tenant, usuario));
                CREATE TABLE IF NOT EXISTS sesiones (
                    token TEXT PRIMARY KEY, usuario TEXT REFERENCES usuarios,
                    caduca INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS productos (
                    tenant TEXT REFERENCES empresas, sku TEXT, datos TEXT NOT NULL,
                    PRIMARY KEY (tenant, sku));
                CREATE TABLE IF NOT EXISTS operaciones (
                    tenant TEXT REFERENCES empresas, tipo TEXT, id TEXT, usuario TEXT NOT NULL,
                    datos TEXT NOT NULL, PRIMARY KEY (tenant, tipo, id));
                CREATE INDEX IF NOT EXISTS historial
                    ON operaciones (tenant, usuario, tipo);
            """)

    @contextmanager
    def db(self, escribir=False):
        db = sqlite3.connect(self.ruta, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            with db:
                db.execute("BEGIN IMMEDIATE" if escribir else "BEGIN")
                yield db
        finally:
            db.close()

    @staticmethod
    def _clave(clave: str, sal: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, 600_000)

    def crear_usuario(self, usuario, clave, *, acceso=None, rol="cliente"):
        validar_tenant(usuario)
        if not 12 <= len(clave) <= 128:
            raise ValueError("Longitud de contraseña inválida")
        sal = secrets.token_bytes(16)
        derivada = self._clave(clave, sal)
        with self.db(True) as db:
            if acceso is None and db.execute("SELECT 1 FROM usuarios WHERE general=1").fetchone():
                raise ValueError("Ya existe administrador general")
            if acceso is not None:
                self.vigente(db, acceso)
            db.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)",
                       (usuario, derivada, sal, acceso is None))
            if acceso is not None:
                db.execute("INSERT INTO miembros VALUES (?, ?, ?)", (acceso.tenant, usuario, rol))

    def login(self, usuario, clave):
        # El perfil local limita trabajo de derivación concurrente y reintentos fallidos.
        if not self._intentos_login.acquire(blocking=False):
            raise BlockingIOError("Inicio de sesión temporalmente ocupado")
        try:
            ahora = time.monotonic()
            self._fallos_login = [t for t in self._fallos_login if ahora - t < 60]
            if len(self._fallos_login) >= 12:
                raise BlockingIOError("Límite temporal de intentos")
            token = self._autenticar(usuario, clave)
            if token is None:
                self._fallos_login.append(ahora)
            return token
        finally:
            self._intentos_login.release()

    def _autenticar(self, usuario, clave):
        with self.db() as db:
            fila = db.execute("SELECT * FROM usuarios WHERE id=?", (usuario,)).fetchone()
        derivada = self._clave(clave, fila["sal"] if fila else bytes(16))
        if fila is None or not hmac.compare_digest(derivada, fila["clave"]):
            return None
        token = secrets.token_urlsafe(32)
        ahora = int(time.time())
        with self.db(True) as db:
            db.execute("DELETE FROM sesiones WHERE caduca<=?", (ahora,))
            db.execute("INSERT INTO sesiones VALUES (?, ?, ?)",
                       (self._hash(token), usuario, ahora + 8 * 3600))
        return token

    @staticmethod
    def _hash(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def logout(self, token):
        with self.db(True) as db:
            db.execute("DELETE FROM sesiones WHERE token=?", (self._hash(token),))

    def identidad(self, token):
        if not token or len(token) != 43:
            return None
        with self.db() as db:
            return db.execute(
                "SELECT usuarios.id, general FROM sesiones JOIN usuarios ON usuario=usuarios.id "
                "WHERE token=? AND caduca>?", (self._hash(token), time.time()),
            ).fetchone()

    def empresas(self, identidad):
        with self.db() as db:
            if identidad["general"]:
                filas = db.execute("SELECT id, datos FROM empresas ORDER BY id").fetchall()
            else:
                filas = db.execute(
                    "SELECT id, datos FROM empresas JOIN miembros ON id=tenant "
                    "WHERE usuario=? AND activa=1 ORDER BY id", (identidad["id"],),
                ).fetchall()
        return [{"id": f["id"], **json.loads(f["datos"])} for f in filas]

    def acceso(self, identidad, tenant):
        with self.db() as db:
            fila = db.execute(
                "SELECT activa, rol FROM empresas LEFT JOIN miembros "
                "ON id=tenant AND usuario=? WHERE id=?", (identidad["id"], tenant),
            ).fetchone()
        if not fila or not fila["activa"] or not (identidad["general"] or fila["rol"]):
            return None
        return Acceso(identidad["id"], tenant, "general" if identidad["general"] else fila["rol"])

    @staticmethod
    def vigente(db, acceso):
        fila = db.execute(
            "SELECT activa, rol FROM empresas LEFT JOIN miembros "
            "ON id=tenant AND usuario=? WHERE id=?", (acceso.usuario, acceso.tenant),
        ).fetchone()
        if (not fila or not fila["activa"]
                or (acceso.rol != "general" and fila["rol"] != acceso.rol)):
            raise PermissionError("El acceso dejó de estar vigente")

    def empresa(self, tenant):
        with self.db() as db:
            fila = db.execute("SELECT datos FROM empresas WHERE id=?", (tenant,)).fetchone()
        return Empresa.model_validate_json(fila["datos"])

    def guardar_empresa(self, tenant, empresa, *, crear=False, acceso=None):
        validar_tenant(tenant)
        for valor in (empresa.nombre, empresa.descripcion, empresa.logo,
                      empresa.politicas, *empresa.servicios):
            validar_texto_publico(valor)
        datos = empresa.model_dump_json()
        with self.db(True) as db:
            if acceso is not None:
                self.vigente(db, acceso)
            if crear:
                db.execute("INSERT INTO empresas (id, datos, activa) VALUES (?, ?, ?)",
                           (tenant, datos, empresa.activa))
            else:
                actualizado = db.execute(
                    "UPDATE empresas SET datos=?, activa=?, revision=revision+1 WHERE id=?",
                    (datos, empresa.activa, tenant),
                )
                if not actualizado.rowcount:
                    raise LookupError("Empresa inexistente")

    def membresia(self, tenant, usuario, rol, acceso=None):
        with self.db(True) as db:
            if acceso is not None:
                self.vigente(db, acceso)
            if rol is None:
                db.execute("DELETE FROM miembros WHERE tenant=? AND usuario=?", (tenant, usuario))
            else:
                db.execute("INSERT INTO miembros VALUES (?, ?, ?) "
                           "ON CONFLICT (tenant, usuario) DO UPDATE SET rol=excluded.rol",
                           (tenant, usuario, rol))

    def miembros(self, tenant):
        with self.db() as db:
            return [dict(f) for f in db.execute(
                "SELECT usuario, rol FROM miembros WHERE tenant=? ORDER BY usuario", (tenant,),
            )]

    @staticmethod
    def _productos(db, tenant):
        return [json.loads(f[0]) for f in db.execute(
            "SELECT datos FROM productos WHERE tenant=? ORDER BY sku", (tenant,),
        )]

    def catalogo(self, tenant):
        with self.db() as db:
            return Catalogo(productos=self._productos(db, tenant))

    def producto(self, tenant, sku, producto, acceso=None):
        if not re.fullmatch(r"(?=.{1,80}$)[A-Z0-9]+(?:-[A-Z0-9]+)+", sku):
            raise ValueError("SKU inválido")
        with self.db(True) as db:
            if acceso is not None:
                self.vigente(db, acceso)
            if producto is None:
                db.execute("DELETE FROM productos WHERE tenant=? AND sku=?", (tenant, sku))
            else:
                ficha = producto.especificaciones
                plantilla = self._fichas[producto.categoria]
                for campo, ejemplo in plantilla.items():
                    valor = ficha.get(campo)
                    if (type(valor) is not type(ejemplo)
                            or isinstance(valor, int) and valor < 0
                            or isinstance(valor, list)
                            and any(not isinstance(x, str) for x in valor)
                            or isinstance(valor, dict) and any(type(x) is not int or x < 0
                                                               for x in valor.values())):
                        raise ValueError("Ficha técnica inválida")
                datos = json.dumps({"sku": sku, **producto.model_dump()}, ensure_ascii=False)
                if len(datos) > 3500:
                    raise ValueError("Ficha demasiado extensa")
                total = db.execute("SELECT COUNT(*) FROM productos WHERE tenant=? AND sku!=?",
                                   (tenant, sku)).fetchone()[0]
                if total >= 500:
                    raise ValueError("Límite local de productos")
                validar_texto_publico(datos)
                db.execute("INSERT INTO productos VALUES (?, ?, ?) "
                           "ON CONFLICT (tenant, sku) DO UPDATE SET datos=excluded.datos",
                           (tenant, sku, datos))
            db.execute("UPDATE empresas SET revision=revision+1 WHERE id=?", (tenant,))

    def sembrar(self):
        originales = Catalogo().listar()
        demos = (
            ("veltri", "Veltri Tecnologic", "VT", "#2563eb",
             "Políticas de cotización y stock. Garantía sintética de doce meses. "
             "Despacho simulado a Lima y provincias; revisión de pago manual."),
            ("andina", "Andina Componentes", "AC", "#047857",
             "Políticas de cotización y stock. Garantía sintética de seis meses. "
             "Despacho simulado por recojo en tienda; revisión de pago manual."),
            ("pacifico", "Pacífico PC", "PC", "#7e22ce",
             "Políticas de cotización y stock. Garantía sintética de dieciocho meses. "
             "Envío simulado regional; revisión de pago manual."),
        )
        with self.db(True) as db:
            for indice, (tenant, nombre, logo, color, politicas) in enumerate(demos):
                empresa = Empresa(nombre=nombre, logo=logo, color=color, politicas=politicas,
                                  descripcion="Empresa de demostración con datos sintéticos.",
                                  servicios=["Venta de componentes", "Armado de PC"])
                if not db.execute(
                    "INSERT OR IGNORE INTO empresas (id, datos, activa) VALUES (?, ?, 1)",
                    (tenant, empresa.model_dump_json()),
                ).rowcount:
                    continue
                for pos, original in enumerate(originales):
                    if indice and pos % 11 == 10 - indice:
                        continue
                    producto = dict(original)
                    if indice:
                        producto["precio_centimos"] += indice * 2500
                        producto["stock"] = (producto["stock"] + indice) % 13
                    db.execute("INSERT INTO productos VALUES (?, ?, ?)",
                               (tenant, producto["sku"], json.dumps(producto)))

    def contexto(self, tenant):
        """Sincroniza RAG y la instantánea comercial antes de liberar la escritura."""
        with self.db() as db:
            empresa = db.execute("SELECT * FROM empresas WHERE id=?", (tenant,)).fetchone()
            if empresa and empresa["activa"] and empresa["indexada"] == empresa["revision"]:
                return self._contexto(db, empresa, tenant)
        with self.db(True) as db:
            empresa = db.execute("SELECT * FROM empresas WHERE id=?", (tenant,)).fetchone()
            if not empresa or not empresa["activa"]:
                raise PermissionError("Empresa no disponible")
            datos, catalogo = self._contexto(db, empresa, tenant)
            if empresa["indexada"] != empresa["revision"]:
                corpus = json.dumps({"naturaleza": "demostracion_sintetica",
                                     "aviso": "Datos sintéticos", "productos": catalogo.listar()},
                                    ensure_ascii=False)
                self.almacen.reemplazar(tenant, construir_documentos(tenant, fuentes={
                    "catalogo.json": corpus, "politicas.md": datos.politicas,
                }))
                db.execute("UPDATE empresas SET indexada=revision WHERE id=?", (tenant,))
            return datos, catalogo

    @staticmethod
    def _contexto(db, empresa, tenant):
        return Empresa.model_validate_json(empresa["datos"]), Catalogo(
            productos=Plataforma._productos(db, tenant),
        )

    def historial(self, acceso):
        filtro = "tenant=?"
        params = (acceso.tenant,)
        if acceso.rol == "cliente":
            filtro += " AND usuario=? AND tipo!='revision'"
            params += (acceso.usuario,)
        with self.db() as db:
            filas = db.execute(
                f"SELECT tipo, id, datos FROM operaciones WHERE {filtro} "
                "ORDER BY rowid DESC LIMIT 100", params,
            ).fetchall()
            stats = db.execute(
                f"SELECT tipo, count(*) FROM operaciones WHERE {filtro} GROUP BY tipo", params,
            )
            return {"estadisticas": dict(stats),
                    "historial": [{"tipo": f[0], "id": f[1], "datos": json.loads(f[2])}
                                  for f in filas]}

    def guardar_consulta(self, acceso, respuesta):
        # No se guardan mensajes de entrada, comprobantes ni texto libre.
        datos = respuesta.model_dump(mode="json", include={
            "intencion", "status", "motivos", "hitl_requerido", "cotizacion",
        })
        with self.db(True) as db:
            self.vigente(db, acceso)
            tipo = "cotizacion" if respuesta.cotizacion else "consulta"
            db.execute("INSERT INTO operaciones VALUES (?, ?, ?, ?, ?)",
                       (acceso.tenant, tipo, secrets.token_hex(16), acceso.usuario,
                        json.dumps(datos)))


class Operaciones:
    """Adaptador de dominio sin capacidad de elegir otro tenant."""

    def __init__(self, plataforma, acceso):
        self.plataforma = plataforma
        self.acceso = acceso

    def _validar(self, tenant):
        if tenant != self.acceso.tenant:
            raise PermissionError("Ámbito inválido")

    def _leer(self, db, tipo, clave):
        return db.execute(
            "SELECT usuario, datos FROM operaciones WHERE tenant=? AND tipo=? AND id=?",
            (self.acceso.tenant, tipo, clave),
        ).fetchone()

    @property
    def alias(self):
        digest = hashlib.sha256(self.acceso.usuario.encode()).digest()[:16]
        return "demo_" + "".join(chr(97 + (byte >> 4)) + chr(97 + (byte & 15))
                                 for byte in digest)

    def registrar(self, tenant, cliente, seleccion, canal, catalogo):
        self._validar(tenant)
        resultado = RegistroDemo().registrar(self.alias, seleccion, canal, catalogo)
        pedido = resultado["pedido"]
        with self.plataforma.db(True) as db:
            self.plataforma.vigente(db, self.acceso)
            db.execute(
                "INSERT OR IGNORE INTO operaciones VALUES (?, 'cliente', ?, ?, ?)",
                (tenant, self.alias, self.acceso.usuario, json.dumps({"alias": self.alias})),
            )
            nuevo = db.execute(
                "INSERT OR IGNORE INTO operaciones VALUES (?, 'pedido', ?, ?, ?)",
                (tenant, pedido["clave"], self.acceso.usuario, json.dumps(pedido)),
            ).rowcount
        return {**resultado, "duplicado": not nuevo, "registros_creados": nuevo}

    def consultar(self, tenant, clave):
        self._validar(tenant)
        RegistroDemo().consultar(clave)
        with self.plataforma.db() as db:
            fila = self._leer(db, "pedido", clave)
        if fila and (self.acceso.rol != "cliente" or fila["usuario"] == self.acceso.usuario):
            return json.loads(fila["datos"])
        return None

    def encolar(self, tenant, solicitud):
        self._validar(tenant)
        resultado = BandejaRevision().encolar(tenant, solicitud)
        clave = resultado.revision.id
        with self.plataforma.db(True) as db:
            self.plataforma.vigente(db, self.acceso)
            fila = self._leer(db, "revision", clave)
            if fila:
                return resultado.model_copy(update={
                    "duplicado": True, "revision": Revision.model_validate_json(fila["datos"]),
                })
            db.execute("INSERT INTO operaciones VALUES (?, 'revision', ?, ?, ?)",
                       (tenant, clave, self.acceso.usuario, resultado.revision.model_dump_json()))
        return resultado

    def obtener(self, tenant, id_):
        self._validar(tenant)
        with self.plataforma.db() as db:
            fila = self._leer(db, "revision", id_)
        if not fila:
            raise ValueError("Revisión no encontrada")
        return Revision.model_validate_json(fila["datos"])

    def resolver(self, tenant, id_, resolucion):
        self._validar(tenant)
        if self.acceso.rol == "cliente":
            raise PermissionError("Revisión reservada a operadores")
        with self.plataforma.db(True) as db:
            self.plataforma.vigente(db, self.acceso)
            fila = self._leer(db, "revision", id_)
            if not fila:
                raise ValueError("Revisión no encontrada")
            registro = Revision.model_validate_json(fila["datos"])
            revision = resolver_revision(registro, resolucion)
            db.execute("UPDATE operaciones SET datos=? WHERE tenant=? AND tipo='revision' AND id=?",
                       (revision.model_dump_json(), tenant, id_))
            return revision
