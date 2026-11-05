"""Pruebas de los endpoints de documentos de soporte de la HU-02 (CDP-25)."""
from fastapi.testclient import TestClient

from app.api.main import app

cliente = TestClient(app)
ADMIN = {"X-Rol": "ADMINISTRATIVO"}
DIRECCION = {"X-Rol": "DIRECCION"}
PDF = b"%PDF-1.4 soporte de prueba"
TIPOS = ("CEDULA", "CERTIFICACION_BANCARIA", "RUT", "HOJA_DE_VIDA")


def registrar_con_proyecto(cedula):
    """Registra a Sofía y devuelve (id_colaborador, id_vinculacion); también lo usa
    test_api_contratos."""
    datos = {
        "nombre_completo": "Sofía Ramírez", "numero_documento": cedula,
        "correo": "sofia@correo.com", "banco": "Davivienda", "numero_cuenta": "4500998877",
        "proyecto": "Soy Digital", "cargo": "Formadora", "fecha_inicio": "2026-11-01",
        "fecha_fin": "2027-04-30", "forma_pago": "HONORARIO_MENSUAL", "valor_mensual": "2800000",
    }
    respuesta = cliente.post("/colaboradores", json=datos, headers=ADMIN)
    id_colaborador = respuesta.json()["id_colaborador"]
    ficha = cliente.get(f"/colaboradores/{id_colaborador}", headers=ADMIN).json()["colaborador"]
    return id_colaborador, ficha["vinculaciones"][0]["id_vinculacion"]


def cargar_documento(id_colaborador, tipo, nombre="soporte.pdf", contenido=PDF):
    """Carga un archivo por el endpoint de documentos."""
    return cliente.post(f"/colaboradores/{id_colaborador}/documentos", data={"tipo": tipo},
                        files={"archivo": (nombre, contenido, "application/pdf")}, headers=ADMIN)


def test_cargar_documentos_hasta_completarlos():
    id_colaborador, _ = registrar_con_proyecto("62000011")

    primera = cargar_documento(id_colaborador, "CEDULA")
    for tipo in TIPOS[1:]:
        ultima = cargar_documento(id_colaborador, tipo)

    assert primera.status_code == 201
    assert primera.json()["completos"] is False
    assert ultima.json()["completos"] is True
    assert ultima.json()["faltantes"] == []


def test_cargar_un_archivo_que_no_es_pdf_devuelve_415():
    id_colaborador, _ = registrar_con_proyecto("62000012")

    respuesta = cargar_documento(id_colaborador, "RUT", "rut.docx", b"PK word")

    assert respuesta.status_code == 415
    assert respuesta.json()["mensaje"] == "Solo se permiten archivos PDF"


def test_cargar_sin_tipo_ni_archivo_devuelve_422():
    id_colaborador, _ = registrar_con_proyecto("62000013")

    respuesta = cliente.post(f"/colaboradores/{id_colaborador}/documentos", headers=ADMIN)

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == ["tipo", "archivo"]


def test_consultar_documentos_como_direccion():
    id_colaborador, _ = registrar_con_proyecto("62000014")
    cargar_documento(id_colaborador, "RUT")

    cuerpo = cliente.get(f"/colaboradores/{id_colaborador}/documentos", headers=DIRECCION).json()

    assert [d["tipo"] for d in cuerpo["documentos"]] == ["RUT"]
    assert "Cédula" in cuerpo["faltantes"]
