"""Control de acceso por rol (RNF-03)."""
from app.dominio.entidades import Rol, Usuario


class ControlAcceso:
    """Verifica que un usuario tenga el rol necesario para una operación."""

    def tiene_rol(self, usuario: Usuario, rol: Rol) -> bool:
        """Devuelve True solo si el usuario existe y tiene el rol pedido."""
        return usuario is not None and usuario.rol == rol
