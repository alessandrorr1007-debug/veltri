"""Sesiones locales y API de administración con autorización por solicitud."""

import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field

from src.plataforma import Acceso, Empresa, Identificador, Operaciones, Producto, Rol
from src.schemas.base import SKU, Contrato, HashPedido
from src.schemas.hitl import ResolucionRevision

COOKIE = "veltri_sesion"


class Credenciales(Contrato):
    usuario: Identificador
    clave: Annotated[str, Field(min_length=12, max_length=128, repr=False)]


class AltaUsuario(Credenciales):
    rol: Rol


class Permiso(Contrato):
    rol: Rol | None


def identificar(request: Request):
    identidad = request.app.state.plataforma.identidad(request.cookies.get(COOKIE))
    if identidad is None:
        raise HTTPException(401)
    return identidad


def autorizar(request: Request):
    # Un header selecciona ámbito; la sesión y la base de datos conceden autorización.
    plataforma = request.app.state.plataforma
    identidad = identificar(request)
    tenants = request.headers.getlist("X-Veltri-Tenant")
    acceso = plataforma.acceso(identidad, tenants[0]) if len(tenants) == 1 else None
    if acceso is None:
        raise HTTPException(403)
    return acceso


def gestionar(request: Request):
    acceso = autorizar(request)
    if not acceso.gestor:
        raise HTTPException(403)
    return acceso


def exigir_general(request: Request):
    if not identificar(request)["general"]:
        raise HTTPException(403)


class Resolver(Contrato):
    accion: Literal["aprobar_demo", "rechazar", "solicitar_correccion"]


def rutas_empresas(plataforma):
    router = APIRouter(prefix="/plataforma")

    @router.post("/sesion")
    def sesion(credenciales: Credenciales, request: Request, response: Response):
        try:
            token = plataforma.login(credenciales.usuario, credenciales.clave)
        except BlockingIOError:
            raise HTTPException(429) from None
        if token is None:
            raise HTTPException(401)
        anterior = request.cookies.get(COOKIE)
        if anterior:
            plataforma.logout(anterior)
        response.set_cookie(COOKIE, token, httponly=True, samesite="strict", max_age=8 * 3600)
        return {"autenticado": True}

    @router.delete("/sesion")
    def salir(request: Request, response: Response):
        token = request.cookies.get(COOKIE)
        if token:
            plataforma.logout(token)
        response.delete_cookie(COOKIE, httponly=True, samesite="strict")
        return {"autenticado": False}

    @router.get("/empresas")
    def empresas(identidad: Annotated[sqlite3.Row, Depends(identificar)]):
        empresas = plataforma.empresas(identidad)
        for empresa in empresas:
            acceso = plataforma.acceso(identidad, empresa["id"])
            empresa["rol"] = acceso.rol if acceso else None
        return {"empresas": empresas, "general": bool(identidad["general"])}

    @router.post("/empresas/{tenant}", status_code=201, dependencies=[Depends(exigir_general)])
    def alta(tenant: Identificador, empresa: Empresa):
        try:
            plataforma.guardar_empresa(tenant, empresa, crear=True)
        except sqlite3.IntegrityError:
            raise HTTPException(409) from None
        except ValueError:
            raise HTTPException(422) from None
        return empresa

    @router.put("/empresas/{tenant}")
    def editar(tenant: Identificador, empresa: Empresa, request: Request):
        identidad = identificar(request)
        actual = plataforma.acceso(identidad, tenant)
        if not identidad["general"] and (actual is None or not actual.gestor or not empresa.activa):
            raise HTTPException(403)
        try:
            plataforma.guardar_empresa(tenant, empresa, acceso=None if identidad["general"]
                                       else actual)
        except LookupError:
            raise HTTPException(404) from None
        except ValueError:
            raise HTTPException(422) from None
        return empresa

    @router.get("/miembros")
    def miembros(acceso: Annotated[Acceso, Depends(gestionar)]):
        return plataforma.miembros(acceso.tenant)

    @router.post("/miembros", status_code=201)
    def usuario(alta: AltaUsuario, acceso: Annotated[Acceso, Depends(gestionar)]):
        try:
            plataforma.crear_usuario(alta.usuario, alta.clave, acceso=acceso, rol=alta.rol)
        except sqlite3.IntegrityError:
            raise HTTPException(409) from None
        return {"usuario": alta.usuario, "rol": alta.rol}

    @router.put("/miembros/{usuario}")
    def permiso(
        usuario: Identificador, permiso: Permiso, acceso: Annotated[Acceso, Depends(gestionar)],
    ):
        if usuario == acceso.usuario:
            raise HTTPException(403)
        try:
            plataforma.membresia(acceso.tenant, usuario, permiso.rol, acceso)
        except sqlite3.IntegrityError:
            raise HTTPException(404) from None
        return {"usuario": usuario, "rol": permiso.rol}

    @router.put("/productos/{sku}")
    def producto(sku: SKU, producto: Producto, acceso: Annotated[Acceso, Depends(gestionar)]):
        try:
            plataforma.producto(acceso.tenant, sku, producto, acceso)
        except ValueError:
            raise HTTPException(422) from None
        return producto

    @router.delete("/productos/{sku}")
    def retirar_producto(sku: SKU, acceso: Annotated[Acceso, Depends(gestionar)]):
        plataforma.producto(acceso.tenant, sku, None, acceso)
        return {"retirado": True}

    @router.get("/historial")
    def historial(acceso: Annotated[Acceso, Depends(autorizar)]):
        return plataforma.historial(acceso)

    @router.post("/revisiones/{clave}")
    def resolver(
        clave: HashPedido, solicitud: Resolver, acceso: Annotated[Acceso, Depends(autorizar)],
    ):
        if acceso.rol == "cliente":
            raise HTTPException(403)
        operaciones = Operaciones(plataforma, acceso)
        motivos = {"aprobar_demo": "informacion_verificada", "rechazar": "revision_rechazada",
                   "solicitar_correccion": "requiere_correccion"}
        try:
            return operaciones.resolver(acceso.tenant, clave, ResolucionRevision(
                accion=solicitud.accion, motivo=motivos[solicitud.accion],
                revisor=operaciones.alias,
            ))
        except ValueError:
            raise HTTPException(409) from None

    return router
