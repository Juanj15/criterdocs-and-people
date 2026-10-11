"""HU-01: Registro de colaborador.

El orden de las validaciones sigue el diagrama de actividad de la RTF3:
rol (nodo 2) -> campos obligatorios (4) -> fechas (6) -> valor según la forma
de pago (7) -> cédula repetida (9) -> guardar dentro de try (11-12).
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List

from app.dominio.entidades import (Colaborador, EstadoColaborador, FormaPago, Rol, Usuario,
                                   Vinculacion)
from app.dominio.resultado import Resultado
from app.persistencia.repositorio_colaborador import ErrorPersistencia
from app.servicios.control_acceso import ControlAcceso

logger = logging.getLogger(__name__)

CAMPOS_OBLIGATORIOS = (
    "nombre_completo", "numero_documento", "correo", "banco", "numero_cuenta",
    "proyecto", "cargo", "fecha_inicio", "fecha_fin", "forma_pago",
)

ACCESO_NO_AUTORIZADO = Resultado.error("ACCESO_NO_AUTORIZADO", "Acceso no autorizado")


class ServicioColaborador:
    """Lógica de negocio para registrar y administrar colaboradores."""

    def __init__(self, repositorio, control_acceso: ControlAcceso = None) -> None:
        self._repositorio = repositorio
        self._control_acceso = control_acceso or ControlAcceso()

    def registrar(self, datos: Dict[str, Any], usuario: Usuario) -> Resultado:
        """Registra un colaborador con su primera vinculación (camino feliz C7)."""
        if not self._control_acceso.tiene_rol(usuario, Rol.ADMINISTRATIVO):    # nodo 2
            return ACCESO_NO_AUTORIZADO                                      # C1

        faltantes = self._validar_campos_obligatorios(datos)
        if faltantes:                                                        # nodo 4
            return Resultado.error("CAMPOS_FALTANTES",
                                   "Faltan campos obligatorios", faltantes)  # C2

        if datos["fecha_fin"] <= datos["fecha_inicio"]:                      # nodo 6
            return Resultado.error("DATOS_INVALIDOS",
                                   "La fecha fin debe ser posterior a la fecha inicio")  # C3

        if not self._validar_datos_vinculacion(datos):                       # nodo 7
            return Resultado.error("DATOS_INVALIDOS",
                                   "El valor no es válido para la forma de pago")  # C4

        if self._repositorio.existe_documento(datos["numero_documento"]):    # nodo 9
            return Resultado.error(
                "COLABORADOR_EXISTENTE",
                "El colaborador ya existe: agregue la nueva vinculación a su registro")  # C5

        colaborador = self._construir_colaborador(datos)
        try:                                                                 # nodo 11
            guardado = self._repositorio.guardar(colaborador)
        except ErrorPersistencia as error:                                   # nodo 12
            logger.error("No se pudo guardar el colaborador %s: %s",
                         datos["numero_documento"], error)
            return Resultado.error("ERROR_GUARDADO",
                                   "No fue posible guardar, intente de nuevo")  # C6

        return Resultado.ok("COLABORADOR_REGISTRADO", "Colaborador registrado", guardado)  # C7

    def cambiar_estado(self, id_colaborador: int, nuevo_estado: EstadoColaborador,
                       usuario: Usuario) -> Resultado:
        """Activa o desactiva un colaborador (RF-04)."""
        if not self._control_acceso.tiene_rol(usuario, Rol.ADMINISTRATIVO):
            return ACCESO_NO_AUTORIZADO

        colaborador = self._repositorio.buscar_por_id(id_colaborador)
        if colaborador is None:
            return Resultado.error("COLABORADOR_NO_ENCONTRADO", "El colaborador no existe")

        if colaborador.estado == nuevo_estado:
            return Resultado.error("ESTADO_SIN_CAMBIO",
                                   f"El colaborador ya está {nuevo_estado.value}")

        colaborador.estado = nuevo_estado
        return Resultado.ok("ESTADO_ACTUALIZADO", "Estado actualizado",
                            self._repositorio.guardar(colaborador))

    @staticmethod
    def _validar_campos_obligatorios(datos: Dict[str, Any]) -> List[str]:
        """Recorre los campos obligatorios y devuelve TODOS los que están vacíos."""
        faltantes = []
        for campo in CAMPOS_OBLIGATORIOS:
            valor = datos.get(campo)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                faltantes.append(campo)
        return faltantes

    @staticmethod
    def _validar_datos_vinculacion(datos: Dict[str, Any]) -> bool:
        """Revisa que el valor tenga sentido según la forma de pago."""
        try:
            forma_pago = FormaPago(datos["forma_pago"])
        except ValueError:
            return False

        if forma_pago == FormaPago.HONORARIO_MENSUAL:
            return _es_positivo(datos.get("valor_mensual"))
        return _es_positivo(datos.get("valor_total")) and _es_positivo(datos.get("numero_meses"))

    @staticmethod
    def _construir_colaborador(datos: Dict[str, Any]) -> Colaborador:
        vinculacion = Vinculacion(
            proyecto=datos["proyecto"].strip(),
            cargo=datos["cargo"].strip(),
            fecha_inicio=datos["fecha_inicio"],
            fecha_fin=datos["fecha_fin"],
            forma_pago=FormaPago(datos["forma_pago"]),
            valor_mensual=datos.get("valor_mensual"),
            valor_total=datos.get("valor_total"),
            numero_meses=datos.get("numero_meses"),
        )
        return Colaborador(
            nombre_completo=datos["nombre_completo"].strip(),
            numero_documento=datos["numero_documento"].strip(),
            correo=datos["correo"].strip(),
            banco=datos["banco"].strip(),
            numero_cuenta=datos["numero_cuenta"].strip(),
            vinculaciones=[vinculacion],
        )


def _es_positivo(valor: Any) -> bool:
    """True si el valor existe y es mayor que cero."""
    return valor is not None and Decimal(valor) > 0
