"""Repositorio de colaboradores.

Para el Sprint 1 se guarda en memoria; en un sprint siguiente se cambia por
una base de datos sin tocar el servicio, porque el servicio solo conoce esta
interfaz.
"""
import copy
from typing import Dict, Optional

from app.dominio.entidades import Colaborador


class ErrorPersistencia(Exception):
    """Error al leer o escribir datos (por ejemplo, se cae la conexión)."""


class RepositorioColaboradorMemoria:
    """Implementación en memoria del repositorio de colaboradores."""

    def __init__(self) -> None:
        self._colaboradores: Dict[int, Colaborador] = {}
        self._siguiente_id = 1

    def existe_documento(self, numero_documento: str,
                         excluir_id: Optional[int] = None) -> bool:
        """Indica si ya hay un colaborador con esa cédula (sin contar a excluir_id)."""
        return any(c.numero_documento == numero_documento and c.id_colaborador != excluir_id
                   for c in self._colaboradores.values())

    def guardar(self, colaborador: Colaborador) -> Colaborador:
        """Guarda un colaborador nuevo o actualiza uno existente."""
        guardado = copy.deepcopy(colaborador)
        if guardado.id_colaborador is None:
            guardado.id_colaborador = self._siguiente_id
            self._siguiente_id += 1
        self._colaboradores[guardado.id_colaborador] = guardado
        return copy.deepcopy(guardado)

    def buscar_por_id(self, id_colaborador: int) -> Optional[Colaborador]:
        """Devuelve el colaborador o None si no existe."""
        encontrado = self._colaboradores.get(id_colaborador)
        return copy.deepcopy(encontrado) if encontrado else None

    def contar(self) -> int:
        """Cantidad de colaboradores guardados (útil en pruebas)."""
        return len(self._colaboradores)
