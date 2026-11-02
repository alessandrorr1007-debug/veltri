"""El verificador detecta errores estructurales sin ejecutar código de negocio."""

from pathlib import Path

from scripts.verificar import comprobar_estructura


def copiar_referencias(raiz: Path) -> None:
    """Fixture mínimo: referencias documentales no se ejecutan."""
    for nombre in (
        "frontend/index.html",
        "data/catalogo.json",
        "data/compatibilidad.json",
        "data/politicas.md",
        "docs/bpmn_as_is.bpmn",
        "docs/bpmn_to_be.bpmn",
        "docs/entrega-semana10/generar_informe.py",
        "docs/entrega-semana10/Veltri_Semana10_Informe_Academico.docx",
        "docs/evidencias/semana10-fase43/ejecucion-unica.json",
    ):
        ruta = raiz / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text("", encoding="utf-8")


def test_import_eliminado_detectado_sin_ejecutar(tmp_path):
    copiar_referencias(tmp_path)
    archivo = tmp_path / "src/ejemplo.py"
    archivo.parent.mkdir()
    archivo.write_text("from src.modulo_retirado import funcion\nraise RuntimeError()\n")
    assert comprobar_estructura(tmp_path) == 1


def test_sintaxis_invalida_detectada(tmp_path):
    copiar_referencias(tmp_path)
    archivo = tmp_path / "src/ejemplo.py"
    archivo.parent.mkdir()
    archivo.write_text("def rota(:\n")
    assert comprobar_estructura(tmp_path) == 1


def test_estructura_valida_no_importa_modulos(tmp_path):
    copiar_referencias(tmp_path)
    archivo = tmp_path / "src/ejemplo.py"
    archivo.parent.mkdir()
    archivo.write_text("raise RuntimeError('No debe ejecutarse')\n")
    assert comprobar_estructura(tmp_path) == 0


def test_referencia_critica_ausente(tmp_path):
    assert comprobar_estructura(tmp_path) == 1
