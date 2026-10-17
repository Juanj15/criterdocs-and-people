"""Prueba de integración ligera del endpoint de HU-01."""
from fastapi.testclient import TestClient

from app.api.main import app

cliente = TestClient(app)

DATOS = {
    "nombre_completo": "Carlos Ruiz",
    "numero_documento": "98765432",
    "correo": "carlos.ruiz@correo.com",
    "banco": "Davivienda",
    "numero_cuenta": "4500123",
    "proyecto": "Conecta Futuro",
    "cargo": "Docente",
    "fecha_inicio": "2026-10-16",
    "fecha_fin": "2027-03-31",
    "forma_pago": "HONORARIO_MENSUAL",
    "valor_mensual": "3000000",
}


def test_registro_por_api_devuelve_201():
    respuesta = cliente.post("/colaboradores", json=DATOS, headers={"X-Rol": "ADMINISTRATIVO"})

    assert respuesta.status_code == 201
    assert respuesta.json()["codigo"] == "COLABORADOR_REGISTRADO"


def test_registro_por_api_sin_rol_devuelve_403():
    respuesta = cliente.post("/colaboradores", json=DATOS, headers={"X-Rol": "DIRECCION"})

    assert respuesta.status_code == 403


def test_registro_por_api_con_campos_vacios_devuelve_422():
    respuesta = cliente.post("/colaboradores", json={"nombre_completo": "Ana"},
                             headers={"X-Rol": "ADMINISTRATIVO"})

    assert respuesta.status_code == 422
    assert "correo" in respuesta.json()["detalle"]


def test_editar_y_agregar_proyecto_por_api():
    datos = dict(DATOS, numero_documento="11223344", correo="ana@correo.com")
    id_colaborador = cliente.post("/colaboradores", json=datos,
                                  headers={"X-Rol": "ADMINISTRATIVO"}).json()["id_colaborador"]

    edicion = cliente.patch(f"/colaboradores/{id_colaborador}", json={"banco": "Nequi"},
                            headers={"X-Rol": "ADMINISTRATIVO"})
    proyecto = cliente.post(f"/colaboradores/{id_colaborador}/vinculaciones", json={
        "proyecto": "Soy Digital", "cargo": "Analista", "fecha_inicio": "2026-11-01",
        "fecha_fin": "2027-04-30", "forma_pago": "VALOR_TOTAL_DIVIDIDO",
        "valor_total": "18000000", "numero_meses": 6}, headers={"X-Rol": "ADMINISTRATIVO"})

    assert edicion.status_code == 200
    assert proyecto.status_code == 201


def test_editar_colaborador_inexistente_por_api_devuelve_404():
    respuesta = cliente.patch("/colaboradores/9999", json={"banco": "Nequi"},
                              headers={"X-Rol": "ADMINISTRATIVO"})

    assert respuesta.status_code == 404


def test_formulario_de_registro_se_muestra():
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    assert '<form id="formulario"' in respuesta.text
    assert 'name="numero_documento"' in respuesta.text
