"""Pruebas estructurales de HU-01: ServicioColaborador.registrar().

Cada prueba lleva en el nombre el camino del grafo de flujo de la RTF3
(sección 5.2) que recorre. V(G) = 7, por eso hay 7 caminos (C1 a C7),
más las pruebas de condiciones y valores límite.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.dominio.entidades import EstadoColaborador, FormaPago
from app.persistencia.repositorio_colaborador import ErrorPersistencia


# ---------- Caminos independientes ----------

def test_c1_usuario_sin_rol_administrativo_es_rechazado(servicio, repositorio,
                                                        direccion, datos_validos):
    resultado = servicio.registrar(datos_validos, direccion)

    assert not resultado.exito
    assert resultado.codigo == "ACCESO_NO_AUTORIZADO"
    assert repositorio.contar() == 0


def test_c2_campos_obligatorios_vacios_devuelve_la_lista(servicio, repositorio,
                                                        auxiliar, datos_validos):
    datos_validos["banco"] = ""
    del datos_validos["numero_cuenta"]

    resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.codigo == "CAMPOS_FALTANTES"
    assert resultado.detalle == ["banco", "numero_cuenta"]
    assert repositorio.contar() == 0


def test_c3_fecha_fin_anterior_a_fecha_inicio(servicio, auxiliar, datos_validos):
    datos_validos["fecha_inicio"] = date(2026, 11, 1)
    datos_validos["fecha_fin"] = date(2026, 10, 30)

    resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.codigo == "DATOS_INVALIDOS"


def test_c4_valor_del_contrato_en_cero(servicio, auxiliar, datos_validos):
    datos_validos["valor_mensual"] = Decimal("0")

    resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.codigo == "DATOS_INVALIDOS"


def test_c5_cedula_ya_registrada_pide_agregar_vinculacion(servicio, repositorio,
                                                         auxiliar, datos_validos):
    servicio.registrar(dict(datos_validos), auxiliar)

    resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.codigo == "COLABORADOR_EXISTENTE"
    assert "vinculación" in resultado.mensaje
    assert repositorio.contar() == 1


def test_c6_error_al_guardar_entra_al_catch(servicio, repositorio, auxiliar, datos_validos):
    with patch.object(repositorio, "guardar", side_effect=ErrorPersistencia("sin conexión")):
        resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.codigo == "ERROR_GUARDADO"
    assert repositorio.contar() == 0


def test_c7_registro_exitoso_queda_activo_con_su_vinculacion(servicio, repositorio,
                                                            auxiliar, datos_validos):
    resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.exito
    assert resultado.codigo == "COLABORADOR_REGISTRADO"
    guardado = repositorio.buscar_por_id(resultado.datos.id_colaborador)
    assert guardado.estado == EstadoColaborador.ACTIVO
    assert len(guardado.vinculaciones) == 1
    assert guardado.vinculaciones[0].proyecto == "Soy Digital"


# ---------- Condición (4): ciclo de campos obligatorios ----------

@pytest.mark.parametrize("campos_vacios", [
    ["correo"],                                   # 1 campo vacío
    ["nombre_completo", "numero_documento", "correo", "banco", "numero_cuenta",
     "proyecto", "cargo", "fecha_inicio", "fecha_fin", "forma_pago"],  # todos vacíos
])
def test_ciclo_de_campos_reporta_todos_los_faltantes(servicio, auxiliar, datos_validos,
                                                     campos_vacios):
    for campo in campos_vacios:
        datos_validos[campo] = None

    resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.codigo == "CAMPOS_FALTANTES"
    assert resultado.detalle == campos_vacios


def test_campo_con_solo_espacios_cuenta_como_vacio(servicio, auxiliar, datos_validos):
    datos_validos["nombre_completo"] = "   "

    resultado = servicio.registrar(datos_validos, auxiliar)

    assert resultado.detalle == ["nombre_completo"]


# ---------- Condiciones (6) y (7): valores límite ----------

def test_fechas_iguales_se_consideran_invalidas(servicio, auxiliar, datos_validos):
    datos_validos["fecha_fin"] = datos_validos["fecha_inicio"]

    assert servicio.registrar(datos_validos, auxiliar).codigo == "DATOS_INVALIDOS"


@pytest.mark.parametrize("valor, codigo_esperado", [
    (Decimal("-1"), "DATOS_INVALIDOS"),
    (Decimal("0"), "DATOS_INVALIDOS"),
    (Decimal("1"), "COLABORADOR_REGISTRADO"),
    (None, "DATOS_INVALIDOS"),
])
def test_valores_limite_del_honorario_mensual(servicio, auxiliar, datos_validos,
                                              valor, codigo_esperado):
    datos_validos["valor_mensual"] = valor

    assert servicio.registrar(datos_validos, auxiliar).codigo == codigo_esperado


@pytest.mark.parametrize("valor_total, meses, codigo_esperado", [
    (Decimal("18000000"), 6, "COLABORADOR_REGISTRADO"),
    (Decimal("18000000"), 0, "DATOS_INVALIDOS"),   # evitaría una división por cero en HU-04
    (Decimal("0"), 6, "DATOS_INVALIDOS"),
])
def test_valor_total_dividido_exige_valor_y_meses(servicio, auxiliar, datos_validos,
                                                  valor_total, meses, codigo_esperado):
    datos_validos["forma_pago"] = FormaPago.VALOR_TOTAL_DIVIDIDO
    datos_validos["valor_total"] = valor_total
    datos_validos["numero_meses"] = meses

    assert servicio.registrar(datos_validos, auxiliar).codigo == codigo_esperado


def test_forma_de_pago_desconocida_es_invalida(servicio, auxiliar, datos_validos):
    datos_validos["forma_pago"] = "POR_HORAS"

    assert servicio.registrar(datos_validos, auxiliar).codigo == "DATOS_INVALIDOS"
