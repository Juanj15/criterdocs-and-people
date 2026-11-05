"""Pruebas de los endpoints que faltaban para probar HU-01 desde afuera (CDP-43).

Al diseñar las pruebas de caja negra (RTF4) noté que el criterio "permitir
activar o desactivar colaboradores" no se podía comprobar por la API, y que
tampoco había forma de consultar lo que quedó guardado.
"""
from fastapi.testclient import TestClient

from app.api.main import app

cliente = TestClient(app)
ADMIN = {"X-Rol": "ADMINISTRATIVO"}
DIRECCION = {"X-Rol": "DIRECCION"}

DATOS = {
    "nombre_completo": "Marta Salazar",
    "correo": "marta.salazar@correo.com",
    "banco": "Bancolombia",
    "numero_cuenta": "12345678901",
    "proyecto": "Conecta Futuro",
    "cargo": "Coordinadora",
    "fecha_inicio": "2026-11-01",
    "fecha_fin": "2027-04-30",
    "forma_pago": "HONORARIO_MENSUAL",
    "valor_mensual": "4200000",
}


def _registrar(cedula):
    datos = dict(DATOS, numero_documento=cedula)
    return cliente.post("/colaboradores", json=datos, headers=ADMIN).json()["id_colaborador"]


def test_consultar_colaborador_por_api():
    id_colaborador = _registrar("55001001")

    respuesta = cliente.get(f"/colaboradores/{id_colaborador}", headers=ADMIN)
    ficha = respuesta.json()["colaborador"]

    assert respuesta.status_code == 200
    assert ficha["nombre_completo"] == "Marta Salazar"
    assert ficha["estado"] == "ACTIVO"
    assert ficha["vinculaciones"][0]["proyecto"] == "Conecta Futuro"


def test_la_consulta_no_muestra_la_cuenta_completa():
    id_colaborador = _registrar("55001002")

    ficha = cliente.get(f"/colaboradores/{id_colaborador}", headers=DIRECCION).json()["colaborador"]

    assert ficha["numero_cuenta"] == "*******8901"


def test_consultar_sin_encabezado_de_rol_devuelve_403():
    id_colaborador = _registrar("55001003")

    respuesta = cliente.get(f"/colaboradores/{id_colaborador}")

    assert respuesta.status_code == 403


def test_consultar_inexistente_devuelve_404():
    respuesta = cliente.get("/colaboradores/99999", headers=ADMIN)

    assert respuesta.status_code == 404


def test_desactivar_y_reactivar_por_api():
    id_colaborador = _registrar("55001004")

    desactivar = cliente.patch(f"/colaboradores/{id_colaborador}/estado",
                               json={"estado": "INACTIVO"}, headers=ADMIN)
    consulta = cliente.get(f"/colaboradores/{id_colaborador}", headers=ADMIN).json()
    reactivar = cliente.patch(f"/colaboradores/{id_colaborador}/estado",
                              json={"estado": "ACTIVO"}, headers=ADMIN)

    assert desactivar.status_code == 200
    assert desactivar.json()["codigo"] == "ESTADO_ACTUALIZADO"
    assert consulta["colaborador"]["estado"] == "INACTIVO"
    assert reactivar.status_code == 200


def test_colaborador_inactivo_no_recibe_proyectos_por_api():
    id_colaborador = _registrar("55001005")
    cliente.patch(f"/colaboradores/{id_colaborador}/estado",
                  json={"estado": "INACTIVO"}, headers=ADMIN)

    respuesta = cliente.post(f"/colaboradores/{id_colaborador}/vinculaciones", json={
        "proyecto": "Soy Digital", "cargo": "Analista", "fecha_inicio": "2026-12-01",
        "fecha_fin": "2027-05-31", "forma_pago": "HONORARIO_MENSUAL",
        "valor_mensual": "3000000"}, headers=ADMIN)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "COLABORADOR_INACTIVO"


def test_cambiar_al_mismo_estado_devuelve_409():
    id_colaborador = _registrar("55001006")

    respuesta = cliente.patch(f"/colaboradores/{id_colaborador}/estado",
                              json={"estado": "ACTIVO"}, headers=ADMIN)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "ESTADO_SIN_CAMBIO"


def test_cambiar_estado_sin_enviar_estado_devuelve_422():
    id_colaborador = _registrar("55001007")

    respuesta = cliente.patch(f"/colaboradores/{id_colaborador}/estado", json={}, headers=ADMIN)

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == ["estado"]


def test_direccion_no_puede_cambiar_el_estado():
    id_colaborador = _registrar("55001008")

    respuesta = cliente.patch(f"/colaboradores/{id_colaborador}/estado",
                              json={"estado": "INACTIVO"}, headers=DIRECCION)

    assert respuesta.status_code == 403
