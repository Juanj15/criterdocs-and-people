"""Plantillas de contrato (HU-02): una por forma de pago.

El texto es un contrato de prestación de servicios genérico. Los campos entre
llaves se reemplazan con los datos del colaborador y de la vinculación.
"""
import copy
from typing import Dict, Optional

from app.dominio.entidades import FormaPago, PlantillaContrato

_INICIO = [
    "Entre CRITERTEC, que en adelante se llamará EL CONTRATANTE, y {nombre}, identificado(a) "
    "con cédula de ciudadanía n.° {cedula}, que en adelante se llamará EL CONTRATISTA, se "
    "celebra el presente contrato de prestación de servicios, que se rige por las siguientes "
    "cláusulas:",
    "PRIMERA. OBJETO. EL CONTRATISTA prestará sus servicios como {cargo} en el proyecto "
    "{proyecto}, con autonomía técnica y administrativa.",
    "SEGUNDA. PLAZO. El contrato va del {fecha_inicio} al {fecha_fin}.",
]
_FINAL = [
    "CUARTA. OBLIGACIONES DEL CONTRATISTA. Cumplir el objeto del contrato y presentar cada "
    "mes su cuenta de cobro junto con la planilla de pago de seguridad social.",
    "QUINTA. NATURALEZA DEL CONTRATO. Este contrato no genera relación laboral entre las "
    "partes.",
    "SEXTA. DOCUMENTOS. Hacen parte de este contrato la cédula, la certificación bancaria, "
    "el RUT y la hoja de vida con sus soportes. El pago se consignará en la cuenta n.° "
    "{cuenta} del banco {banco}.",
    "Para constancia se firma en Medellín el {fecha_generacion}.",
    "EL CONTRATANTE: ______________________________",
    "EL CONTRATISTA: ______________________________",
]

PLANTILLAS_BASE = {
    FormaPago.HONORARIO_MENSUAL: PlantillaContrato(
        forma_pago=FormaPago.HONORARIO_MENSUAL,
        titulo="CONTRATO DE PRESTACIÓN DE SERVICIOS N.° {numero}",
        clausulas=_INICIO + [
            "TERCERA. VALOR Y FORMA DE PAGO. EL CONTRATANTE pagará un honorario mensual de "
            "${valor_mensual}. Las cuentas de cobro se reciben con corte al día 25 de cada mes y, "
            "si el servicio inicia o termina dentro del mes, el pago es proporcional a los días.",
        ] + _FINAL),
    FormaPago.VALOR_TOTAL_DIVIDIDO: PlantillaContrato(
        forma_pago=FormaPago.VALOR_TOTAL_DIVIDIDO,
        titulo="CONTRATO DE PRESTACIÓN DE SERVICIOS N.° {numero}",
        clausulas=_INICIO + [
            "TERCERA. VALOR Y FORMA DE PAGO. El valor total del contrato es de ${valor_total}, "
            "que se pagará en {numero_meses} cuotas mensuales de ${cuota}, previa presentación "
            "de la cuenta de cobro con corte al día 25 de cada mes.",
        ] + _FINAL),
}


class RepositorioPlantillaMemoria:
    """Plantillas disponibles para generar contratos."""

    def __init__(self) -> None:
        self._plantillas: Dict[FormaPago, PlantillaContrato] = copy.deepcopy(PLANTILLAS_BASE)

    def vigente_para(self, forma_pago: FormaPago) -> Optional[PlantillaContrato]:
        """Plantilla vigente para la forma de pago, o None si no hay."""
        plantilla = self._plantillas.get(forma_pago)
        return copy.deepcopy(plantilla) if plantilla and plantilla.vigente else None

    def desactivar(self, forma_pago: FormaPago) -> None:
        """Deja la plantilla sin vigencia (por ejemplo, mientras se actualiza el texto)."""
        self._plantillas[forma_pago].vigente = False
