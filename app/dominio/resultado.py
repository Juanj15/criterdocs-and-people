"""Respuesta común de los servicios.

Cada camino del grafo de flujo de la RTF3 termina en un Resultado con un
código distinto, así las pruebas pueden saber exactamente por dónde pasó.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Resultado:
    """Resultado de una operación de servicio."""
    exito: bool
    codigo: str
    mensaje: str
    detalle: List[str] = field(default_factory=list)
    datos: Optional[Any] = None

    @classmethod
    def ok(cls, codigo: str, mensaje: str, datos: Any = None) -> "Resultado":
        """Crea un resultado exitoso."""
        return cls(exito=True, codigo=codigo, mensaje=mensaje, datos=datos)

    @classmethod
    def error(cls, codigo: str, mensaje: str, detalle: Optional[List[str]] = None) -> "Resultado":
        """Crea un resultado de error."""
        return cls(exito=False, codigo=codigo, mensaje=mensaje, detalle=detalle or [])
