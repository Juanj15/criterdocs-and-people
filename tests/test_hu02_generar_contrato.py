"""Pruebas de HU-02: ServicioContrato.generar_contrato() (CDP-27, CDP-28, CDP-30).

Cada prueba lleva el camino del grafo de flujo de la RTF3 (Figura 6, V(G) = 7):
C1 sin rol, C2 vinculación no habilitada, C3 faltan documentos, C4 ya tiene
contrato, C5 sin plantilla, C6 falla el PDF (catch) y C7 camino feliz.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.dominio.entidades import EstadoColaborador, FormaPago, TipoDocumento
from app.persistencia.repositorio_contrato import RepositorioContratoMemoria
from app.persistencia.repositorio_plantilla import RepositorioPlantillaMemoria
from app.servicios.generador_pdf import ErrorGeneracionPDF, GeneradorPDF
from app.servicios.servicio_contrato import ServicioContrato
from app.servicios.servicio_documentos import Archivo, ServicioDocumentos

PDF = b"%PDF-1.4 soporte"


@pytest.fixture
def contratos():
    return RepositorioContratoMemoria()


@pytest.fixture
def plantillas():
    return RepositorioPlantillaMemoria()


@pytest.fixture
def servicio_contrato(repositorio, contratos, plantillas):
    return ServicioContrato(repositorio, contratos, plantillas)


@pytest.fixture
def laura(servicio, repositorio, auxiliar, datos_validos):
    """Laura con los cuatro documentos cargados. Devuelve (id_colaborador, id_vinculacion)."""
    id_colaborador = servicio.registrar(datos_validos, auxiliar).datos.id_colaborador
    documentos = ServicioDocumentos(repositorio)
    for tipo in TipoDocumento:
        documentos.cargar(id_colaborador, tipo.value, Archivo(f"{tipo.value}.pdf", PDF), auxiliar)
    colaborador = repositorio.buscar_por_id(id_colaborador)
    return id_colaborador, colaborador.vinculaciones[0].id_vinculacion


def test_c1_usuario_sin_rol_administrativo(servicio_contrato, direccion, laura):
    resultado = servicio_contrato.generar_contrato(*laura, direccion)

    assert resultado.codigo == "ACCESO_NO_AUTORIZADO"


def test_c2_vinculacion_que_no_existe(servicio_contrato, auxiliar, laura):
    resultado = servicio_contrato.generar_contrato(laura[0], 999, auxiliar)

    assert resultado.codigo == "VINCULACION_NO_HABILITADA"


def test_c2_colaborador_que_no_existe(servicio_contrato, auxiliar):
    resultado = servicio_contrato.generar_contrato(999, 1, auxiliar)

    assert resultado.codigo == "VINCULACION_NO_HABILITADA"


def test_c2_colaborador_inactivo(servicio_contrato, servicio, auxiliar, laura):
    servicio.cambiar_estado(laura[0], EstadoColaborador.INACTIVO, auxiliar)

    resultado = servicio_contrato.generar_contrato(*laura, auxiliar)

    assert resultado.codigo == "VINCULACION_NO_HABILITADA"


def test_c3_falta_el_rut(servicio_contrato, servicio, repositorio, contratos, auxiliar,
                         datos_validos):
    datos = dict(datos_validos, numero_documento="71000111")
    id_colaborador = servicio.registrar(datos, auxiliar).datos.id_colaborador
    documentos = ServicioDocumentos(repositorio)
    for tipo in (TipoDocumento.CEDULA, TipoDocumento.CERTIFICACION_BANCARIA,
                 TipoDocumento.HOJA_DE_VIDA):
        documentos.cargar(id_colaborador, tipo.value, Archivo("soporte.pdf", PDF), auxiliar)
    id_vinculacion = repositorio.buscar_por_id(id_colaborador).vinculaciones[0].id_vinculacion

    resultado = servicio_contrato.generar_contrato(id_colaborador, id_vinculacion, auxiliar)

    assert resultado.codigo == "DOCUMENTOS_FALTANTES"
    assert resultado.detalle == ["RUT"]
    assert contratos.historial(id_colaborador) == []


def test_c4_la_vinculacion_ya_tiene_contrato(servicio_contrato, contratos, auxiliar, laura):
    servicio_contrato.generar_contrato(*laura, auxiliar)

    resultado = servicio_contrato.generar_contrato(*laura, auxiliar)

    assert resultado.codigo == "CONTRATO_EXISTENTE"
    assert len(contratos.historial(laura[0])) == 1


def test_c5_sin_plantilla_para_la_forma_de_pago(servicio_contrato, plantillas, auxiliar, laura):
    plantillas.desactivar(FormaPago.HONORARIO_MENSUAL)

    resultado = servicio_contrato.generar_contrato(*laura, auxiliar)

    assert resultado.codigo == "SIN_PLANTILLA"


def test_c6_falla_el_generador_de_pdf(repositorio, contratos, plantillas, auxiliar, laura):
    generador = Mock(spec=GeneradorPDF)
    generador.generar.side_effect = ErrorGeneracionPDF("se cayó el servicio")
    servicio_contrato = ServicioContrato(repositorio, contratos, plantillas, generador)

    resultado = servicio_contrato.generar_contrato(*laura, auxiliar)

    assert resultado.codigo == "ERROR_PDF"
    assert contratos.historial(laura[0]) == []      # no queda un contrato "fantasma"


def test_c7_genera_el_contrato_y_lo_guarda_en_el_historial(servicio_contrato, contratos,
                                                          auxiliar, laura):
    resultado = servicio_contrato.generar_contrato(*laura, auxiliar)

    contrato = resultado.datos
    assert resultado.codigo == "CONTRATO_GENERADO"
    assert contrato.pdf.startswith(b"%PDF")
    assert b"Laura G" in contrato.pdf and b"1037654321" in contrato.pdf
    assert b"3.000.000" in contrato.pdf
    assert contratos.historial(laura[0]) == [contrato]


def test_plantilla_de_valor_total_dividido(servicio_contrato, servicio, repositorio, auxiliar,
                                          laura):
    servicio.agregar_vinculacion(laura[0], {
        "proyecto": "Conecta Futuro", "cargo": "Docente", "fecha_inicio": date(2026, 11, 1),
        "fecha_fin": date(2027, 4, 30), "forma_pago": FormaPago.VALOR_TOTAL_DIVIDIDO,
        "valor_total": Decimal("18000000"), "numero_meses": 6}, auxiliar)
    segunda = repositorio.buscar_por_id(laura[0]).vinculaciones[1].id_vinculacion

    resultado = servicio_contrato.generar_contrato(laura[0], segunda, auxiliar)

    assert resultado.codigo == "CONTRATO_GENERADO"
    assert b"18.000.000" in resultado.datos.pdf and b"6 cuotas" in resultado.datos.pdf


def test_dos_proyectos_dos_contratos(servicio_contrato, servicio, repositorio, contratos,
                                     auxiliar, laura):
    servicio.agregar_vinculacion(laura[0], {
        "proyecto": "Talento Tec", "cargo": "Mentora", "fecha_inicio": date(2026, 11, 1),
        "fecha_fin": date(2027, 1, 31), "forma_pago": FormaPago.HONORARIO_MENSUAL,
        "valor_mensual": Decimal("2000000")}, auxiliar)
    segunda = repositorio.buscar_por_id(laura[0]).vinculaciones[1].id_vinculacion

    servicio_contrato.generar_contrato(*laura, auxiliar)
    servicio_contrato.generar_contrato(laura[0], segunda, auxiliar)

    proyectos = [c.proyecto for c in contratos.historial(laura[0])]
    assert proyectos == ["Soy Digital", "Talento Tec"]


# ---------- historial y descarga ----------

def test_historial_lo_puede_ver_la_direccion(servicio_contrato, auxiliar, direccion, laura):
    servicio_contrato.generar_contrato(*laura, auxiliar)

    resultado = servicio_contrato.historial(laura[0], direccion)

    assert resultado.codigo == "HISTORIAL_CONSULTADO"
    assert len(resultado.datos) == 1


def test_historial_sin_rol_y_de_inexistente(servicio_contrato, auxiliar):
    assert servicio_contrato.historial(1, None).codigo == "ACCESO_NO_AUTORIZADO"
    assert servicio_contrato.historial(999, auxiliar).codigo == "COLABORADOR_NO_ENCONTRADO"


def test_descargar_contrato(servicio_contrato, auxiliar, laura):
    id_contrato = servicio_contrato.generar_contrato(*laura, auxiliar).datos.id_contrato

    resultado = servicio_contrato.descargar(id_contrato, auxiliar)

    assert resultado.codigo == "CONTRATO_ENCONTRADO"
    assert resultado.datos.nombre_archivo.endswith(".pdf")


def test_descargar_sin_rol_o_inexistente(servicio_contrato, auxiliar):
    assert servicio_contrato.descargar(1, None).codigo == "ACCESO_NO_AUTORIZADO"
    assert servicio_contrato.descargar(999, auxiliar).codigo == "CONTRATO_NO_ENCONTRADO"


def test_generador_real_convierte_errores_en_error_de_pdf():
    with pytest.raises(ErrorGeneracionPDF):
        GeneradorPDF().generar("Título", ["Texto con un carácter que no cabe: ☃"])
