"""Punto de entrada de la API FastAPI: contrato ConsultaResponse y sin dependencias CDN."""

from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import Configuracion, cargar_configuracion
from src.graph.workflow import Orquestador
from src.knowledge.almacen import Almacen
from src.schemas.consulta import ConsultaResponse
from src.schemas.flujo import SolicitudAPI
from src.tools.catalogo import Catalogo
from src.tools.registro import RegistroPorTenant


def crear_app(
    orquestador: Orquestador | None = None,
    guiones: dict[str, list[dict[str, Any]]] | None = None,
    configuracion: Configuracion | None = None,
    almacen: Almacen | None = None,
) -> FastAPI:
    """Fábrica de la aplicación FastAPI sin dependencias externas de CDN ni texto libre."""
    config = configuracion or cargar_configuracion()
    if orquestador is None:
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

    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
    )

    aplicacion.state.orquestador = orquestador

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

    @aplicacion.exception_handler(Exception)
    async def fallo_general_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ConsultaResponse(
                status="error",
                intencion="desconocida",
                mensaje="No se pudo procesar la solicitud; revisa los parámetros o solicita ayuda.",
                hitl_requerido=False,
                motivos=["fallo_interno"],
            ).model_dump(mode="json"),
        )

    def obtener_orquestador(req: Request) -> Orquestador:
        return req.app.state.orquestador

    @aplicacion.post(
        "/consulta",
        response_model=ConsultaResponse,
        summary="Procesar consulta de cliente",
        description="Enruta la consulta a través de seguridad y el orquestador multiagente.",
    )
    async def consultar_endpoint(
        peticion: SolicitudAPI,
        orq: Annotated[Orquestador, Depends(obtener_orquestador)],
    ) -> ConsultaResponse | JSONResponse:
        try:
            solicitud_flujo = peticion.a_solicitud_flujo()
            resultado = orq.consultar(solicitud_flujo)
            return resultado.respuesta
        except Exception:
            return JSONResponse(
                status_code=500,
                content=ConsultaResponse(
                    status="error",
                    intencion="desconocida",
                    mensaje=(
                        "No se pudo procesar la solicitud; revisa los parámetros o solicita ayuda."
                    ),
                    hitl_requerido=False,
                    motivos=["fallo_interno"],
                ).model_dump(mode="json"),
            )

    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if (frontend_dir / "index.html").is_file():
        aplicacion.mount(
            "/",
            StaticFiles(directory=str(frontend_dir), html=True),
            name="frontend",
        )

    return aplicacion


app = crear_app()
