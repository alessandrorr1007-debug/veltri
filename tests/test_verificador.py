"""El verificador detecta errores estructurales sin ejecutar código de negocio."""

from pathlib import Path

import pytest

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
        "AGENTS.md",
        "docs/arquitectura.md",
        "docs/agentes/deep-agents-semana11.md",
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


@pytest.mark.parametrize("trazabilidad_ejecutada", [True, False])
def test_pytest_rechaza_resultado_omitido(monkeypatch, trazabilidad_ejecutada):
    from scripts import verificar

    def pytest_simulado(nombre, comando):
        informe = Path(comando[-1])
        traza = (
            '<testcase classname="tests.test_trazabilidad_sdd" '
            'name="test_matriz_cubre_requisitos_componentes_y_pruebas"/>'
            if trazabilidad_ejecutada else ""
        )
        omision = '<skipped/>' if trazabilidad_ejecutada else ""
        informe.write_text(
            f'<testsuites><testsuite>{traza}<testcase name="criterio">{omision}</testcase>'
            '</testsuite></testsuites>',
            encoding="utf-8",
        )
        return nombre, "OK"

    monkeypatch.setattr(verificar, "_ejecutar", pytest_simulado)
    assert verificar._ejecutar_pytest("python") == ("pytest", "FALLA")
