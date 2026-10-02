"""Contenido demo de joyería para sliders, categorías y catálogo."""

from datetime import date

from app.db.demo_assets import CATEGORY_IMAGES, PRODUCT_IMAGE_BY_SKU, SLIDER_BANNERS
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.models.slider import Slider

DEMO_SLIDER_SPECS = [
    {
        "title": "Elegancia atemporal",
        "subtitle": "Joyería para cada ocasión",
        "cta": "Ver colección",
        "link_suffix": "category/anillos",
        "theme": "dark",
        "sort_order": 1,
    },
    {
        "title": "Aros con luz propia",
        "subtitle": "Piezas para el día y la noche",
        "cta": "Ver aros",
        "link_suffix": "category/aros",
        "theme": "light",
        "sort_order": 2,
    },
]

LEGACY_CATEGORY_NAMES = {
    "Calzado": "Anillos",
    "Ropa": "Aros",
    "Accesorios": "Collares",
}

DEMO_CATEGORY_SPECS = [
    {
        "name": "Anillos",
        "description": "Anillos de oro y piedras para uso diario y ocasiones especiales",
    },
    {
        "name": "Aros",
        "description": "Aros colgantes y argollas con acabado pulido",
    },
    {
        "name": "Collares",
        "description": "Collares y pulseras para completar el look",
    },
]

DEMO_PRODUCT_SPECS = [
    {
        "sku": "ZAP-001",
        "title": "Anillo clásico",
        "description": "Anillo de oro con piedra central, pensado para uso diario.",
        "category": "Anillos",
        "product_type": "simple",
        "variant_mode": None,
        "status": "active",
        "price": 89990,
        "stock": 12,
        "color_images": {},
        "variants": [],
    },
    {
        "sku": "POL-014",
        "title": "Aros de perla",
        "description": "Aros colgantes con perla y cierre de presión.",
        "category": "Aros",
        "product_type": "simple",
        "status": "active",
        "price": 45990,
        "stock": 18,
        "color_images": {},
        "variants": [],
    },
    {
        "sku": "BOL-008",
        "title": "Collar de cadena",
        "description": "Collar fino de eslabones, para llevar solo o en capas.",
        "category": "Collares",
        "product_type": "simple",
        "status": "active",
        "price": 32990,
        "stock": 15,
        "color_images": {},
        "variants": [],
    },
    {
        "sku": "BAL-003",
        "title": "Pulsera eslabón",
        "description": "Pulsera rígida de eslabones con cierre de caja.",
        "category": "Collares",
        "product_type": "simple",
        "status": "active",
        "price": 24990,
        "stock": 24,
        "color_images": {},
        "variants": [],
    },
    {
        "sku": "CAM-022",
        "title": "Anillo solitario",
        "description": "Solitario de piedra clara sobre montura delgada.",
        "category": "Anillos",
        "product_type": "simple",
        "variant_mode": None,
        "status": "active",
        "price": 129990,
        "stock": 8,
        "color_images": {},
        "variants": [],
    },
]


def build_demo_sliders(tenant_id: str) -> list[Slider]:
    sliders = []
    for index, spec in enumerate(DEMO_SLIDER_SPECS):
        sliders.append(
            Slider(
                tenant_id=tenant_id,
                title=spec["title"],
                subtitle=spec["subtitle"],
                cta=spec["cta"],
                link_suffix=spec["link_suffix"],
                image_url=SLIDER_BANNERS[index % len(SLIDER_BANNERS)],
                theme=spec["theme"],
                sort_order=spec["sort_order"],
                status="active",
            )
        )
    return sliders


def build_demo_categories(tenant_id: str) -> list[Category]:
    created_at = date(2025, 10, 1)
    categories = []
    for index, spec in enumerate(DEMO_CATEGORY_SPECS):
        categories.append(
            Category(
                tenant_id=tenant_id,
                name=spec["name"],
                description=spec["description"],
                image_url=CATEGORY_IMAGES[index % len(CATEGORY_IMAGES)],
                status="active",
                created_at=created_at,
            )
        )
    return categories


def build_catalog_product(tenant_id: str, spec: dict) -> CatalogProduct:
    image = PRODUCT_IMAGE_BY_SKU.get(spec["sku"], "")
    return CatalogProduct(
        tenant_id=tenant_id,
        sku=spec["sku"],
        title=spec["title"],
        description=spec["description"],
        category=spec["category"],
        product_type=spec["product_type"],
        variant_mode=spec.get("variant_mode"),
        status=spec["status"],
        price=spec.get("price", 0),
        stock=spec.get("stock", 0),
        images=[image] if image else [],
        color_images=spec.get("color_images", {}),
        variants=spec.get("variants", []),
    )
