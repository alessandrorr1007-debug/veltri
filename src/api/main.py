"""Punto de entrada de la API FastAPI: contrato ConsultaResponse y sin dependencias CDN."""

from pathlib import Path
from threading import RLock
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.empresas import autorizar, rutas_empresas
from src.config import Configuracion, cargar_configuracion
from src.graph.workflow import Orquestador
from src.knowledge.almacen import Almacen
from src.plataforma import Operaciones, Plataforma
from src.schemas.consulta import ConsultaResponse
from src.schemas.flujo import SolicitudAPI
from src.tools.catalogo import Catalogo
from src.tools.consulta_comercial import atender_consulta_comercial, inferir_parametros_consulta
from src.tools.registro import RegistroPorTenant


def crear_app(
    orquestador: Orquestador | None = None,
    guiones: dict[str, list[dict[str, Any]]] | None = None,
    configuracion: Configuracion | None = None,
    almacen: Almacen | None = None,
    plataforma: Plataforma | None = None,
) -> FastAPI:
    """Fábrica de la aplicación FastAPI sin dependencias externas de CDN ni texto libre."""
    config = configuracion or cargar_configuracion()
    if plataforma is not None:
        config = Configuracion(usar_mock=True)
    elif orquestador is None:
        orquestador = Orquestador(
            guiones=guiones or {},
            configuracion=config,
            catalogo=Catalogo(),
            registro=RegistroPorTenant(),
            almacen=almacen,
        )

    aplicacion = FastAPI(
        title="Veltri Tecnologic API",
        description="API del orquestador multiagente para cotización, compatibilidad y pedidos.",
        version="1.0-demo",
        docs_url=None,
        redoc_url=None,
    )

    if plataforma is None:
        aplicacion.state.orquestador = orquestador
        bloqueo_legado = RLock()
        aplicacion.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["*"],
        )
    else:
        aplicacion.state.plataforma = plataforma
        aplicacion.include_router(rutas_empresas(plataforma))

        @aplicacion.middleware("http")
        async def proteger_datos(request, call_next):
            origen = request.headers.get("origin")
            if (origen is not None and origen != f"{request.url.scheme}://{request.headers.get('host')}"
                    or request.headers.get("sec-fetch-site") == "cross-site"):
                return await http_error_handler(request, StarletteHTTPException(403))
            respuesta = await call_next(request)
            respuesta.headers["Cache-Control"] = "no-store"
            return respuesta

    @aplicacion.exception_handler(RequestValidationError)
    async def validador_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ConsultaResponse(
                status="error",
                intencion="desconocida",
                mensaje="Revisa los campos de la solicitud; entrada inválida.",
                hitl_requerido=False,
                motivos=["entrada_invalida"],
            ).model_dump(mode="json"),
        )

    @aplicacion.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        motivo = "ruta_no_encontrada" if exc.status_code == 404 else "error_http"
        return JSONResponse(
            status_code=exc.status_code,
            content=ConsultaResponse(
                status="error",
                intencion="desconocida",
                mensaje="No se pudo procesar la solicitud en esta ruta.",
                hitl_requerido=False,
                motivos=[motivo],
            ).model_dump(mode="json"),
        )

    @aplicacion.exception_handler(PermissionError)
    async def permiso_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
        return await http_error_handler(request, StarletteHTTPException(403))

    @aplicacion.exception_handler(Exception)
    async def fallo_general_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ConsultaResponse(
                status="error",
                intencion="desconocida",
                mensaje="No se pudo procesar la solicitud; revisa los parámetros.",
                hitl_requerido=False,
                motivos=["fallo_interno"],
            ).model_dump(mode="json"),
        )

    @aplicacion.post(
        "/consulta",
        response_model=ConsultaResponse,
        summary="Procesar consulta de cliente",
        description="Enruta la consulta a través de seguridad y el orquestador multiagente.",
    )
    def consultar_endpoint(
        peticion: SolicitudAPI, request: Request,
    ) -> ConsultaResponse | JSONResponse:
        acceso = None
        if plataforma is not None:
            acceso = autorizar(request)
            tenant_anidado = peticion.consulta.tenant_id if peticion.consulta else None
            tenants = (peticion.tenant_id, tenant_anidado)
            if any(tenant is not None and tenant != acceso.tenant for tenant in tenants):
                raise HTTPException(403)
        try:
            empresa = None
            orq = orquestador
            if acceso is not None:
                empresa, catalogo = plataforma.contexto(acceso.tenant)
                operaciones = Operaciones(plataforma, acceso)
                orq = Orquestador(guiones={}, configuracion=config, catalogo=catalogo,
                                  registro=operaciones, bandeja=operaciones,
                                  almacen=plataforma.almacen)
            if acceso is None:
                with bloqueo_legado:
                    return ejecutar_consulta(peticion, orq)
            respuesta = ejecutar_consulta(peticion, orq, empresa)
            if acceso is not None and respuesta.status not in ("error", "bloqueado"):
                plataforma.guardar_consulta(acceso, respuesta)
            return respuesta
        except PermissionError:
            raise HTTPException(403) from None
        except Exception:
            return JSONResponse(
                status_code=500,
                content=ConsultaResponse(
                    status="error", intencion="desconocida", hitl_requerido=False,
                    mensaje="No se pudo procesar la solicitud; revisa los parámetros.",
                    motivos=["fallo_interno"],
                ).model_dump(mode="json"),
            )

    def ejecutar_consulta(peticion, orq, empresa=None):
        mensaje = peticion.consulta.mensaje if peticion.consulta else peticion.mensaje
        if peticion.parametros is None and mensaje:
            _, params_inf = inferir_parametros_consulta(
                mensaje, orq._servicios.catalogo if empresa is not None else None,
            )
            if params_inf is not None:
                peticion = peticion.model_copy(update={"parametros": params_inf})

        if empresa is not None and peticion.parametros is None:
            consulta = peticion.a_solicitud_flujo().consulta
            return atender_consulta_comercial(
                catalogo=orq._servicios.catalogo, mensaje=consulta.mensaje,
                tenant_id=consulta.tenant_id, canal=consulta.canal, contexto=peticion.contexto,
                orquestador=orq, nombre_empresa=empresa.nombre, politicas=empresa.politicas,
            )

        if orq._servicios.configuracion.usar_mock:
            accion = "informacion"
            if peticion.parametros is not None:
                accion = peticion.parametros.tipo
            elif peticion.mensaje:
                msg = peticion.mensaje.lower()
                if "stock" in msg or "disponible" in msg:
                    accion = "stock"
                elif "pag" in msg or "transfer" in msg or "yape" in msg:
                    accion = "pago"
                elif "compatib" in msg or "socket" in msg:
                    accion = "compatibilidad"
                elif "cotiz" in msg or "armar" in msg or "precio" in msg:
                    accion = "armar"

            ids = {
                "armar": "A2",
                "cotizar": "A3",
                "compatibilidad": "A4",
                "stock": "A5",
                "pago": "A6",
                "pedido": "A7",
                "seguimiento": "A8",
            }
            guion_a1 = orq._servicios.guiones.get("A1")
            if not guion_a1 or guion_a1[0].get("accion") != accion:
                orq._servicios.guiones["A1"] = [{"accion": accion, "p": 1.0, "c": 1.0}]
            dom_id = ids.get(accion)
            if dom_id:
                guion_dom = orq._servicios.guiones.get(dom_id)
                if not guion_dom or guion_dom[0].get("accion") != accion:
                    orq._servicios.guiones[dom_id] = [{"accion": accion, "p": 1.0, "c": 1.0}]

        solicitud_flujo = peticion.a_solicitud_flujo()
        resultado = orq.consultar(solicitud_flujo)

        # Si faltan parámetros requeridos por ser consulta libre en chat,
        # resolvemos mediante el catálogo determinista y políticas de tienda.
        if (
            peticion.parametros is None
            and resultado.respuesta.status == "revision_humana"
            and resultado.respuesta.motivos == ["parametros_requeridos"]
        ):
            return atender_consulta_comercial(
                catalogo=orq._servicios.catalogo,
                mensaje=peticion.mensaje or "",
                tenant_id=peticion.tenant_id or "veltri",
                canal=peticion.canal or "web",
                contexto=peticion.contexto,
                orquestador=orq,
            )

        return resultado.respuesta

    @aplicacion.get(
        "/catalogo",
        summary="Listar catálogo de componentes",
        description="Retorna productos de demostración clasificados por categoría y stock.",
    )
    def listar_catalogo(request: Request) -> dict[str, Any]:
        if plataforma is not None:
            catalogo = plataforma.catalogo(autorizar(request).tenant)
        else:
            catalogo = orquestador._servicios.catalogo
        categorias = [
            "gpu",
            "cpu",
            "placa",
            "ram",
            "ssd",
            "fuente",
            "gabinete",
            "refrigeracion",
        ]
        resultado = {}
        for cat in categorias:
            prods = catalogo.listar(cat)
            prods.sort(key=lambda x: x["precio_centimos"])
            resultado[cat] = prods
        return {
            "moneda": "PEN",
            "categorias": resultado,
            "total_productos": sum(len(v) for v in resultado.values()),
        }

    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if (frontend_dir / "index.html").is_file():
        aplicacion.mount(
            "/",
            StaticFiles(directory=str(frontend_dir), html=True),
            name="frontend",
        )

    return aplicacion
