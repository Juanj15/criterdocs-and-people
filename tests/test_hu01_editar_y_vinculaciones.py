"""Pruebas de HU-01 (RF-03 y vinculaciones): editar() y agregar_vinculacion().

Completan la HU-01 en el Sprint 2. Un colaborador puede tener varias
vinculaciones (una por proyecto), como quedó en la versión ajustada de la RTF3.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.dominio.entidades import EstadoColaborador, FormaPago
from app.persistencia.repositorio_colaborador import ErrorPersistencia


@pytest.fixture
def id_laura(servicio, auxiliar, datos_validos):
    """Registra a Laura (proyecto Soy Digital) y devuelve su id."""
    return servicio.registrar(datos_validos, auxiliar).datos.id_colaborador


@pytest.fixture
def nueva_vinculacion():
    """Segundo proyecto de Laura, con valor total dividido."""
    return {
        "proyecto": "Conecta Futuro",
        "cargo": "Docente",
        "fecha_inicio": date(2026, 11, 1),
        "fecha_fin": date(2027, 4, 30),
        "forma_pago": FormaPago.VALOR_TOTAL_DIVIDIDO,
        "valor_total": Decimal("18000000"),
        "numero_meses": 6,
    }


# ---------- editar() ----------

def test_editar_actualiza_datos_personales(servicio, repositorio, auxiliar, id_laura):
    resultado = servicio.editar(id_laura, {"correo": "laura.g@critertec.com",
                                           "banco": "Davivienda"}, auxiliar)

    assert resultado.codigo == "COLABORADOR_ACTUALIZADO"
    guardado = repositorio.buscar_por_id(id_laura)
    assert guardado.correo == "laura.g@critertec.com"
    assert guardado.banco == "Davivienda"
    assert guardado.nombre_completo == "Laura Gómez"   # lo que no se envía no cambia


def test_editar_sin_rol(servicio, direccion, id_laura):
    assert servicio.editar(id_laura, {"correo": "x@y.com"}, direccion).codigo \
        == "ACCESO_NO_AUTORIZADO"


def test_editar_colaborador_inexistente(servicio, auxiliar):
    assert servicio.editar(999, {"correo": "x@y.com"}, auxiliar).codigo \
        == "COLABORADOR_NO_ENCONTRADO"


def test_editar_no_permite_dejar_campos_vacios(servicio, auxiliar, id_laura):
    resultado = servicio.editar(id_laura, {"correo": "  ", "banco": ""}, auxiliar)

    assert resultado.codigo == "CAMPOS_FALTANTES"
    assert resultado.detalle == ["correo", "banco"]


def test_editar_no_permite_cedula_de_otro_colaborador(servicio, auxiliar, datos_validos, id_laura):
    otro = dict(datos_validos, numero_documento="55555555", nombre_completo="Pedro Ríos")
    servicio.registrar(otro, auxiliar)

    resultado = servicio.editar(id_laura, {"numero_documento": "55555555"}, auxiliar)

    assert resultado.codigo == "COLABORADOR_EXISTENTE"


def test_editar_conservando_su_propia_cedula(servicio, auxiliar, id_laura):
    resultado = servicio.editar(id_laura, {"numero_documento": "1037654321"}, auxiliar)

    assert resultado.codigo == "COLABORADOR_ACTUALIZADO"


def test_editar_error_al_guardar(servicio, repositorio, auxiliar, id_laura):
    with patch.object(repositorio, "guardar", side_effect=ErrorPersistencia("sin conexión")):
        resultado = servicio.editar(id_laura, {"correo": "nuevo@correo.com"}, auxiliar)

    assert resultado.codigo == "ERROR_GUARDADO"
    assert repositorio.buscar_por_id(id_laura).correo == "laura.gomez@correo.com"


# ---------- agregar_vinculacion() ----------

def test_agregar_segundo_proyecto(servicio, repositorio, auxiliar, id_laura, nueva_vinculacion):
    resultado = servicio.agregar_vinculacion(id_laura, nueva_vinculacion, auxiliar)

    assert resultado.codigo == "VINCULACION_AGREGADA"
    proyectos = [v.proyecto for v in repositorio.buscar_por_id(id_laura).vinculaciones]
    assert proyectos == ["Soy Digital", "Conecta Futuro"]


def test_agregar_vinculacion_sin_rol(servicio, direccion, id_laura, nueva_vinculacion):
    assert servicio.agregar_vinculacion(id_laura, nueva_vinculacion, direccion).codigo \
        == "ACCESO_NO_AUTORIZADO"


def test_agregar_vinculacion_a_colaborador_inexistente(servicio, auxiliar, nueva_vinculacion):
    assert servicio.agregar_vinculacion(999, nueva_vinculacion, auxiliar).codigo \
        == "COLABORADOR_NO_ENCONTRADO"


def test_no_se_vincula_a_un_colaborador_inactivo(servicio, auxiliar, id_laura, nueva_vinculacion):
    servicio.cambiar_estado(id_laura, EstadoColaborador.INACTIVO, auxiliar)

    assert servicio.agregar_vinculacion(id_laura, nueva_vinculacion, auxiliar).codigo \
        == "COLABORADOR_INACTIVO"


@pytest.mark.parametrize("cambio, codigo", [
    ({"cargo": ""}, "CAMPOS_FALTANTES"),
    ({"fecha_fin": date(2026, 10, 1)}, "DATOS_INVALIDOS"),
    ({"numero_meses": 0}, "DATOS_INVALIDOS"),
])
def test_validaciones_de_la_nueva_vinculacion(servicio, auxiliar, id_laura, nueva_vinculacion,
                                              cambio, codigo):
    nueva_vinculacion.update(cambio)

    assert servicio.agregar_vinculacion(id_laura, nueva_vinculacion, auxiliar).codigo == codigo


def test_no_se_repite_el_mismo_proyecto_en_fechas_que_se_cruzan(servicio, auxiliar, id_laura,
                                                                nueva_vinculacion):
    nueva_vinculacion.update({"proyecto": "Soy Digital", "fecha_inicio": date(2026, 12, 1),
                              "fecha_fin": date(2027, 2, 28)})

    assert servicio.agregar_vinculacion(id_laura, nueva_vinculacion, auxiliar).codigo \
        == "VINCULACION_DUPLICADA"


def test_mismo_proyecto_en_otro_periodo_si_se_permite(servicio, auxiliar, id_laura,
                                                     nueva_vinculacion):
    nueva_vinculacion.update({"proyecto": "Soy Digital", "fecha_inicio": date(2027, 1, 1),
                              "fecha_fin": date(2027, 6, 30)})

    assert servicio.agregar_vinculacion(id_laura, nueva_vinculacion, auxiliar).codigo \
        == "VINCULACION_AGREGADA"


def test_agregar_vinculacion_error_al_guardar(servicio, repositorio, auxiliar, id_laura,
                                             nueva_vinculacion):
    with patch.object(repositorio, "guardar", side_effect=ErrorPersistencia("sin conexión")):
        resultado = servicio.agregar_vinculacion(id_laura, nueva_vinculacion, auxiliar)

    assert resultado.codigo == "ERROR_GUARDADO"
    assert len(repositorio.buscar_por_id(id_laura).vinculaciones) == 1
