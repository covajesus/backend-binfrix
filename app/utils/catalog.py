VARIANT_TYPES = {"size", "color", "size_color"}


def resolve_product_type(product_type: str | None, variant_mode: str | None = None) -> str:
    if product_type == "variable":
        return variant_mode or "size_color"
    return product_type or "simple"


def is_simple_product(product_type: str) -> bool:
    return resolve_product_type(product_type) == "simple"


def is_variable_product(product_type: str) -> bool:
    return not is_simple_product(product_type)


def uses_color_images(product_type: str) -> bool:
    resolved = resolve_product_type(product_type)
    return resolved in {"color", "size_color"}


def normalize_catalog_payload(data: dict) -> dict:
    product_type = resolve_product_type(data.get("product_type"), data.get("variant_mode"))
    variants = data.get("variants") or []
    images = [img for img in (data.get("images") or []) if img]
    color_images = data.get("color_images") or {}

    if is_simple_product(product_type):
        return {
            **data,
            "product_type": "simple",
            "variant_mode": None,
            "price": int(data.get("price") or 0),
            "stock": int(data.get("stock") or 0),
            "variants": [],
            "color_images": {},
            "images": images,
        }

    total_stock = sum(int(v.get("stock") or 0) for v in variants)
    return {
        **data,
        "product_type": product_type,
        "variant_mode": product_type,
        "price": 0,
        "stock": total_stock,
        "variants": variants,
        "color_images": color_images if uses_color_images(product_type) else {},
        "images": images if not uses_color_images(product_type) else [],
    }


def get_display_price(product: dict) -> int:
    if is_variable_product(product.get("product_type", "simple")):
        prices = [
            int(v.get("price") or 0)
            for v in (product.get("variants") or [])
            if int(v.get("price") or 0) > 0
        ]
        return min(prices) if prices else 0
    return int(product.get("price") or 0)


def get_total_stock(product: dict) -> int:
    if is_variable_product(product.get("product_type", "simple")):
        return sum(int(v.get("stock") or 0) for v in (product.get("variants") or []))
    return int(product.get("stock") or 0)
