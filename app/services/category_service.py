from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.repositories.base import BaseRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.base import BaseService


class CategoryRepository(BaseRepository[Category]):
    model = Category


class CategoryService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = CategoryRepository(db, tenant_id=tenant_id)

    def list_categories(self) -> list[Category]:
        return self.repo.list_all(order_by=Category.name)

    def get_category(self, category_id: str) -> Category:
        return self.repo.get_by_id(category_id)

    def create_category(self, payload: CategoryCreate) -> Category:
        category = Category(
            tenant_id=self.repo.tenant_id,
            name=payload.name.strip(),
            description=payload.description,
            image_url=(payload.image_url or "").strip(),
            status=payload.status,
            created_at=date.today(),
        )
        self.repo.add(category)
        self.commit()
        return self.repo.refresh(category)

    def update_category(self, category_id: str, payload: CategoryUpdate) -> Category:
        category = self.repo.get_by_id(category_id)
        old_name = category.name
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, field, value)

        if payload.name and payload.name != old_name:
            products = (
                self.db.query(CatalogProduct)
                .filter(
                    CatalogProduct.tenant_id == self.repo.tenant_id,
                    CatalogProduct.category == old_name,
                )
                .all()
            )
            for product in products:
                product.category = payload.name

        self.commit()
        return self.repo.refresh(category)

    def delete_category(self, category_id: str) -> None:
        category = self.repo.get_by_id(category_id)
        count = (
            self.db.query(CatalogProduct)
            .filter(
                CatalogProduct.tenant_id == self.repo.tenant_id,
                CatalogProduct.category == category.name,
            )
            .count()
        )
        if count > 0:
            raise AppError("La categoría tiene productos asociados")

        self.repo.delete(category)
        self.commit()
