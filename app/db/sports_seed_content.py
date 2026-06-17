"""Contenido demo deportivo para sliders, categorías y catálogo."""

from datetime import date

from app.db.demo_assets import CATEGORY_IMAGES, PRODUCT_IMAGE_BY_SKU, SLIDER_BANNERS
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.models.slider import Slider

DEMO_SLIDER_SPECS = [
    {
        "title": "RUNNING",
        "subtitle": "Calzado ligero para tu próximo entreno",
        "cta": "Ver calzado",
        "link_suffix": "category/calzado",
        "theme": "dark",
        "sort_order": 1,
    },
    {
        "title": "BASKETBALL",
        "subtitle": "Ropa y accesorios para dominar la cancha",
        "cta": "Ver ropa deportiva",
        "link_suffix": "category/ropa",
        "theme": "light",
        "sort_order": 2,
    },
]

DEMO_CATEGORY_SPECS = [
    {
        "name": "Calzado",
        "description": "Zapatillas de running, training y deportes outdoor",
    },
    {
        "name": "Ropa",
        "description": "Polerones, camisetas y shorts para entrenar",
    },
    {
        "name": "Accesorios",
        "description": "Mochilas, balones y equipamiento deportivo",
    },
]

DEMO_PRODUCT_SPECS = [
    {
        "sku": "ZAP-001",
        "title": "Zapatillas Running Pro",
        "description": "Amortiguación reactiva para running y entrenamiento en ciudad.",
        "category": "Calzado",
        "product_type": "size_color",
        "variant_mode": "size_color",
        "status": "active",
        "price": 0,
        "stock": 42,
        "color_images": {"#111827": [], "#f9fafb": []},
        "variants": [
            {
                "id": "var-1",
                "sku": "ZAP-001-40-BLK",
                "size": "40",
                "color": "#111827",
                "price": 89990,
                "stock": 12,
            },
            {
                "id": "var-2",
                "sku": "ZAP-001-42-BLK",
                "size": "42",
                "color": "#111827",
                "price": 89990,
                "stock": 18,
            },
            {
                "id": "var-3",
                "sku": "ZAP-001-42-WHT",
                "size": "42",
                "color": "#f9fafb",
                "price": 89990,
                "stock": 12,
            },
        ],
    },
    {
        "sku": "POL-014",
        "title": "Polerón Training Fit",
        "description": "Polerón deportivo transpirable ideal para gym y running.",
        "category": "Ropa",
        "product_type": "simple",
        "status": "active",
        "price": 45990,
        "stock": 18,
        "color_images": {},
        "variants": [],
    },
    {
        "sku": "BOL-008",
        "title": "Mochila Gym Sport",
        "description": "Mochila deportiva con compartimento para zapatillas y botella.",
        "category": "Accesorios",
        "product_type": "simple",
        "status": "active",
        "price": 32990,
        "stock": 15,
        "color_images": {},
        "variants": [],
    },
    {
        "sku": "BAL-003",
        "title": "Balón Fútbol Pro",
        "description": "Balón de fútbol Nº5 para entrenamiento y partidos amateur.",
        "category": "Accesorios",
        "product_type": "simple",
        "status": "active",
        "price": 24990,
        "stock": 24,
        "color_images": {},
        "variants": [],
    },
    {
        "sku": "CAM-022",
        "title": "Camiseta Dry-Fit Running",
        "description": "Camiseta deportiva de secado rápido para alto rendimiento.",
        "category": "Ropa",
        "product_type": "size",
        "variant_mode": "size",
        "status": "active",
        "price": 0,
        "stock": 30,
        "color_images": {},
        "variants": [
            {
                "id": "var-cam-s",
                "sku": "CAM-022-S",
                "size": "S",
                "price": 19990,
                "stock": 8,
            },
            {
                "id": "var-cam-m",
                "sku": "CAM-022-M",
                "size": "M",
                "price": 19990,
                "stock": 12,
            },
            {
                "id": "var-cam-l",
                "sku": "CAM-022-L",
                "size": "L",
                "price": 19990,
                "stock": 10,
            },
        ],
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
