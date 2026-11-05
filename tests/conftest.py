"""Datos de prueba reutilizables (fixtures) para las pruebas de HU-01."""
from datetime import date
from decimal import Decimal

import importlib.util

import pytest

from app.dominio.entidades import FormaPago, Rol, Usuario
from app.persistencia.repositorio_colaborador import RepositorioColaboradorMemoria
from app.servicios.servicio_colaborador import ServicioColaborador

# Las pruebas de Playwright (RTF4) necesitan requirements-funcionales.txt. Si no está
# instalado, pytest ni siquiera las importa; así el `pytest` normal funciona solo con
# requirements-dev.txt.
collect_ignore_glob = [] if importlib.util.find_spec("playwright") else ["funcionales/e2e/*"]


@pytest.fixture
def auxiliar():
    """Usuario con rol ADMINISTRATIVO (el auxiliar administrativo)."""
    return Usuario(id_usuario=1, nombre="Auxiliar administrativo", rol=Rol.ADMINISTRATIVO)


@pytest.fixture
def direccion():
    """Usuario de la gerencia, solo puede consultar."""
    return Usuario(id_usuario=2, nombre="Gerencia", rol=Rol.DIRECCION)


@pytest.fixture
def repositorio():
    """Repositorio vacío para cada prueba."""
    return RepositorioColaboradorMemoria()


@pytest.fixture
def servicio(repositorio):
    """Servicio de HU-01 conectado al repositorio en memoria."""
    return ServicioColaborador(repositorio)


@pytest.fixture
def datos_validos():
    """Datos completos de un colaborador con honorario mensual (camino C7)."""
    return {
        "nombre_completo": "Laura Gómez",
        "numero_documento": "1037654321",
        "correo": "laura.gomez@correo.com",
        "banco": "Bancolombia",
        "numero_cuenta": "12345678901",
        "proyecto": "Soy Digital",
        "cargo": "Analista de datos",
        "fecha_inicio": date(2026, 10, 1),
        "fecha_fin": date(2026, 12, 31),
        "forma_pago": FormaPago.HONORARIO_MENSUAL,
        "valor_mensual": Decimal("3000000"),
    }
