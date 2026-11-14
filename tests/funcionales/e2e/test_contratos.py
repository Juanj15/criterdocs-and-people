"""Pruebas de extremo a extremo de la pantalla de documentos y contratos (HU-02, CDP-44).

Hacen lo mismo que el auxiliar: buscar al colaborador, cargar los PDF, generar
el contrato y descargarlo. Cada prueba lleva el ID del caso en la matriz RTF4.
"""
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from tests.funcionales.e2e.apoyo import (ARCHIVOS, AUXILIAR, DATOS, abrir_contratos,
                                         agregar_proyecto, cambiar_estado, cargar_documentos,
                                         registrar)

pytestmark = pytest.mark.funcional


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


def test_cp32_contrato_con_valor_total_dividido(page: Page, url_aplicacion, cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva,
                               forma_pago="VALOR_TOTAL_DIVIDIDO", valor_mensual=None,
                               valor_total="18000000", numero_meses="6")
    cargar_documentos(page, url_aplicacion, id_colaborador)
    abrir_contratos(page, url_aplicacion, id_colaborador)

    page.get_by_role("button", name="Generar contrato").click()
    expect(page.locator("#mensaje")).to_contain_text("Contrato generado: PS-")
    with page.expect_download() as descarga:
        page.get_by_role("button", name="Descargar PDF").click()
    contenido = Path(descarga.value.path()).read_bytes()

    assert b"18.000.000" in contenido and b"6 cuotas" in contenido


def test_cp34_sin_ningun_documento(page: Page, url_aplicacion, colaborador):
    abrir_contratos(page, url_aplicacion, colaborador)
    expect(page.locator(".pendiente")).to_have_count(4)

    page.get_by_role("button", name="Generar contrato").click()

    mensaje = page.locator("#mensaje")
    expect(mensaje).to_have_class("error")
    expect(mensaje).to_contain_text("Faltan documentos obligatorios")
    for documento in ("Cédula", "Certificación bancaria", "RUT", "Hoja de vida"):
        expect(mensaje).to_contain_text(documento)


def test_cp35_colaborador_inactivo_no_muestra_generar(page: Page, url_aplicacion, colaborador):
    cargar_documentos(page, url_aplicacion, colaborador)
    cambiar_estado(page, url_aplicacion, colaborador, "INACTIVO")
    abrir_contratos(page, url_aplicacion, colaborador)

    aviso = page.get_by_text("Colaborador inactivo: no se pueden generar contratos.")
    expect(aviso).to_be_visible()
    expect(page.get_by_role("button", name="Generar contrato")).to_have_count(0)
    expect(page.locator("#vinculaciones")).to_contain_text("Sin contrato")


def test_cp36_un_solo_contrato_por_proyecto(page: Page, url_aplicacion, colaborador):
    cargar_documentos(page, url_aplicacion, colaborador)
    abrir_contratos(page, url_aplicacion, colaborador)

    page.get_by_role("button", name="Generar contrato").click()
    expect(page.locator("#mensaje")).to_contain_text("Contrato generado: PS-")

    expect(page.get_by_role("button", name="Generar contrato")).to_have_count(0)
    expect(page.locator("#vinculaciones")).to_contain_text("Contrato PS-")
    expect(page.get_by_role("button", name="Descargar PDF")).to_have_count(1)


def test_cp37_contrato_del_segundo_proyecto(page: Page, url_aplicacion, colaborador):
    agregar_proyecto(page, url_aplicacion, colaborador, proyecto="Conecta Futuro",
                     cargo="Docente", fecha_inicio="2026-12-01", fecha_fin="2027-05-31",
                     forma_pago="HONORARIO_MENSUAL", valor_mensual="2500000")
    cargar_documentos(page, url_aplicacion, colaborador)
    abrir_contratos(page, url_aplicacion, colaborador)

    page.get_by_role("button", name="Generar contrato").first.click()
    expect(page.get_by_role("button", name="Descargar PDF")).to_have_count(1)
    page.get_by_role("button", name="Generar contrato").click()

    expect(page.get_by_role("button", name="Descargar PDF")).to_have_count(2)
    expect(page.locator("#historial")).to_contain_text("Soy Digital")
    expect(page.locator("#historial")).to_contain_text("Conecta Futuro")


@pytest.mark.perfil("DIRECCION")
def test_cp38_la_direccion_no_ve_cargar_ni_generar(page: Page, url_aplicacion, colaborador):
    """Seguridad: la dirección consulta y descarga, pero no carga ni genera."""
    cargar_documentos(page, url_aplicacion, colaborador)
    page.request.post(f"{url_aplicacion}/colaboradores/{colaborador}/vinculaciones/"
                      f"{_primera_vinculacion(page, url_aplicacion, colaborador)}/contrato",
                      headers=AUXILIAR)
    abrir_contratos(page, url_aplicacion, colaborador)

    expect(page.get_by_role("button", name="Generar contrato")).to_have_count(0)
    expect(page.get_by_role("button", name="Cargar", exact=True)).to_have_count(0)
    expect(page.get_by_role("columnheader", name="Cargar PDF")).to_have_count(0)
    expect(page.get_by_role("button", name="Descargar PDF")).to_be_visible()


def test_cp56_el_contrato_se_genera_en_menos_de_3_segundos(page: Page, url_aplicacion,
                                                          colaborador):
    """Rendimiento (RNF-01): desde el clic hasta ver el mensaje."""
    cargar_documentos(page, url_aplicacion, colaborador)
    abrir_contratos(page, url_aplicacion, colaborador)

    inicio = time.perf_counter()
    page.get_by_role("button", name="Generar contrato").click()
    expect(page.locator("#mensaje")).to_contain_text("Contrato generado: PS-")

    assert time.perf_counter() - inicio < 3


def _primera_vinculacion(pagina: Page, url, id_colaborador):
    ficha = pagina.request.get(f"{url}/colaboradores/{id_colaborador}", headers=AUXILIAR)
    return ficha.json()["colaborador"]["vinculaciones"][0]["id_vinculacion"]
