"""Entidades del dominio usadas por la HU-01 y la HU-02.

Siguen el diagrama de clases de la RTF3: el colaborador guarda los datos
personales y bancarios, y cada vinculación representa un proyecto con sus
fechas, forma de pago y valores. Un colaborador puede tener varias vinculaciones.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional


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


class TipoDocumento(Enum):
    """Los cuatro documentos que Critertec exige antes de hacer un contrato (HU-02)."""
    CEDULA = "CEDULA"
    CERTIFICACION_BANCARIA = "CERTIFICACION_BANCARIA"
    RUT = "RUT"
    HOJA_DE_VIDA = "HOJA_DE_VIDA"

    @property
    def descripcion(self) -> str:
        """Nombre que ve el usuario."""
        return {
            "CEDULA": "Cédula",
            "CERTIFICACION_BANCARIA": "Certificación bancaria",
            "RUT": "RUT",
            "HOJA_DE_VIDA": "Hoja de vida con soportes",
        }[self.value]


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

    def se_cruza_con(self, otra: "Vinculacion") -> bool:
        """True si es el mismo proyecto y los periodos se traslapan."""
        return (self.proyecto.lower() == otra.proyecto.lower()
                and self.fecha_inicio <= otra.fecha_fin
                and otra.fecha_inicio <= self.fecha_fin)


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
    documentos: Dict[TipoDocumento, "DocumentoSoporte"] = field(default_factory=dict)

    def esta_activo(self) -> bool:
        """Indica si el colaborador puede recibir nuevas vinculaciones y contratos."""
        return self.estado == EstadoColaborador.ACTIVO


@dataclass
class DocumentoSoporte:
    """Archivo PDF que soporta la contratación (cédula, RUT, etc.)."""
    tipo: TipoDocumento
    nombre_archivo: str
    contenido: bytes
    fecha_carga: date


@dataclass
class PlantillaContrato:
    """Texto base del contrato; hay una por forma de pago."""
    forma_pago: FormaPago
    titulo: str
    clausulas: List[str]
    vigente: bool = True


@dataclass
class Contrato:
    """Contrato generado para una vinculación (un contrato por proyecto)."""
    id_colaborador: int
    id_vinculacion: int
    numero: str
    proyecto: str
    forma_pago: FormaPago
    pdf: bytes
    fecha_generacion: date
    id_contrato: Optional[int] = None

    @property
    def nombre_archivo(self) -> str:
        """Nombre con el que se descarga el PDF."""
        return f"contrato_{self.numero}.pdf"
