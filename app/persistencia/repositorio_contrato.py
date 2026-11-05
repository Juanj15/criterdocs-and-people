"""Repositorio de contratos (HU-02). En memoria, igual que el de colaboradores."""
import copy
from typing import Dict, List, Optional

from app.dominio.entidades import Contrato


class RepositorioContratoMemoria:
    """Guarda los contratos generados y arma el historial de cada colaborador."""

    def __init__(self) -> None:
        self._contratos: Dict[int, Contrato] = {}
        self._siguiente_id = 1

    def guardar(self, contrato: Contrato) -> Contrato:
        """Guarda un contrato nuevo y le asigna su id."""
        guardado = copy.deepcopy(contrato)
        guardado.id_contrato = self._siguiente_id
        self._siguiente_id += 1
        self._contratos[guardado.id_contrato] = guardado
        return copy.deepcopy(guardado)

    def buscar_por_id(self, id_contrato: int) -> Optional[Contrato]:
        """Devuelve el contrato o None."""
        encontrado = self._contratos.get(id_contrato)
        return copy.deepcopy(encontrado) if encontrado else None

    def buscar_por_vinculacion(self, id_vinculacion: int) -> Optional[Contrato]:
        """Contrato de una vinculación, si ya se generó."""
        for contrato in self._contratos.values():
            if contrato.id_vinculacion == id_vinculacion:
                return copy.deepcopy(contrato)
        return None

    def historial(self, id_colaborador: int) -> List[Contrato]:
        """Contratos de un colaborador en el orden en que se generaron."""
        return [copy.deepcopy(c) for c in self._contratos.values()
                if c.id_colaborador == id_colaborador]
