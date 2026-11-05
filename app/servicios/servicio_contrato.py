"""HU-02: Generación automática de contratos (CDP-27 y CDP-28).

El orden de las decisiones sigue el grafo de flujo de la RTF3 (Figura 6):
rol (nodo 2) -> vinculación habilitada (4) -> documentos completos (6) ->
contrato previo (8) -> plantilla vigente (10) -> generar PDF dentro de try (12-13).
"""
import logging
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from app.dominio.entidades import (Colaborador, Contrato, FormaPago, PlantillaContrato, Rol,
                                   Usuario, Vinculacion)
from app.dominio.resultado import Resultado
from app.servicios.control_acceso import ControlAcceso
from app.servicios.generador_pdf import ErrorGeneracionPDF, GeneradorPDF
from app.servicios.servicio_documentos import validar_documentos

logger = logging.getLogger(__name__)

ACCESO_NO_AUTORIZADO = Resultado.error("ACCESO_NO_AUTORIZADO", "Acceso no autorizado")


def _pesos(valor: Optional[Decimal]) -> str:
    """3000000 -> 3.000.000"""
    return f"{int(valor or 0):,}".replace(",", ".")


def _fecha(dia: date) -> str:
    return dia.strftime("%d/%m/%Y")


class ServicioContrato:
    """Genera el contrato en PDF de una vinculación y lo guarda en el historial."""

    def __init__(self, repo_colaboradores, repo_contratos, repo_plantillas,
                 generador: GeneradorPDF = None) -> None:
        self._colaboradores = repo_colaboradores
        self._contratos = repo_contratos
        self._plantillas = repo_plantillas
        self._generador = generador or GeneradorPDF()
        self._control_acceso = ControlAcceso()

    def generar_contrato(self, id_colaborador: int, id_vinculacion: int,
                         usuario: Usuario) -> Resultado:
        """Genera el contrato de una vinculación (camino feliz C7)."""
        if not self._control_acceso.tiene_rol(usuario, Rol.ADMINISTRATIVO):     # nodo 2
            return ACCESO_NO_AUTORIZADO                                         # C1

        colaborador, vinculacion = self._buscar(id_colaborador, id_vinculacion)
        if vinculacion is None or not colaborador.esta_activo():               # nodo 4
            return Resultado.error("VINCULACION_NO_HABILITADA",
                                   "La vinculación no está habilitada para contrato")  # C2

        faltantes = validar_documentos(colaborador)
        if faltantes:                                                           # nodo 6
            return Resultado.error("DOCUMENTOS_FALTANTES", "Faltan documentos obligatorios",
                                   [tipo.descripcion for tipo in faltantes])    # C3

        if self._contratos.buscar_por_vinculacion(id_vinculacion):              # nodo 8
            return Resultado.error("CONTRATO_EXISTENTE",
                                   "Esta vinculación ya tiene contrato")         # C4

        plantilla = self._plantillas.vigente_para(vinculacion.forma_pago)
        if plantilla is None:                                                   # nodo 10
            return Resultado.error("SIN_PLANTILLA",
                                   "No hay plantilla configurada para esta forma de pago")  # C5

        numero = f"PS-{date.today().year}-{id_vinculacion:04d}"
        try:                                                                    # nodo 12
            titulo, parrafos = self._llenar(plantilla, colaborador, vinculacion, numero)
            pdf = self._generador.generar(titulo, parrafos)
        except ErrorGeneracionPDF as error:                                     # nodo 13
            logger.error("No se pudo generar el contrato %s: %s", numero, error)
            return Resultado.error("ERROR_PDF",
                                   "No se pudo generar el contrato, intente de nuevo")  # C6

        contrato = self._contratos.guardar(Contrato(
            id_colaborador=id_colaborador, id_vinculacion=id_vinculacion, numero=numero,
            proyecto=vinculacion.proyecto, forma_pago=vinculacion.forma_pago, pdf=pdf,
            fecha_generacion=date.today()))
        return Resultado.ok("CONTRATO_GENERADO", "Contrato generado", contrato)  # C7

    def historial(self, id_colaborador: int, usuario: Usuario) -> Resultado:
        """Contratos del colaborador (CDP-28). Lo pueden ver el auxiliar y la dirección."""
        if not self._control_acceso.tiene_alguno(usuario, Rol.ADMINISTRATIVO, Rol.DIRECCION):
            return ACCESO_NO_AUTORIZADO
        if self._colaboradores.buscar_por_id(id_colaborador) is None:
            return Resultado.error("COLABORADOR_NO_ENCONTRADO", "El colaborador no existe")
        return Resultado.ok("HISTORIAL_CONSULTADO", "Historial de contratos",
                            self._contratos.historial(id_colaborador))

    def descargar(self, id_contrato: int, usuario: Usuario) -> Resultado:
        """Devuelve el contrato con su PDF."""
        if not self._control_acceso.tiene_alguno(usuario, Rol.ADMINISTRATIVO, Rol.DIRECCION):
            return ACCESO_NO_AUTORIZADO
        contrato = self._contratos.buscar_por_id(id_contrato)
        if contrato is None:
            return Resultado.error("CONTRATO_NO_ENCONTRADO", "El contrato no existe")
        return Resultado.ok("CONTRATO_ENCONTRADO", "Contrato encontrado", contrato)

    def _buscar(self, id_colaborador: int,
                id_vinculacion: int) -> Tuple[Optional[Colaborador], Optional[Vinculacion]]:
        colaborador = self._colaboradores.buscar_por_id(id_colaborador)
        if colaborador is None:
            return None, None
        vinculacion = next((v for v in colaborador.vinculaciones
                            if v.id_vinculacion == id_vinculacion), None)
        return colaborador, vinculacion

    @staticmethod
    def _llenar(plantilla: PlantillaContrato, colaborador: Colaborador,
                vinculacion: Vinculacion, numero: str):
        """Reemplaza los campos de la plantilla con los datos reales."""
        meses = vinculacion.numero_meses or 1
        campos = {
            "numero": numero, "nombre": colaborador.nombre_completo,
            "cedula": colaborador.numero_documento, "cargo": vinculacion.cargo,
            "proyecto": vinculacion.proyecto, "fecha_inicio": _fecha(vinculacion.fecha_inicio),
            "fecha_fin": _fecha(vinculacion.fecha_fin), "banco": colaborador.banco,
            "cuenta": colaborador.numero_cuenta, "fecha_generacion": _fecha(date.today()),
            "valor_mensual": _pesos(vinculacion.valor_mensual),
            "valor_total": _pesos(vinculacion.valor_total), "numero_meses": meses,
            "cuota": _pesos((vinculacion.valor_total or 0) / meses)
            if vinculacion.forma_pago == FormaPago.VALOR_TOTAL_DIVIDIDO else "",
        }
        return (plantilla.titulo.format(**campos),
                [clausula.format(**campos) for clausula in plantilla.clausulas])
