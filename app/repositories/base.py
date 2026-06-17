"""Repository pattern — acceso a datos por tenant."""

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session, tenant_id: str | None = None):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        query = self.db.query(self.model)
        if self.tenant_id and hasattr(self.model, "tenant_id"):
            query = query.filter(self.model.tenant_id == self.tenant_id)
        return query

    def list_all(self, order_by=None) -> list[ModelT]:
        query = self._base_query()
        if order_by is not None:
            if isinstance(order_by, tuple):
                query = query.order_by(*order_by)
            else:
                query = query.order_by(order_by)
        return query.all()

    def get_by_id(self, entity_id: str) -> ModelT:
        entity = self._base_query().filter(self.model.id == entity_id).first()
        if entity is None:
            raise NotFoundError(f"{self.model.__name__} no encontrado")
        return entity

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity: ModelT) -> ModelT:
        self.db.refresh(entity)
        return entity
