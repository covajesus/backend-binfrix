"""Imágenes demo deportivas (Unsplash — calzado, ropa y equipamiento)."""


def unsplash(photo_id: str, width: int, height: int) -> str:
    path = photo_id if photo_id.startswith("photo-") else f"photo-{photo_id}"
    return (
        f"https://images.unsplash.com/{path}"
        f"?auto=format&fit=crop&w={width}&h={height}&q=80"
    )


# Sliders: running / basketball
SLIDER_BANNER_RUNNING = unsplash("photo-1476480862126-209bfaa8edc8", 1600, 900)
SLIDER_BANNER_BASKETBALL = unsplash("photo-1546519638-68e109498ffc", 1600, 900)

SLIDER_BANNERS = [SLIDER_BANNER_RUNNING, SLIDER_BANNER_BASKETBALL]

# Categorías: calzado, ropa, accesorios
CATEGORY_IMAGE_SHOES = unsplash("photo-1542291026-7eec264c27ff", 800, 1000)
CATEGORY_IMAGE_APPAREL = unsplash("photo-1571019614242-c5c5dee9f50b", 800, 1000)
CATEGORY_IMAGE_ACCESSORIES = unsplash("photo-1591047139829-d91aecb6caea", 800, 1000)

CATEGORY_IMAGES = [
    CATEGORY_IMAGE_SHOES,
    CATEGORY_IMAGE_APPAREL,
    CATEGORY_IMAGE_ACCESSORIES,
]

# Productos
PRODUCT_IMAGE_RUNNING = unsplash("photo-1542291026-7eec264c27ff", 600, 600)
PRODUCT_IMAGE_HOODIE = unsplash("photo-1556821840-3a63f95609a7", 600, 600)
PRODUCT_IMAGE_BAG = unsplash("photo-1553062407-98eeb64c6a62", 600, 600)
PRODUCT_IMAGE_BALL = unsplash("photo-1574629810360-7efbbe195018", 600, 600)
PRODUCT_IMAGE_SHIRT = unsplash("photo-1571902943202-507ec2618e8f", 600, 600)

PRODUCT_IMAGES = [
    PRODUCT_IMAGE_RUNNING,
    PRODUCT_IMAGE_HOODIE,
    PRODUCT_IMAGE_BAG,
    PRODUCT_IMAGE_BALL,
    PRODUCT_IMAGE_SHIRT,
]

PRODUCT_IMAGE_BY_SKU = {
    "ZAP-001": PRODUCT_IMAGE_RUNNING,
    "POL-014": PRODUCT_IMAGE_HOODIE,
    "BOL-008": PRODUCT_IMAGE_BAG,
    "BAL-003": PRODUCT_IMAGE_BALL,
    "CAM-022": PRODUCT_IMAGE_SHIRT,
}

# URLs antiguas o genéricas que deben reemplazarse al reparar
STALE_IMAGE_MARKERS = (
    "picsum.photos",
    "photo-1460353581641-37baddab0a0a",
    "photo-1606107557195-0afed8c8d0c0",
    "photo-1556906781-93a956577a80",
    "photo-1515886657613-9f3525f0cc69",
    "photo-1503341504253-dff4815485f1",
    "binfrix-slider-1",
    "binfrix-slider-2",
    "binfrix-product-runner",
    "binfrix-product-hoodie",
    "binfrix-product-bag",
    "binfrix-cat-shoes",
    "binfrix-cat-apparel",
    "binfrix-cat-accessories",
    "sports-running-track",
    "sports-basketball-court",
    "sports-shoes-sneakers",
    "sports-apparel-gym",
    "sports-gym-bag",
    "sports-running-shoes",
    "sports-hoodie-training",
    "sports-gym-backpack",
    "sports-football-ball",
    "sports-dryfit-shirt",
    "sports-thumb",
    "photo-1622273273912-84a486c16860",
    "photo-1521572267360-6c63f2e0ad26",
)

# Compatibilidad con imports existentes
BROKEN_UNSPLASH_MARKERS = STALE_IMAGE_MARKERS
BROKEN_SLIDER_IMAGE_MARKERS = STALE_IMAGE_MARKERS

IMAGE_PLACEHOLDER_THUMB = unsplash("photo-1542291026-7eec264c27ff", 160, 90)


def image_needs_repair(url: str) -> bool:
    text = (url or "").strip()
    if not text:
        return True
    return any(marker in text for marker in STALE_IMAGE_MARKERS)
