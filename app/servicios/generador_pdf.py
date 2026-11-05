"""Generador de PDF (HU-02).

Está separado de ServicioContrato, como en el diagrama de clases de la RTF3,
para poder reemplazarlo en las pruebas por uno que falle a propósito (camino C6).
"""
from typing import List

from fpdf import FPDF
from fpdf.errors import FPDFException


class ErrorGeneracionPDF(Exception):
    """No se pudo crear el PDF."""


class GeneradorPDF:
    """Convierte un título y sus párrafos en un PDF tamaño carta."""

    def generar(self, titulo: str, parrafos: List[str]) -> bytes:
        """Devuelve los bytes del PDF o lanza ErrorGeneracionPDF."""
        try:
            pdf = FPDF(format="Letter")
            pdf.set_compression(False)   # el texto queda legible dentro del archivo
            pdf.set_margins(25, 25, 25)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 8, titulo, align="C")
            pdf.ln(4)
            pdf.set_font("Helvetica", size=11)
            for parrafo in parrafos:
                pdf.multi_cell(0, 6, parrafo, align="J")
                pdf.ln(3)
            return bytes(pdf.output())
        except (FPDFException, UnicodeEncodeError) as error:
            raise ErrorGeneracionPDF(str(error)) from error
