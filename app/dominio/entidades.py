"""Entidades del dominio usadas por la HU-01.

Siguen el diagrama de clases de la RTF3: el colaborador guarda los datos
personales y bancarios, y cada vinculación representa un proyecto con sus
fechas, forma de pago y valores. Un colaborador puede tener varias vinculaciones.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class Rol(Enum):
    """Roles de los usuarios del sistema."""
    ADMINISTRATIVO = "ADMINISTRATIVO"
    DIRECCION = "DIRECCION"


class EstadoColaborador(Enum):
    """Estado del colaborador dentro de Critertec."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class FormaPago(Enum):
    """Forma de pago pactada en cada proyecto."""
    HONORARIO_MENSUAL = "HONORARIO_MENSUAL"
    VALOR_TOTAL_DIVIDIDO = "VALOR_TOTAL_DIVIDIDO"


@dataclass
class Usuario:
    """Persona que usa el sistema (por ahora, el auxiliar administrativo o la dirección)."""
    id_usuario: int
    nombre: str
    rol: Rol


@dataclass
class Vinculacion:
    """Un proyecto en el que participa el colaborador."""
    proyecto: str
    cargo: str
    fecha_inicio: date
    fecha_fin: date
    forma_pago: FormaPago
    valor_mensual: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None
    numero_meses: Optional[int] = None
    id_vinculacion: Optional[int] = None


@dataclass
class Colaborador:
    """Persona vinculada por prestación de servicios."""
    nombre_completo: str
    numero_documento: str
    correo: str
    banco: str
    numero_cuenta: str
    estado: EstadoColaborador = EstadoColaborador.ACTIVO
    vinculaciones: List[Vinculacion] = field(default_factory=list)
    id_colaborador: Optional[int] = None
