"""Pruebas de HU-01 (RF-04): activar o desactivar un colaborador."""
from app.dominio.entidades import EstadoColaborador


def _registrar(servicio, auxiliar, datos):
    return servicio.registrar(datos, auxiliar).datos.id_colaborador


def test_desactivar_colaborador(servicio, repositorio, auxiliar, datos_validos):
    id_colaborador = _registrar(servicio, auxiliar, datos_validos)

    resultado = servicio.cambiar_estado(id_colaborador, EstadoColaborador.INACTIVO, auxiliar)

    assert resultado.codigo == "ESTADO_ACTUALIZADO"
    assert repositorio.buscar_por_id(id_colaborador).estado == EstadoColaborador.INACTIVO


def test_cambiar_estado_sin_rol(servicio, auxiliar, direccion, datos_validos):
    id_colaborador = _registrar(servicio, auxiliar, datos_validos)

    resultado = servicio.cambiar_estado(id_colaborador, EstadoColaborador.INACTIVO, direccion)

    assert resultado.codigo == "ACCESO_NO_AUTORIZADO"


def test_cambiar_estado_de_colaborador_inexistente(servicio, auxiliar):
    resultado = servicio.cambiar_estado(999, EstadoColaborador.INACTIVO, auxiliar)

    assert resultado.codigo == "COLABORADOR_NO_ENCONTRADO"


def test_no_se_cambia_al_mismo_estado(servicio, auxiliar, datos_validos):
    id_colaborador = _registrar(servicio, auxiliar, datos_validos)

    resultado = servicio.cambiar_estado(id_colaborador, EstadoColaborador.ACTIVO, auxiliar)

    assert resultado.codigo == "ESTADO_SIN_CAMBIO"
