"""HU-02: carga de documentos de soporte (CDP-25) y revisión de los obligatorios (CDP-26)."""
import logging
from datetime import date
from typing import List, NamedTuple

from app.dominio.entidades import Colaborador, DocumentoSoporte, Rol, TipoDocumento, Usuario
from app.dominio.resultado import Resultado
from app.persistencia.repositorio_colaborador import ErrorPersistencia
from app.servicios.control_acceso import ControlAcceso

logger = logging.getLogger(__name__)

ACCESO_NO_AUTORIZADO = Resultado.error("ACCESO_NO_AUTORIZADO", "Acceso no autorizado")
NO_ENCONTRADO = Resultado.error("COLABORADOR_NO_ENCONTRADO", "El colaborador no existe")


class Archivo(NamedTuple):
    """Archivo que llega desde el formulario."""
    nombre: str
    contenido: bytes


def validar_documentos(colaborador: Colaborador) -> List[TipoDocumento]:
    """Método de apoyo de la RTF3 (Figura 8): devuelve los documentos obligatorios que faltan."""
    faltantes = []
    for tipo in TipoDocumento:                 # nodo 2: recorre los cuatro tipos
        if tipo not in colaborador.documentos:  # nodo 3: ¿lo tiene cargado?
            faltantes.append(tipo)              # nodo 4
    return faltantes


def _es_pdf(nombre_archivo: str, contenido: bytes) -> bool:
    """Revisa la extensión y también la firma del archivo, por si le cambiaron el nombre."""
    return nombre_archivo.lower().endswith(".pdf") and contenido.startswith(b"%PDF")


class ServicioDocumentos:
    """Carga y consulta de los documentos de soporte del colaborador."""

    def __init__(self, repositorio, control_acceso: ControlAcceso = None) -> None:
        self._repositorio = repositorio
        self._control_acceso = control_acceso or ControlAcceso()

    def cargar(self, id_colaborador: int, tipo: str, archivo: Archivo,
               usuario: Usuario) -> Resultado:
        """Carga (o reemplaza) un documento en PDF."""
        if not self._control_acceso.tiene_rol(usuario, Rol.ADMINISTRATIVO):
            return ACCESO_NO_AUTORIZADO

        colaborador = self._repositorio.buscar_por_id(id_colaborador)
        if colaborador is None:
            return NO_ENCONTRADO

        try:
            tipo_documento = TipoDocumento(tipo)
        except ValueError:
            return Resultado.error("DATOS_INVALIDOS", "Tipo de documento no válido", ["tipo"])

        if not _es_pdf(archivo.nombre, archivo.contenido):
            return Resultado.error("FORMATO_NO_PERMITIDO", "Solo se permiten archivos PDF",
                                   [tipo_documento.descripcion])

        colaborador.documentos[tipo_documento] = DocumentoSoporte(
            tipo_documento, archivo.nombre, archivo.contenido, date.today())
        try:
            guardado = self._repositorio.guardar(colaborador)
        except ErrorPersistencia as error:
            logger.error("No se pudo guardar el documento %s: %s", tipo, error)
            return Resultado.error("ERROR_GUARDADO", "No fue posible guardar, intente de nuevo")
        return Resultado.ok("DOCUMENTO_CARGADO", "Documento cargado", guardado)

    def consultar(self, id_colaborador: int, usuario: Usuario) -> Resultado:
        """Devuelve el colaborador con sus documentos (auxiliar o dirección)."""
        if not self._control_acceso.tiene_alguno(usuario, Rol.ADMINISTRATIVO, Rol.DIRECCION):
            return ACCESO_NO_AUTORIZADO
        colaborador = self._repositorio.buscar_por_id(id_colaborador)
        if colaborador is None:
            return NO_ENCONTRADO
        return Resultado.ok("DOCUMENTOS_CONSULTADOS", "Documentos del colaborador", colaborador)
