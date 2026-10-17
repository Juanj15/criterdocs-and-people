"""HU-01: Registro de colaborador.

El orden de las validaciones sigue el diagrama de actividad de la RTF3:
rol (nodo 2) -> campos obligatorios (4) -> fechas (6) -> valor según la forma
de pago (7) -> cédula repetida (9) -> guardar dentro de try (11-12).
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.dominio.entidades import (Colaborador, EstadoColaborador, FormaPago, Rol, Usuario,
                                   Vinculacion)
from app.dominio.resultado import Resultado
from app.persistencia.repositorio_colaborador import ErrorPersistencia
from app.servicios.control_acceso import ControlAcceso

logger = logging.getLogger(__name__)

CAMPOS_PERSONALES = ("nombre_completo", "numero_documento", "correo", "banco", "numero_cuenta")
CAMPOS_VINCULACION = ("proyecto", "cargo", "fecha_inicio", "fecha_fin", "forma_pago")
CAMPOS_OBLIGATORIOS = CAMPOS_PERSONALES + CAMPOS_VINCULACION

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

    def editar(self, id_colaborador: int, cambios: Dict[str, Any],
               usuario: Usuario) -> Resultado:
        """Actualiza los datos personales y bancarios de un colaborador (RF-03).

        Solo cambia los campos que llegan en `cambios`; los proyectos se manejan
        con agregar_vinculacion().
        """
        if not self._control_acceso.tiene_rol(usuario, Rol.ADMINISTRATIVO):
            return ACCESO_NO_AUTORIZADO

        colaborador = self._repositorio.buscar_por_id(id_colaborador)
        if colaborador is None:
            return Resultado.error("COLABORADOR_NO_ENCONTRADO", "El colaborador no existe")

        cambios = {c: v for c, v in cambios.items() if c in CAMPOS_PERSONALES}
        vacios = self._validar_campos_obligatorios(cambios, tuple(cambios))
        if vacios:
            return Resultado.error("CAMPOS_FALTANTES",
                                   "No se pueden dejar campos obligatorios vacíos", vacios)

        nueva_cedula = cambios.get("numero_documento")
        if nueva_cedula and self._repositorio.existe_documento(nueva_cedula.strip(),
                                                               excluir_id=id_colaborador):
            return Resultado.error("COLABORADOR_EXISTENTE",
                                   "Esa cédula ya pertenece a otro colaborador")

        for campo, valor in cambios.items():
            setattr(colaborador, campo, valor.strip())
        return self._guardar(colaborador, "COLABORADOR_ACTUALIZADO", "Colaborador actualizado")

    def agregar_vinculacion(self, id_colaborador: int, datos: Dict[str, Any],
                            usuario: Usuario) -> Resultado:
        """Agrega un nuevo proyecto a un colaborador que ya existe."""
        if not self._control_acceso.tiene_rol(usuario, Rol.ADMINISTRATIVO):
            return ACCESO_NO_AUTORIZADO

        colaborador = self._repositorio.buscar_por_id(id_colaborador)
        if colaborador is None:
            return Resultado.error("COLABORADOR_NO_ENCONTRADO", "El colaborador no existe")
        if not colaborador.esta_activo():
            return Resultado.error("COLABORADOR_INACTIVO",
                                   "No se pueden agregar proyectos a un colaborador inactivo")

        error = self._validar_nueva_vinculacion(datos)
        if error:
            return error

        vinculacion = self._construir_vinculacion(datos)
        if any(v.se_cruza_con(vinculacion) for v in colaborador.vinculaciones):
            return Resultado.error("VINCULACION_DUPLICADA",
                                   "Ya tiene ese proyecto en fechas que se cruzan")

        colaborador.vinculaciones.append(vinculacion)
        return self._guardar(colaborador, "VINCULACION_AGREGADA", "Proyecto agregado")

    def _guardar(self, colaborador: Colaborador, codigo: str, mensaje: str) -> Resultado:
        """Guarda dentro de try/except para no dejar cambios a medias."""
        try:
            guardado = self._repositorio.guardar(colaborador)
        except ErrorPersistencia as error:
            logger.error("No se pudo guardar el colaborador %s: %s",
                         colaborador.numero_documento, error)
            return Resultado.error("ERROR_GUARDADO", "No fue posible guardar, intente de nuevo")
        return Resultado.ok(codigo, mensaje, guardado)

    def _validar_nueva_vinculacion(self, datos: Dict[str, Any]) -> Optional[Resultado]:
        """Mismas reglas de la vinculación que en registrar() (nodos 4, 6 y 7)."""
        faltantes = self._validar_campos_obligatorios(datos, CAMPOS_VINCULACION)
        if faltantes:
            return Resultado.error("CAMPOS_FALTANTES", "Faltan campos obligatorios", faltantes)
        if datos["fecha_fin"] <= datos["fecha_inicio"]:
            return Resultado.error("DATOS_INVALIDOS",
                                   "La fecha fin debe ser posterior a la fecha inicio")
        if not self._validar_datos_vinculacion(datos):
            return Resultado.error("DATOS_INVALIDOS", "El valor no es válido para la forma de pago")
        return None

    @staticmethod
    def _validar_campos_obligatorios(datos: Dict[str, Any],
                                     campos=CAMPOS_OBLIGATORIOS) -> List[str]:
        """Recorre los campos obligatorios y devuelve TODOS los que están vacíos."""
        faltantes = []
        for campo in campos:
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
    def _construir_vinculacion(datos: Dict[str, Any]) -> Vinculacion:
        return Vinculacion(
            proyecto=datos["proyecto"].strip(),
            cargo=datos["cargo"].strip(),
            fecha_inicio=datos["fecha_inicio"],
            fecha_fin=datos["fecha_fin"],
            forma_pago=FormaPago(datos["forma_pago"]),
            valor_mensual=datos.get("valor_mensual"),
            valor_total=datos.get("valor_total"),
            numero_meses=datos.get("numero_meses"),
        )

    def _construir_colaborador(self, datos: Dict[str, Any]) -> Colaborador:
        vinculacion = self._construir_vinculacion(datos)
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
