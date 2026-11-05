"""Pruebas de los endpoints de contrato, historial y descarga de la HU-02 (CDP-27, CDP-28)."""
from tests.test_api_documentos import (ADMIN, DIRECCION, TIPOS, cargar_documento, cliente,
                                         registrar_con_proyecto)


def test_generar_contrato_con_documentos_faltantes_devuelve_422():
    id_colaborador, id_vinculacion = registrar_con_proyecto("62000005")
    cargar_documento(id_colaborador, "CEDULA")

    respuesta = cliente.post(
        f"/colaboradores/{id_colaborador}/vinculaciones/{id_vinculacion}/contrato", headers=ADMIN)

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == ["Certificación bancaria", "RUT",
                                           "Hoja de vida con soportes"]


def test_generar_historial_y_descargar_el_contrato():
    id_colaborador, id_vinculacion = registrar_con_proyecto("62000006")
    for tipo in TIPOS:
        cargar_documento(id_colaborador, tipo)

    generado = cliente.post(
        f"/colaboradores/{id_colaborador}/vinculaciones/{id_vinculacion}/contrato", headers=ADMIN)
    repetido = cliente.post(
        f"/colaboradores/{id_colaborador}/vinculaciones/{id_vinculacion}/contrato", headers=ADMIN)
    historial = cliente.get(f"/colaboradores/{id_colaborador}/contratos", headers=DIRECCION)
    id_contrato = generado.json()["contrato"]["id_contrato"]
    descarga = cliente.get(f"/contratos/{id_contrato}/pdf", headers=ADMIN)

    assert generado.status_code == 201
    assert repetido.status_code == 409
    assert len(historial.json()["contratos"]) == 1
    assert descarga.headers["content-type"] == "application/pdf"
    assert descarga.content.startswith(b"%PDF")


def test_descargar_contrato_inexistente_devuelve_404():
    respuesta = cliente.get("/contratos/99999/pdf", headers=ADMIN)

    assert respuesta.status_code == 404


def test_la_pantalla_de_contratos_se_muestra():
    respuesta = cliente.get("/contratos")

    assert respuesta.status_code == 200
    assert 'id="buscar"' in respuesta.text
