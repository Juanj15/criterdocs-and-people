"""Pruebas de extremo a extremo de la pantalla de documentos y contratos (HU-02, CDP-44).

Hacen lo mismo que el auxiliar: buscar al colaborador, cargar los PDF, generar
el contrato y descargarlo. Cada prueba lleva el ID del caso en la matriz RTF4.
"""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.funcional

DATOS = Path(__file__).resolve().parent.parent / "datos"
ARCHIVOS = {
    "CEDULA": "cedula.pdf",
    "CERTIFICACION_BANCARIA": "certificacion_bancaria.pdf",
    "RUT": "rut.pdf",
    "HOJA_DE_VIDA": "hoja_de_vida.pdf",
}


@pytest.fixture
def colaborador(page: Page, url_aplicacion, cedula_nueva):
    """Registra a una colaboradora por la API y devuelve su id."""
    respuesta = page.request.post(f"{url_aplicacion}/colaboradores", headers={
        "X-Rol": "ADMINISTRATIVO"}, data={
        "nombre_completo": "Laura Gómez", "numero_documento": cedula_nueva,
        "correo": "laura.gomez@correo.com", "banco": "Bancolombia",
        "numero_cuenta": "12345678901", "proyecto": "Soy Digital", "cargo": "Formadora",
        "fecha_inicio": "2026-11-01", "fecha_fin": "2027-04-30",
        "forma_pago": "HONORARIO_MENSUAL", "valor_mensual": "3000000"})
    return respuesta.json()["id_colaborador"]


def _buscar(pagina: Page, url, id_colaborador):
    pagina.goto(f"{url}/contratos")
    pagina.fill("#id_colaborador", str(id_colaborador))
    pagina.get_by_role("button", name="Buscar").click()
    expect(pagina.locator("#detalle")).to_be_visible()


def _cargar(pagina: Page, tipo, archivo):
    """Carga un archivo y espera la respuesta, como el auxiliar que mira el mensaje."""
    fila = pagina.locator(f'tr[data-tipo="{tipo}"]')
    fila.locator('input[type="file"]').set_input_files(DATOS / archivo)
    with pagina.expect_response(lambda r: "/documentos" in r.url and r.request.method == "POST"):
        fila.get_by_role("button", name="Cargar").click()


def test_cp29_cargar_los_cuatro_documentos(page: Page, url_aplicacion, colaborador):
    _buscar(page, url_aplicacion, colaborador)
    expect(page.locator("#resumen")).to_contain_text("Faltan")

    for tipo, archivo in ARCHIVOS.items():
        _cargar(page, tipo, archivo)
        expect(page.locator(f'tr[data-tipo="{tipo}"] .cargado')).to_contain_text(archivo)

    expect(page.locator("#resumen")).to_have_text("Documentos completos")


def test_cp30_un_word_no_se_acepta(page: Page, url_aplicacion, colaborador):
    _buscar(page, url_aplicacion, colaborador)
    _cargar(page, "RUT", "rut.docx")

    expect(page.locator("#mensaje")).to_have_text("Solo se permiten archivos PDF: RUT")
    expect(page.locator('tr[data-tipo="RUT"] .pendiente')).to_be_visible()


def test_cp33_sin_rut_no_hay_contrato(page: Page, url_aplicacion, colaborador):
    _buscar(page, url_aplicacion, colaborador)
    for tipo, archivo in ARCHIVOS.items():
        if tipo != "RUT":
            _cargar(page, tipo, archivo)
    expect(page.locator("#resumen")).to_have_text("Faltan: RUT")

    page.get_by_role("button", name="Generar contrato").click()

    expect(page.locator("#mensaje")).to_have_text("Faltan documentos obligatorios: RUT")
    expect(page.locator("#historial")).to_contain_text("Todavía no hay contratos")


def test_cp31_generar_y_descargar_el_contrato(page: Page, url_aplicacion, colaborador,
                                             cedula_nueva):
    _buscar(page, url_aplicacion, colaborador)
    for tipo, archivo in ARCHIVOS.items():
        _cargar(page, tipo, archivo)
    expect(page.locator("#resumen")).to_have_text("Documentos completos")

    page.get_by_role("button", name="Generar contrato").click()
    expect(page.locator("#mensaje")).to_contain_text("Contrato generado: PS-")

    with page.expect_download() as descarga:
        page.get_by_role("button", name="Descargar PDF").click()
    contenido = Path(descarga.value.path()).read_bytes()

    assert descarga.value.suggested_filename.endswith(".pdf")
    assert contenido.startswith(b"%PDF")
    assert cedula_nueva.encode() in contenido and b"Soy Digital" in contenido


def test_cp57_un_proyecto_con_html_se_muestra_como_texto(page: Page, url_aplicacion,
                                                        cedula_nueva):
    """Seguridad: lo que escribe el usuario no se ejecuta en la pantalla (XSS)."""
    proyecto = '<img src=x onerror="window.atacado=1">Proyecto X'
    respuesta = page.request.post(f"{url_aplicacion}/colaboradores", headers={
        "X-Rol": "ADMINISTRATIVO"}, data={
        "nombre_completo": "Prueba Seguridad", "numero_documento": cedula_nueva,
        "correo": "seguridad@correo.com", "banco": "Bancolombia",
        "numero_cuenta": "12345678901", "proyecto": proyecto, "cargo": "<b>Docente</b>",
        "fecha_inicio": "2026-11-01", "fecha_fin": "2027-04-30",
        "forma_pago": "HONORARIO_MENSUAL", "valor_mensual": "3000000"})

    _buscar(page, url_aplicacion, respuesta.json()["id_colaborador"])

    expect(page.locator("#vinculaciones")).to_contain_text(proyecto)
    expect(page.locator("#vinculaciones img, #vinculaciones b")).to_have_count(0)
    assert page.evaluate("window.atacado") is None
