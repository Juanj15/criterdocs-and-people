"""Datos y pasos que comparten las pruebas de extremo a extremo.

Preparar los datos se hace por la API (es el "Dado que"); la acción y lo que
se revisa siempre pasan por la pantalla, como lo haría el usuario.
"""
from pathlib import Path

from playwright.sync_api import Page, expect

AUXILIAR = {"X-Rol": "ADMINISTRATIVO"}
DATOS = Path(__file__).resolve().parent.parent / "datos"
ARCHIVOS = {
    "CEDULA": "cedula.pdf",
    "CERTIFICACION_BANCARIA": "certificacion_bancaria.pdf",
    "RUT": "rut.pdf",
    "HOJA_DE_VIDA": "hoja_de_vida.pdf",
}
LAURA = {
    "nombre_completo": "Laura Gómez", "correo": "laura.gomez@correo.com",
    "banco": "Bancolombia", "numero_cuenta": "12345678901", "proyecto": "Conecta Futuro",
    "cargo": "Docente", "fecha_inicio": "2026-11-01", "fecha_fin": "2027-04-30",
    "forma_pago": "HONORARIO_MENSUAL", "valor_mensual": "3000000",
}


def registrar(pagina: Page, url: str, cedula: str, **cambios) -> int:
    """Registra a Laura por la API (con los cambios pedidos) y devuelve su id.

    Un cambio con valor None quita ese campo de la petición.
    """
    datos = {campo: valor for campo, valor in dict(LAURA, numero_documento=cedula,
                                                   **cambios).items() if valor is not None}
    respuesta = pagina.request.post(f"{url}/colaboradores", headers=AUXILIAR, data=datos)
    return respuesta.json()["id_colaborador"]


def agregar_proyecto(pagina: Page, url: str, id_colaborador: int, **datos) -> None:
    """Agrega un proyecto por la API."""
    pagina.request.post(f"{url}/colaboradores/{id_colaborador}/vinculaciones",
                        headers=AUXILIAR, data=datos)


def cambiar_estado(pagina: Page, url: str, id_colaborador: int, estado: str) -> None:
    """Activa o desactiva por la API."""
    pagina.request.patch(f"{url}/colaboradores/{id_colaborador}/estado",
                         headers=AUXILIAR, data={"estado": estado})


def cargar_documentos(pagina: Page, url: str, id_colaborador: int, sin=()) -> None:
    """Carga por la API los documentos obligatorios, menos los indicados en 'sin'."""
    for tipo, archivo in ARCHIVOS.items():
        if tipo not in sin:
            ruta = DATOS / archivo
            pagina.request.post(
                f"{url}/colaboradores/{id_colaborador}/documentos", headers=AUXILIAR,
                multipart={"tipo": tipo, "archivo": {
                    "name": archivo, "mimeType": "application/pdf",
                    "buffer": ruta.read_bytes()}})


def buscar(pagina: Page, url: str, pantalla: str, id_colaborador) -> None:
    """Abre la pantalla, escribe el número del colaborador y pulsa Buscar."""
    pagina.goto(f"{url}{pantalla}")
    pagina.fill("#id_colaborador", str(id_colaborador))
    pagina.get_by_role("button", name="Buscar").click()


def abrir_ficha(pagina: Page, url: str, id_colaborador: int) -> None:
    """Busca al colaborador en la ficha y espera a que se vean sus datos."""
    buscar(pagina, url, "/ficha", id_colaborador)
    expect(pagina.locator("#detalle")).to_be_visible()


def abrir_contratos(pagina: Page, url: str, id_colaborador: int) -> None:
    """Busca al colaborador en documentos y contratos."""
    buscar(pagina, url, "/contratos", id_colaborador)
    expect(pagina.locator("#detalle")).to_be_visible()
