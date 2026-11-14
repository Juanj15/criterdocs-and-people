"""Pruebas de extremo a extremo de la ficha del colaborador (HU-01, CDP-46).

Cubren consultar, editar, agregar proyecto y activar o desactivar desde la
pantalla, con el perfil que tendría el usuario (CDP-47). Cada prueba lleva el
ID del caso en la matriz de la RTF4.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.funcionales.e2e.apoyo import abrir_ficha, agregar_proyecto, cambiar_estado, registrar

pytestmark = pytest.mark.funcional

SOY_DIGITAL = {"proyecto": "Soy Digital", "cargo": "Formadora",
               "fecha_inicio": "2026-12-01", "fecha_fin": "2027-05-31",
               "forma_pago": "HONORARIO_MENSUAL", "valor_mensual": "2500000"}


def _campo(pagina: Page, nombre: str):
    return pagina.locator(f'#datos [name="{nombre}"]')


def _guardar(pagina: Page):
    pagina.get_by_role("button", name="Guardar cambios").click()


def _llenar_proyecto(pagina: Page, **datos):
    formulario = pagina.locator("#nuevo_proyecto")
    for campo, valor in datos.items():
        if campo == "forma_pago":
            formulario.locator("#forma_pago").select_option(valor)
        else:
            formulario.locator(f'[name="{campo}"]').fill(valor)
    formulario.get_by_role("button", name="Agregar proyecto").click()


def test_cp15_consultar_muestra_los_datos_registrados(page: Page, url_aplicacion,
                                                     cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    expect(_campo(page, "nombre_completo")).to_have_value("Laura Gómez")
    expect(_campo(page, "numero_documento")).to_have_value(cedula_nueva)
    expect(_campo(page, "banco")).to_have_value("Bancolombia")
    expect(_campo(page, "numero_cuenta")).to_have_attribute("placeholder", "Actual: *******8901")
    expect(page.locator("#estado")).to_have_text("ACTIVO")
    expect(page.locator("#vinculaciones")).to_contain_text("Conecta Futuro")
    expect(page.locator("#vinculaciones")).to_contain_text("2026-11-01 a 2027-04-30")


@pytest.mark.perfil("")
def test_cp16_sin_perfil_no_se_puede_consultar(page: Page, url_aplicacion):
    page.goto(f"{url_aplicacion}/ficha")

    expect(page.get_by_text("Seleccione su perfil en la parte superior")).to_be_visible()
    expect(page.get_by_role("button", name="Buscar")).to_be_hidden()
    expect(page.locator("#perfil")).to_have_value("")


def test_cp17_editar_el_banco_y_verlo_como_direccion(page: Page, url_aplicacion,
                                                    cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    _campo(page, "banco").fill("Nequi")
    _guardar(page)
    expect(page.locator("#mensaje")).to_have_text("Colaborador actualizado.")
    expect(page.locator("#mensaje")).to_have_class("ok")

    page.select_option("#perfil", "DIRECCION")
    expect(_campo(page, "banco")).to_have_value("Nequi")
    expect(_campo(page, "banco")).not_to_be_editable()


def test_cp18_no_se_puede_dejar_el_nombre_vacio(page: Page, url_aplicacion, cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    _campo(page, "nombre_completo").fill("")
    _guardar(page)

    expect(page.locator("#mensaje")).to_have_class("error")
    expect(page.locator("#mensaje")).to_contain_text(
        "No se pueden dejar campos obligatorios vacíos")
    expect(_campo(page, "nombre_completo")).to_have_class("error")


def test_cp19_la_cedula_de_otro_colaborador(page: Page, url_aplicacion, cedula_nueva):
    otra = "31" + cedula_nueva[2:]
    registrar(page, url_aplicacion, otra, nombre_completo="Andrés Ruiz")
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    _campo(page, "numero_documento").fill(otra)
    _guardar(page)

    expect(page.locator("#mensaje")).to_have_text("Esa cédula ya pertenece a otro colaborador")


def test_cp20_buscar_un_colaborador_que_no_existe(page: Page, url_aplicacion):
    page.goto(f"{url_aplicacion}/ficha")
    page.fill("#id_colaborador", "99999")
    page.get_by_role("button", name="Buscar").click()

    expect(page.locator("#mensaje")).to_have_text("El colaborador no existe")
    expect(page.locator("#mensaje")).to_have_class("error")
    expect(page.locator("#detalle")).to_be_hidden()


def test_cp21_agregar_un_segundo_proyecto(page: Page, url_aplicacion, cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    _llenar_proyecto(page, **SOY_DIGITAL)

    expect(page.locator("#mensaje")).to_have_text("Proyecto agregado.")
    expect(page.locator("#vinculaciones tr")).to_have_count(2)
    expect(page.locator("#vinculaciones")).to_contain_text("2026-12-01 a 2027-05-31")


def test_cp22_proyecto_repetido_en_fechas_que_se_cruzan(page: Page, url_aplicacion,
                                                       cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    agregar_proyecto(page, url_aplicacion, id_colaborador, **SOY_DIGITAL)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    cruzado = {**SOY_DIGITAL, "fecha_inicio": "2027-01-01", "fecha_fin": "2027-02-28"}
    _llenar_proyecto(page, **cruzado)

    expect(page.locator("#mensaje")).to_have_text("Ya tiene ese proyecto en fechas que se cruzan")
    expect(page.locator("#vinculaciones tr")).to_have_count(2)


def test_cp23_desactivar(page: Page, url_aplicacion, cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    page.get_by_role("button", name="Desactivar").click()

    expect(page.locator("#mensaje")).to_have_text(
        "Estado actualizado: el colaborador quedó INACTIVO.")
    expect(page.locator("#estado")).to_have_text("INACTIVO")


def test_cp24_cp25_inactivo_no_permite_proyecto_ni_desactivar_otra_vez(
        page: Page, url_aplicacion, cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    cambiar_estado(page, url_aplicacion, id_colaborador, "INACTIVO")
    abrir_ficha(page, url_aplicacion, id_colaborador)

    expect(page.get_by_text("No se pueden agregar proyectos a un colaborador inactivo. "
                            "Reactívelo primero.")).to_be_visible()
    expect(page.locator("#campos_proyecto")).to_be_hidden()          # CP-24
    expect(page.get_by_role("button", name="Desactivar")).to_be_hidden()   # CP-25
    expect(page.get_by_role("button", name="Reactivar")).to_be_visible()


def test_cp26_reactivar(page: Page, url_aplicacion, cedula_nueva):
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    cambiar_estado(page, url_aplicacion, id_colaborador, "INACTIVO")
    abrir_ficha(page, url_aplicacion, id_colaborador)

    page.get_by_role("button", name="Reactivar").click()

    expect(page.locator("#mensaje")).to_have_text(
        "Estado actualizado: el colaborador quedó ACTIVO.")
    expect(page.locator("#estado")).to_have_text("ACTIVO")
    expect(page.locator("#campos_proyecto")).to_be_visible()


@pytest.mark.perfil("DIRECCION")
def test_cp27_la_direccion_solo_consulta(page: Page, url_aplicacion, cedula_nueva):
    """Seguridad: a la dirección no se le muestran los botones que no puede usar."""
    id_colaborador = registrar(page, url_aplicacion, cedula_nueva)
    abrir_ficha(page, url_aplicacion, id_colaborador)

    expect(_campo(page, "nombre_completo")).to_have_value("Laura Gómez")
    for boton in ("Guardar cambios", "Desactivar", "Reactivar", "Agregar proyecto"):
        expect(page.get_by_role("button", name=boton)).to_have_count(0)
    expect(page.locator("#nuevo_proyecto")).to_be_hidden()
    expect(_campo(page, "nombre_completo")).not_to_be_editable()
