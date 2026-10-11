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
