"""Ejemplo Service + Repository para catálogo. Usar como referencia al crear módulos."""

from sqlalchemy.orm import Session

from app.models.catalog import CatalogProduct
from app.repositories.base import BaseRepository
from app.schemas.catalog import CatalogProductCreate, CatalogProductUpdate
from app.services.base import BaseService
from app.utils.catalog import normalize_catalog_payload


class CatalogRepository(BaseRepository[CatalogProduct]):
    model = CatalogProduct


class CatalogService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = CatalogRepository(db, tenant_id=tenant_id)

    def list_products(self) -> list[CatalogProduct]:
        return self.repo.list_all(order_by=CatalogProduct.created_at.desc())

    def get_product(self, product_id: str) -> CatalogProduct:
        return self.repo.get_by_id(product_id)

    def create_product(self, payload: CatalogProductCreate) -> CatalogProduct:
        data = normalize_catalog_payload(payload.model_dump())
        product = CatalogProduct(tenant_id=self.repo.tenant_id, **data)
        self.repo.add(product)
        self.commit()
        return self.repo.refresh(product)

    def update_product(
        self, product_id: str, payload: CatalogProductUpdate
    ) -> CatalogProduct:
        product = self.repo.get_by_id(product_id)
        current = {
            "sku": product.sku,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "product_type": product.product_type,
            "status": product.status,
            "price": product.price,
            "stock": product.stock,
            "images": product.images,
            "color_images": product.color_images,
            "variants": product.variants,
            "variant_mode": product.variant_mode,
        }
        data = normalize_catalog_payload({**current, **payload.model_dump(exclude_unset=True)})
        for field in data:
            setattr(product, field, data[field])
        self.commit()
        return self.repo.refresh(product)

    def delete_product(self, product_id: str) -> None:
        product = self.repo.get_by_id(product_id)
        self.repo.delete(product)
        self.commit()
