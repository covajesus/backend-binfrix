from app.data.platform_catalog import PLATFORM_PRODUCTS
from app.schemas.product import ProductOut

BINFRIX_PRODUCTS: list[ProductOut] = [
    ProductOut(id=product_id, name=name, description=description)
    for product_id, name, description in PLATFORM_PRODUCTS
]


def get_product_by_id(product_id: str) -> ProductOut | None:
    for product in BINFRIX_PRODUCTS:
        if product.id == product_id:
            return product
    return None
