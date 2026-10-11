"""API de CriterDocs and People - incremento del Sprint 1 (HU-01).

Mientras no exista el inicio de sesión (sprint futuro), el rol del usuario se
envía en el encabezado X-Rol para poder probar el control de acceso.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.dominio.entidades import FormaPago, Rol, Usuario
from app.persistencia.repositorio_colaborador import RepositorioColaboradorMemoria
from app.servicios.servicio_colaborador import ServicioColaborador

app = FastAPI(title="CriterDocs and People", version="0.1.0")
servicio = ServicioColaborador(RepositorioColaboradorMemoria())

CODIGOS_HTTP = {
    "COLABORADOR_REGISTRADO": 201,
    "ACCESO_NO_AUTORIZADO": 403,
    "CAMPOS_FALTANTES": 422,
    "DATOS_INVALIDOS": 422,
    "COLABORADOR_EXISTENTE": 409,
    "ERROR_GUARDADO": 500,
}


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


@app.post("/colaboradores")
def registrar_colaborador(solicitud: SolicitudRegistro, x_rol: str = Header(default="")):
    """Registra un colaborador con su primera vinculación (HU-01)."""
    rol = Rol.ADMINISTRATIVO if x_rol == Rol.ADMINISTRATIVO.value else Rol.DIRECCION
    usuario = Usuario(id_usuario=0, nombre="usuario de prueba", rol=rol)
    resultado = servicio.registrar(solicitud.model_dump(), usuario)
    cuerpo = {"codigo": resultado.codigo, "mensaje": resultado.mensaje,
              "detalle": resultado.detalle}
    if resultado.exito:
        cuerpo["id_colaborador"] = resultado.datos.id_colaborador
    return JSONResponse(status_code=CODIGOS_HTTP[resultado.codigo], content=cuerpo)
