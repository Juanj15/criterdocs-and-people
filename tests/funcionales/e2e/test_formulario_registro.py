"""Pruebas de extremo a extremo del formulario de registro (HU-01, CDP-42).

Son de caja negra: no miran el código, solo hacen lo que haría el auxiliar
administrativo en el navegador (llenar, enviar) y revisan lo que ve en pantalla.
Cada prueba lleva el ID del caso en la matriz de la RTF4.
"""
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.funcional

CAMPOS_TEXTO = {
    "nombre_completo": "Laura Gómez",
    "correo": "laura.gomez@correo.com",
    "banco": "Bancolombia",
    "numero_cuenta": "12345678901",
    "proyecto": "Conecta Futuro",
    "cargo": "Docente",
    "fecha_inicio": "2026-11-01",
    "fecha_fin": "2027-04-30",
    "valor_mensual": "3000000",
}


def _llenar(pagina: Page, cedula: str, **cambios):
    """Llena el formulario como lo haría el auxiliar; un valor vacío deja el campo en blanco."""
    datos = dict(CAMPOS_TEXTO, numero_documento=cedula, **cambios)
    for campo, valor in datos.items():
        pagina.locator(f'[name="{campo}"]').fill(valor)
    pagina.select_option("#forma_pago", "HONORARIO_MENSUAL")


def _enviar(pagina: Page):
    pagina.get_by_role("button", name="Registrar colaborador").click()


def test_cp01_registro_exitoso_desde_el_formulario(page: Page, url_aplicacion, cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva)
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_class("ok")
    patron = re.compile(r"Colaborador registrado \(id \d+\)\.")
    expect(page.locator("#mensaje")).to_have_text(patron)
    expect(page.locator('[name="nombre_completo"]')).to_have_value("")  # el formulario se limpia


def test_cp03_formulario_vacio_marca_todos_los_campos(page: Page, url_aplicacion):
    page.goto(url_aplicacion)
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_class("error")
    expect(page.locator("#mensaje")).to_contain_text("Faltan campos obligatorios")
    expect(page.locator("input.error, select.error")).to_have_count(10)


def test_cp04_solo_falta_el_banco(page: Page, url_aplicacion, cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva, banco="")
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_text("Faltan campos obligatorios: banco")
    expect(page.locator('[name="banco"]')).to_have_class("error")
    expect(page.locator("input.error, select.error")).to_have_count(1)


def test_cp06_fecha_fin_igual_a_la_de_inicio(page: Page, url_aplicacion, cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva, fecha_fin="2026-11-01")
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_text(
        "La fecha fin debe ser posterior a la fecha inicio")


def test_cp12_cedula_repetida(page: Page, url_aplicacion, cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva)
    _enviar(page)
    expect(page.locator("#mensaje")).to_have_class("ok")

    _llenar(page, cedula_nueva, nombre_completo="Otra persona", correo="otra@correo.com")
    _enviar(page)

    expect(page.locator("#mensaje")).to_contain_text("El colaborador ya existe")


def test_cp28_valor_total_muestra_sus_campos(page: Page, url_aplicacion):
    """Usabilidad: al cambiar la forma de pago, el formulario pide los datos que corresponden."""
    page.goto(url_aplicacion)
    page.select_option("#forma_pago", "VALOR_TOTAL_DIVIDIDO")

    expect(page.locator('[name="valor_total"]')).to_be_visible()
    expect(page.locator('[name="numero_meses"]')).to_be_visible()
    expect(page.locator('[name="valor_mensual"]')).to_be_hidden()


@pytest.mark.xfail(strict=True, reason="Hallazgo abierto (CDP-43): el correo no valida su formato")
def test_cp14_correo_sin_arroba_es_rechazado(page: Page, url_aplicacion, cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva, correo="laura.gomez")
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_class("error", timeout=2000)
