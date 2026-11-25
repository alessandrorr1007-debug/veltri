"""Instalación y ciclo de vida del despliegue nativo de Veltri."""

import argparse
import ipaddress
import json
import os
import re
import socket
import subprocess
import sys
import venv
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

HOST = "127.0.0.1"
PUERTO = 8765
TENANT = "veltri"
ENTORNO_LOCAL = {
    "USE_MOCK_LLM": "1", "LLM_PROVIDER": "gemini", "LLM_MODEL": "", "GOOGLE_API_KEY": "",
    "VELTRI_TRACING_ENABLED": "0", "VELTRI_TRACING_ALLOW_EXTERNAL": "0",
    "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false",
    "LANGSMITH_OTEL_ENABLED": "false", "LANGSMITH_API_KEY": "", "LANGCHAIN_API_KEY": "",
}


class ErrorLocal(RuntimeError):
    """Mensaje operativo fijo o basado solo en los parámetros de la CLI."""


def _exigir_python() -> None:
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 14):
        raise ErrorLocal("El perfil fijado de instalación requiere CPython 3.14.")


def instalar(destino: Path, desarrollo: bool) -> None:
    _exigir_python()
    interprete = destino / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interprete.is_file():
        if destino.exists() and any(destino.iterdir()):
            raise ErrorLocal("El destino contiene archivos y no es un entorno virtual reconocido.")
        venv.EnvBuilder(with_pip=True).create(destino)
    if not (destino / "pyvenv.cfg").is_file():
        raise ErrorLocal("El intérprete elegido no pertenece a un entorno virtual reconocido.")
    version = subprocess.check_output(
        [str(interprete), "-c", "import sys; print(sys.version_info[:2])"], text=True,
    ).strip()
    if version != "(3, 14)":
        raise ErrorLocal("El entorno existente no usa Python 3.14. Elige otro destino.")
    manifiesto = RAIZ / ("requirements-dev.txt" if desarrollo else "requirements.txt")
    subprocess.run([str(interprete), "-m", "pip", "install", "-r", str(manifiesto)], check=True)
    subprocess.run([str(interprete), "-m", "pip", "check"], check=True)
    print(f"Entorno listo en {destino}")


def comprobar() -> None:
    _exigir_python()
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
    os.environ.update(ENTORNO_LOCAL)
    from src.api.main import crear_app
    from src.config import cargar_observabilidad

    obs = cargar_observabilidad()
    if not (crear_app().state.orquestador._servicios.configuracion.usar_mock
            and not obs.habilitada and not obs.permitir_envio_externo
            and (RAIZ / "frontend/index.html").is_file()):
        raise ErrorLocal("Configuración o interfaz local no disponible.")
    print("Configuración local válida. MockLLM activo y trazas externas desactivadas.")


def _proteger_red(evento: str, args: tuple) -> None:
    """Impide conexiones salientes no locales desde los sockets de Python."""
    if evento in {"socket.connect", "socket.sendto", "socket.sendmsg"}:
        sock, direccion = args
        if direccion is None or sock.family not in (socket.AF_INET, socket.AF_INET6):
            return
        destino = direccion[0]
    elif evento in {
        "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr",
        "socket.gethostbyname_ex",
    }:
        destino = args[0]
        if destino is None:
            return
    else:
        return
    if destino in (b"localhost", "localhost"):
        return
    if isinstance(destino, bytes):
        destino = destino.decode("ascii", errors="replace")
    try:
        local = ipaddress.ip_address(destino).is_loopback
    except ValueError:
        local = False
    if not local:
        raise PermissionError("Egreso de red bloqueado en Veltri local")


def _bloqueo(datos: Path):
    from filelock import FileLock

    return FileLock(datos / ".veltri.lock", timeout=0)


@contextmanager
def _exclusivo(datos: Path):
    from filelock import Timeout

    datos.mkdir(parents=True, exist_ok=True)
    bloqueo = _bloqueo(datos)
    try:
        adquirido = bloqueo.acquire()
    except Timeout:
        raise ErrorLocal("El directorio de datos ya está en uso por Veltri.") from None
    with adquirido:
        yield


def _indexar(datos: Path, tenant: str):
    from src.knowledge.almacen import Almacen
    from src.knowledge.documentos import construir_documentos

    documentos = construir_documentos(tenant)
    return Almacen(datos).reemplazar(tenant, documentos)


def indexar(datos: Path, tenant: str) -> None:
    _exigir_python()
    os.environ.update(ENTORNO_LOCAL)
    sys.addaudithook(_proteger_red)
    with _exclusivo(datos):
        resultado = _indexar(datos, tenant)
    print(f"Índice local listo. Fragmentos: {resultado['fragmentos']}.")


def _escuchar(puerto: int) -> socket.socket:
    escucha = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if os.name == "nt":
            escucha.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            escucha.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        escucha.bind((HOST, puerto))
        escucha.listen()
    except OSError:
        escucha.close()
        mensaje = f"No se pudo reservar {HOST}:{puerto}. Comprueba si está ocupado."
        raise ErrorLocal(mensaje) from None
    return escucha


def proteger_http(app, puerto: int):
    """Acepta la autoridad local y el origen de la propia interfaz."""
    from starlette.responses import JSONResponse

    from src.schemas.consulta import ConsultaResponse

    autoridades = {f"{host}:{puerto}".encode() for host in (HOST, "localhost")}

    async def local(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        cabeceras = scope["headers"]
        hosts = [v.lower() for k, v in cabeceras if k == b"host"]
        origenes = [v for k, v in cabeceras if k == b"origin"]
        sitio_ajeno = any(k == b"sec-fetch-site" and v == b"cross-site" for k, v in cabeceras)
        if (len(hosts) == 1 and hosts[0] in autoridades and not sitio_ajeno
                and (not origenes or origenes == [b"http://" + hosts[0]])):
            return await app(scope, receive, send)
        error = ConsultaResponse(
            status="error", intencion="desconocida", hitl_requerido=False,
            mensaje="Acceso permitido únicamente desde la interfaz local.",
            motivos=["origen_no_permitido"],
        )
        await JSONResponse(error.model_dump(mode="json"), status_code=403)(scope, receive, send)

    return local


def iniciar(datos: Path, puerto: int, demo_legada: bool = False) -> None:
    _exigir_python()
    os.environ.update(ENTORNO_LOCAL)
    sys.addaudithook(_proteger_red)
    with _exclusivo(datos), _escuchar(puerto) as escucha:
        _servir(datos, puerto, escucha, demo_legada)


def _plataforma(datos: Path):
    from src.knowledge.almacen import Almacen
    from src.plataforma import Plataforma

    directorio = datos / "plataforma"
    directorio.mkdir(mode=0o700, parents=True, exist_ok=True)
    return Plataforma(directorio / "comercial.sqlite3", Almacen(directorio / "rag"))


def _servir(datos: Path, puerto: int, escucha: socket.socket, demo_legada: bool) -> None:
    import uvicorn

    from src.api.main import crear_app
    from src.config import Configuracion
    from src.knowledge.almacen import Almacen
    from src.knowledge.documentos import construir_documentos

    ruta_estado = datos / ".veltri.estado.json"
    temporal = datos / ".veltri.estado.tmp"
    sesion = uuid4().hex
    parada = datos / f".veltri.detener-{sesion}"
    ruta_estado.unlink(missing_ok=True)

    if demo_legada:
        almacen = Almacen(datos)
        if not almacen.contar(TENANT):
            almacen.reemplazar(TENANT, construir_documentos(TENANT))
        app = crear_app(almacen=almacen, configuracion=Configuracion(usar_mock=True))
    else:
        plataforma = _plataforma(datos)
        plataforma.sembrar()
        app = crear_app(plataforma=plataforma)

    class ServidorLocal(uvicorn.Server):
        async def startup(self, sockets=None):
            await super().startup(sockets)
            if self.started:
                temporal.write_text(json.dumps({"sesion": sesion, "puerto": puerto}),
                                    encoding="utf-8")
                temporal.replace(ruta_estado)
                print(f"Veltri disponible en http://{HOST}:{puerto}", flush=True)

        async def on_tick(self, counter):
            if parada.is_file():
                self.should_exit = True
            return await super().on_tick(counter)

    servidor = ServidorLocal(uvicorn.Config(
        proteger_http(app, puerto), host=HOST, port=puerto, loop="asyncio", workers=1,
        proxy_headers=False, access_log=False, timeout_graceful_shutdown=10,
    ))
    try:
        servidor.run(sockets=[escucha])
        if not servidor.started:
            raise ErrorLocal("El servidor local no completó el arranque.")
    finally:
        for ruta in (ruta_estado, temporal, parada):
            ruta.unlink(missing_ok=True)


def _estado(datos: Path) -> dict | None:
    from filelock import Timeout

    if not datos.is_dir():
        return None
    try:
        with _bloqueo(datos):
            return None
    except Timeout:
        try:
            estado = json.loads((datos / ".veltri.estado.json").read_text(encoding="utf-8"))
            if (re.fullmatch(r"[a-f0-9]{32}", estado["sesion"])
                    and type(estado["puerto"]) is int and 1024 <= estado["puerto"] <= 65535):
                return estado
        except (OSError, ValueError, TypeError, KeyError):
            pass
        return {}


def estado_local(datos: Path) -> None:
    estado = _estado(datos)
    if estado is None:
        print("Veltri detenido.")
    elif estado:
        print(f"Veltri en ejecución en http://{HOST}:{estado['puerto']}.")
    else:
        print("Veltri está iniciando o el índice está en mantenimiento.")


def detener(datos: Path) -> None:
    from filelock import Timeout

    estado = _estado(datos)
    if estado is None:
        print("Veltri ya está detenido.")
        return
    if not estado:
        raise ErrorLocal("El servidor aún no publicó su estado. Revisa la terminal de inicio.")
    parada = datos / f".veltri.detener-{estado['sesion']}"
    parada.touch()
    try:
        with _bloqueo(datos).acquire(timeout=15):
            parada.unlink(missing_ok=True)
    except Timeout:
        raise ErrorLocal("La parada sigue en curso. Revisa la terminal del servidor.") from None
    print("Veltri detenido.")


def _puerto(valor: str) -> int:
    puerto = int(valor)
    if not 1024 <= puerto <= 65535:
        raise argparse.ArgumentTypeError("Usa un puerto entre 1024 y 65535.")
    return puerto


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=RAIZ / "chroma_db")
    comandos = parser.add_subparsers(dest="comando", required=True)
    instalacion = comandos.add_parser("instalar")
    instalacion.add_argument("--venv", type=Path, default=RAIZ / ".venv")
    instalacion.add_argument("--desarrollo", action="store_true")
    arranque = comandos.add_parser("iniciar")
    arranque.add_argument("--puerto", type=_puerto, default=PUERTO)
    arranque.add_argument("--demo-legada", action="store_true",
                          help="Servidor aislado para fixtures históricos")
    comandos.add_parser("administrador").add_argument("--usuario", required=True)
    comandos.add_parser("indexar").add_argument("--tenant", required=True)
    comandos.add_parser("estado")
    comandos.add_parser("detener")
    comandos.add_parser("comprobar")
    args = parser.parse_args()
    datos = args.datos.resolve()
    try:
        match args.comando:
            case "instalar":
                instalar(args.venv.resolve(), args.desarrollo)
            case "iniciar":
                iniciar(datos, args.puerto, args.demo_legada)
            case "administrador":
                from getpass import getpass

                os.environ.update(ENTORNO_LOCAL)
                sys.addaudithook(_proteger_red)
                clave = getpass("Contraseña local (12 caracteres como mínimo): ")
                if clave != getpass("Repite la contraseña: "):
                    raise ErrorLocal("Las contraseñas no coinciden.")
                with _exclusivo(datos):
                    _plataforma(datos).crear_usuario(args.usuario, clave)
                print("Administrador general creado.")
            case "indexar":
                indexar(datos, args.tenant)
            case "estado":
                estado_local(datos)
            case "detener":
                detener(datos)
            case "comprobar":
                comprobar()
    except KeyboardInterrupt:
        return 0
    except ErrorLocal as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Falló la operación local ({type(error).__name__}).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
