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


def _valor_total(pagina: Page, total: str, meses: str):
    """Cambia la forma de pago a valor total dividido y llena sus campos."""
    pagina.select_option("#forma_pago", "VALOR_TOTAL_DIVIDIDO")
    pagina.fill('[name="valor_total"]', total)
    pagina.fill('[name="numero_meses"]', meses)


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

    expect(page.locator("#mensaje")).to_have_text("Faltan campos obligatorios: Banco")
    expect(page.locator('[name="banco"]')).to_have_class("error")
    expect(page.locator("input.error, select.error")).to_have_count(1)


def test_cp02_registro_con_valor_total_dividido(page: Page, url_aplicacion, cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva)
    _valor_total(page, "18000000", "6")
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_class("ok")
    expect(page.locator("#mensaje")).to_contain_text("Colaborador registrado")


def test_cp05_nombre_con_solo_espacios_cuenta_como_vacio(page: Page, url_aplicacion,
                                                        cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva, nombre_completo="   ")
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_text("Faltan campos obligatorios: Nombre completo")
    expect(page.locator('[name="nombre_completo"]')).to_have_class("error")


@pytest.mark.parametrize("caso, cambios, esperado", [
    ("CP-07", {"fecha_fin": "2026-11-02"}, None),
    ("CP-08", {"valor_mensual": "0"}, "El valor no es válido para la forma de pago"),
    ("CP-09", {"valor_mensual": "-1"}, "El valor no es válido para la forma de pago"),
    ("CP-10", {"valor_mensual": "1"}, None),
])
def test_cp07_a_cp10_limites_de_fecha_y_valor(page: Page, url_aplicacion, cedula_nueva,
                                             caso, cambios, esperado):
    """Valores límite: justo afuera se rechaza, justo adentro se registra."""
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva, **cambios)
    _enviar(page)

    if esperado is None:
        expect(page.locator("#mensaje"), caso).to_have_class("ok")
    else:
        expect(page.locator("#mensaje"), caso).to_have_class("error")
        expect(page.locator("#mensaje"), caso).to_contain_text(esperado)


def test_cp11_valor_total_con_cero_meses(page: Page, url_aplicacion, cedula_nueva):
    page.goto(url_aplicacion)
    _llenar(page, cedula_nueva)
    _valor_total(page, "18000000", "0")
    _enviar(page)

    expect(page.locator("#mensaje")).to_have_class("error")
    expect(page.locator("#mensaje")).to_contain_text("El valor no es válido para la forma de pago")


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


@pytest.mark.perfil("DIRECCION")
def test_cp13_la_direccion_no_ve_el_formulario_de_registro(page: Page, url_aplicacion):
    """Seguridad: la pantalla no le muestra a la dirección lo que no puede hacer."""
    page.goto(url_aplicacion)

    expect(page.locator("#formulario")).to_be_hidden()
    expect(page.get_by_role("button", name="Registrar colaborador")).to_have_count(0)
    expect(page.get_by_role("link", name="Registrar colaborador")).to_be_hidden()
    expect(page.get_by_text("Su perfil (Dirección) puede consultar colaboradores")).to_be_visible()


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
