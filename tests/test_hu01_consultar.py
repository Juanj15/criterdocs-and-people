"""Pruebas de HU-01: consultar un colaborador (hallazgo de las pruebas de caja negra, CDP-43).

Sin esta consulta no había forma de comprobar desde afuera que el registro, la
edición o el cambio de estado quedaron guardados.
"""
from app.dominio.entidades import Rol, Usuario


def test_auxiliar_consulta_un_colaborador(servicio, auxiliar, datos_validos):
    id_colaborador = servicio.registrar(datos_validos, auxiliar).datos.id_colaborador

    resultado = servicio.consultar(id_colaborador, auxiliar)

    assert resultado.codigo == "COLABORADOR_ENCONTRADO"
    assert resultado.datos.nombre_completo == "Laura Gómez"


def test_direccion_tambien_puede_consultar(servicio, auxiliar, direccion, datos_validos):
    id_colaborador = servicio.registrar(datos_validos, auxiliar).datos.id_colaborador

    resultado = servicio.consultar(id_colaborador, direccion)

    assert resultado.codigo == "COLABORADOR_ENCONTRADO"


def test_usuario_sin_rol_no_puede_consultar(servicio, auxiliar, datos_validos):
    id_colaborador = servicio.registrar(datos_validos, auxiliar).datos.id_colaborador
    sin_rol = Usuario(id_usuario=3, nombre="Sin rol", rol=None)

    resultado = servicio.consultar(id_colaborador, sin_rol)

    assert resultado.codigo == "ACCESO_NO_AUTORIZADO"


def test_consultar_colaborador_inexistente(servicio, auxiliar):
    resultado = servicio.consultar(999, auxiliar)

    assert resultado.codigo == "COLABORADOR_NO_ENCONTRADO"


def test_control_de_acceso_con_varios_roles(servicio):
    control = servicio._control_acceso  # pylint: disable=protected-access
    gerente = Usuario(id_usuario=4, nombre="Gerencia", rol=Rol.DIRECCION)

    assert control.tiene_alguno(gerente, Rol.ADMINISTRATIVO, Rol.DIRECCION)
    assert not control.tiene_alguno(None, Rol.ADMINISTRATIVO, Rol.DIRECCION)
