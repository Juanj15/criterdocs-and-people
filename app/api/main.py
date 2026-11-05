"""API de CriterDocs and People - HU-01 (registro, edición, consulta y estado).

Mientras no exista el inicio de sesión (sprint futuro), el rol del usuario se
envía en el encabezado X-Rol para poder probar el control de acceso.
"""
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.dominio.entidades import Colaborador, EstadoColaborador, FormaPago, Rol, Usuario
from app.persistencia.repositorio_colaborador import RepositorioColaboradorMemoria
from app.servicios.servicio_colaborador import ServicioColaborador

app = FastAPI(title="CriterDocs and People", version="0.1.0")
servicio = ServicioColaborador(RepositorioColaboradorMemoria())
FORMULARIO = Path(__file__).resolve().parent.parent / "web" / "registro.html"

CODIGOS_HTTP = {
    "COLABORADOR_REGISTRADO": 201,
    "ACCESO_NO_AUTORIZADO": 403,
    "CAMPOS_FALTANTES": 422,
    "DATOS_INVALIDOS": 422,
    "COLABORADOR_EXISTENTE": 409,
    "ERROR_GUARDADO": 500,
    "COLABORADOR_ACTUALIZADO": 200,
    "VINCULACION_AGREGADA": 201,
    "COLABORADOR_NO_ENCONTRADO": 404,
    "COLABORADOR_INACTIVO": 409,
    "VINCULACION_DUPLICADA": 409,
    "COLABORADOR_ENCONTRADO": 200,
    "ESTADO_ACTUALIZADO": 200,
    "ESTADO_SIN_CAMBIO": 409,
}


class SolicitudEdicion(BaseModel):
    """Datos personales o bancarios que se quieren cambiar."""
    nombre_completo: Optional[str] = None
    numero_documento: Optional[str] = None
    correo: Optional[str] = None
    banco: Optional[str] = None
    numero_cuenta: Optional[str] = None


class SolicitudVinculacion(BaseModel):
    """Nuevo proyecto para un colaborador existente."""
    proyecto: Optional[str] = None
    cargo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    forma_pago: Optional[FormaPago] = None
    valor_mensual: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None
    numero_meses: Optional[int] = None


class SolicitudEstado(BaseModel):
    """Nuevo estado del colaborador: ACTIVO o INACTIVO."""
    estado: Optional[EstadoColaborador] = None


class SolicitudRegistro(BaseModel):
    """Datos que llegan desde el formulario de registro."""
    nombre_completo: Optional[str] = None
    numero_documento: Optional[str] = None
    correo: Optional[str] = None
    banco: Optional[str] = None
    numero_cuenta: Optional[str] = None
    proyecto: Optional[str] = None
    cargo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    forma_pago: Optional[FormaPago] = None
    valor_mensual: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None
    numero_meses: Optional[int] = None


def _usuario(x_rol: str) -> Usuario:
    """Usuario simulado a partir del encabezado X-Rol (mientras no hay login).

    Si el encabezado no llega o no es un rol conocido, el usuario queda sin rol.
    Antes cualquier valor se tomaba como DIRECCION (hallazgo de caja negra, CDP-43).
    """
    try:
        rol = Rol(x_rol)
    except ValueError:
        rol = None
    return Usuario(id_usuario=0, nombre="usuario de prueba", rol=rol)


def _ficha(colaborador: Colaborador) -> dict:
    """Datos que se muestran al consultar; la cuenta bancaria va enmascarada."""
    cuenta = colaborador.numero_cuenta
    return {
        "id_colaborador": colaborador.id_colaborador,
        "nombre_completo": colaborador.nombre_completo,
        "numero_documento": colaborador.numero_documento,
        "correo": colaborador.correo,
        "banco": colaborador.banco,
        "numero_cuenta": "*" * (len(cuenta) - 4) + cuenta[-4:],
        "estado": colaborador.estado.value,
        "vinculaciones": [{
            "proyecto": v.proyecto,
            "cargo": v.cargo,
            "fecha_inicio": v.fecha_inicio.isoformat(),
            "fecha_fin": v.fecha_fin.isoformat(),
            "forma_pago": v.forma_pago.value,
        } for v in colaborador.vinculaciones],
    }


def _respuesta(resultado) -> JSONResponse:
    cuerpo = {"codigo": resultado.codigo, "mensaje": resultado.mensaje,
              "detalle": resultado.detalle}
    if resultado.exito:
        cuerpo["id_colaborador"] = resultado.datos.id_colaborador
    if resultado.codigo == "COLABORADOR_ENCONTRADO":
        cuerpo["colaborador"] = _ficha(resultado.datos)
    return JSONResponse(status_code=CODIGOS_HTTP[resultado.codigo], content=cuerpo)


@app.get("/", response_class=HTMLResponse)
def formulario_registro():
    """Formulario web de registro de colaboradores (CDP-21)."""
    return FORMULARIO.read_text(encoding="utf-8")


@app.post("/colaboradores")
def registrar_colaborador(solicitud: SolicitudRegistro, x_rol: str = Header(default="")):
    """Registra un colaborador con su primera vinculación (HU-01)."""
    return _respuesta(servicio.registrar(solicitud.model_dump(), _usuario(x_rol)))


@app.patch("/colaboradores/{id_colaborador}")
def editar_colaborador(id_colaborador: int, solicitud: SolicitudEdicion,
                       x_rol: str = Header(default="")):
    """Edita los datos personales o bancarios de un colaborador (RF-03)."""
    cambios = solicitud.model_dump(exclude_unset=True)
    return _respuesta(servicio.editar(id_colaborador, cambios, _usuario(x_rol)))


@app.post("/colaboradores/{id_colaborador}/vinculaciones")
def agregar_vinculacion(id_colaborador: int, solicitud: SolicitudVinculacion,
                        x_rol: str = Header(default="")):
    """Agrega un nuevo proyecto a un colaborador existente."""
    return _respuesta(servicio.agregar_vinculacion(id_colaborador, solicitud.model_dump(),
                                                   _usuario(x_rol)))


@app.get("/colaboradores/{id_colaborador}")
def consultar_colaborador(id_colaborador: int, x_rol: str = Header(default="")):
    """Consulta un colaborador con sus proyectos (CDP-43)."""
    return _respuesta(servicio.consultar(id_colaborador, _usuario(x_rol)))


@app.patch("/colaboradores/{id_colaborador}/estado")
def cambiar_estado(id_colaborador: int, solicitud: SolicitudEstado,
                   x_rol: str = Header(default="")):
    """Activa o desactiva un colaborador (RF-04, CDP-43)."""
    if solicitud.estado is None:
        return JSONResponse(status_code=422, content={
            "codigo": "CAMPOS_FALTANTES", "mensaje": "Faltan campos obligatorios",
            "detalle": ["estado"]})
    return _respuesta(servicio.cambiar_estado(id_colaborador, solicitud.estado,
                                              _usuario(x_rol)))
