"""Service layer — reglas de negocio."""

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

from app.core.exceptions import AppError

T = TypeVar("T")


class BaseService:
    """Clase base para servicios con sesión de BD."""

    def __init__(self, db: Session):
        self.db = db

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def run(self, action: Callable[[], T]) -> T:
        """Ejecuta acción con commit; rollback en AppError."""
        try:
            result = action()
            self.commit()
            return result
        except AppError:
            self.rollback()
            raise
