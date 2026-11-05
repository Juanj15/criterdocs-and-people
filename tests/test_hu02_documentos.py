"""Pruebas de HU-02: carga de documentos de soporte (CDP-25) y validar_documentos() (CDP-26).

validar_documentos() es el método de apoyo de la RTF3 (Figura 8): recorre los
cuatro tipos obligatorios y devuelve los que faltan. Sus caminos son D1, D2 y D3.
"""
from unittest.mock import patch

import pytest

from app.dominio.entidades import TipoDocumento
from app.persistencia.repositorio_colaborador import ErrorPersistencia
from app.servicios.servicio_documentos import Archivo, ServicioDocumentos, validar_documentos

PDF = b"%PDF-1.4 documento de prueba"


@pytest.fixture
def documentos(repositorio):
    return ServicioDocumentos(repositorio)


@pytest.fixture
def id_laura(servicio, auxiliar, datos_validos):
    return servicio.registrar(datos_validos, auxiliar).datos.id_colaborador


def _cargar_todos(documentos, id_colaborador, usuario, excepto=()):
    for tipo in TipoDocumento:
        if tipo not in excepto:
            archivo = Archivo(f"{tipo.value}.pdf", PDF)
            documentos.cargar(id_colaborador, tipo.value, archivo, usuario)


# ---------- cargar() ----------

def test_cargar_un_documento_pdf(documentos, repositorio, auxiliar, id_laura):
    resultado = documentos.cargar(id_laura, "RUT", Archivo("rut_laura.pdf", PDF), auxiliar)

    assert resultado.codigo == "DOCUMENTO_CARGADO"
    guardado = repositorio.buscar_por_id(id_laura).documentos[TipoDocumento.RUT]
    assert guardado.nombre_archivo == "rut_laura.pdf"


def test_volver_a_cargar_reemplaza_el_documento(documentos, repositorio, auxiliar, id_laura):
    documentos.cargar(id_laura, "RUT", Archivo("rut_viejo.pdf", PDF), auxiliar)
    documentos.cargar(id_laura, "RUT", Archivo("rut_nuevo.pdf", PDF), auxiliar)

    colaborador = repositorio.buscar_por_id(id_laura)
    assert len(colaborador.documentos) == 1
    assert colaborador.documentos[TipoDocumento.RUT].nombre_archivo == "rut_nuevo.pdf"


def test_cargar_sin_rol_administrativo(documentos, direccion, id_laura):
    resultado = documentos.cargar(id_laura, "RUT", Archivo("rut.pdf", PDF), direccion)

    assert resultado.codigo == "ACCESO_NO_AUTORIZADO"


def test_cargar_a_colaborador_inexistente(documentos, auxiliar):
    resultado = documentos.cargar(999, "RUT", Archivo("rut.pdf", PDF), auxiliar)

    assert resultado.codigo == "COLABORADOR_NO_ENCONTRADO"


def test_tipo_de_documento_desconocido(documentos, auxiliar, id_laura):
    resultado = documentos.cargar(id_laura, "PASAPORTE", Archivo("pasaporte.pdf", PDF), auxiliar)

    assert resultado.codigo == "DATOS_INVALIDOS"


@pytest.mark.parametrize("nombre, contenido", [
    ("rut.docx", b"PK documento de word"),        # otra extensión
    ("rut.pdf", b"PK no es un pdf de verdad"),   # extensión cambiada a mano
    ("rut.pdf", b""),                            # archivo vacío
])
def test_solo_se_aceptan_pdf(documentos, repositorio, auxiliar, id_laura, nombre, contenido):
    resultado = documentos.cargar(id_laura, "RUT", Archivo(nombre, contenido), auxiliar)

    assert resultado.codigo == "FORMATO_NO_PERMITIDO"
    assert repositorio.buscar_por_id(id_laura).documentos == {}


def test_error_al_guardar_el_documento(documentos, repositorio, auxiliar, id_laura):
    with patch.object(repositorio, "guardar", side_effect=ErrorPersistencia("sin conexión")):
        resultado = documentos.cargar(id_laura, "RUT", Archivo("rut.pdf", PDF), auxiliar)

    assert resultado.codigo == "ERROR_GUARDADO"


# ---------- consultar() ----------

def test_consultar_documentos_como_direccion(documentos, auxiliar, direccion, id_laura):
    documentos.cargar(id_laura, "CEDULA", Archivo("cedula.pdf", PDF), auxiliar)

    resultado = documentos.consultar(id_laura, direccion)

    assert resultado.codigo == "DOCUMENTOS_CONSULTADOS"
    assert TipoDocumento.CEDULA in resultado.datos.documentos


def test_consultar_documentos_sin_rol(documentos):
    assert documentos.consultar(1, None).codigo == "ACCESO_NO_AUTORIZADO"


def test_consultar_documentos_de_inexistente(documentos, auxiliar):
    assert documentos.consultar(999, auxiliar).codigo == "COLABORADOR_NO_ENCONTRADO"


# ---------- validar_documentos(): caminos D1, D2 y D3 de la RTF3 ----------

def test_d1_con_los_cuatro_documentos_no_falta_nada(documentos, repositorio, auxiliar, id_laura):
    _cargar_todos(documentos, id_laura, auxiliar)

    assert not validar_documentos(repositorio.buscar_por_id(id_laura))


def test_d2_falta_solo_el_rut(documentos, repositorio, auxiliar, id_laura):
    _cargar_todos(documentos, id_laura, auxiliar, excepto=(TipoDocumento.RUT,))

    assert validar_documentos(repositorio.buscar_por_id(id_laura)) == [TipoDocumento.RUT]


def test_d3_sin_documentos_faltan_los_cuatro(repositorio, id_laura):
    assert validar_documentos(repositorio.buscar_por_id(id_laura)) == list(TipoDocumento)
