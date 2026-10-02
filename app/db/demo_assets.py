"""Imágenes demo de joyería (Unsplash) para la plantilla Lamora."""


def unsplash(photo_id: str, width: int, height: int) -> str:
    path = photo_id if photo_id.startswith("photo-") else f"photo-{photo_id}"
    return (
        f"https://images.unsplash.com/{path}"
        f"?auto=format&fit=crop&w={width}&h={height}&q=80"
    )


SLIDER_BANNER_HERO = unsplash("photo-1515562141207-7a88fb7ce338", 1920, 1080)
SLIDER_BANNER_EDITORIAL = unsplash("photo-1617038260897-41a1f14a8ca0", 1600, 1200)

SLIDER_BANNERS = [SLIDER_BANNER_HERO, SLIDER_BANNER_EDITORIAL]

CATEGORY_IMAGE_RINGS = unsplash("photo-1605100804763-247f67b3557e", 900, 1200)
CATEGORY_IMAGE_EARRINGS = unsplash("photo-1535632066927-ab7c9ab60908", 900, 1200)
CATEGORY_IMAGE_NECKLACES = unsplash("photo-1599643478518-a784e5dc4c8f", 900, 1200)

CATEGORY_IMAGES = [
    CATEGORY_IMAGE_RINGS,
    CATEGORY_IMAGE_EARRINGS,
    CATEGORY_IMAGE_NECKLACES,
]

PRODUCT_IMAGE_RING = unsplash("photo-1605100804763-247f67b3557e", 900, 1200)
PRODUCT_IMAGE_EARRINGS = unsplash("photo-1535632066927-ab7c9ab60908", 900, 1200)
PRODUCT_IMAGE_NECKLACE = unsplash("photo-1599643478518-a784e5dc4c8f", 900, 1200)
PRODUCT_IMAGE_BRACELET = unsplash("photo-1611591437281-460bfbe1220a", 900, 1200)
PRODUCT_IMAGE_SOLITAIRE = unsplash("photo-1573408301185-9146fe634ad0", 900, 1200)

PRODUCT_IMAGES = [
    PRODUCT_IMAGE_RING,
    PRODUCT_IMAGE_EARRINGS,
    PRODUCT_IMAGE_NECKLACE,
    PRODUCT_IMAGE_BRACELET,
    PRODUCT_IMAGE_SOLITAIRE,
]

PRODUCT_IMAGE_BY_SKU = {
    "ZAP-001": PRODUCT_IMAGE_RING,
    "POL-014": PRODUCT_IMAGE_EARRINGS,
    "BOL-008": PRODUCT_IMAGE_NECKLACE,
    "BAL-003": PRODUCT_IMAGE_BRACELET,
    "CAM-022": PRODUCT_IMAGE_SOLITAIRE,
}

STALE_IMAGE_MARKERS = (
    "picsum.photos",
    "photo-1460353581641-37baddab0a0a",
    "photo-1606107557195-0afed8c8d0c0",
    "photo-1556906781-93a956577a80",
    "photo-1515886657613-9f3525f0cc69",
    "photo-1503341504253-dff4815485f1",
    "photo-1476480862126-209bfaa8edc8",
    "photo-1546519638-68e109498ffc",
    "photo-1542291026-7eec264c27ff",
    "photo-1571019614242-c5c5dee9f50b",
    "photo-1591047139829-d91aecb6caea",
    "photo-1556821840-3a63f95609a7",
    "photo-1553062407-98eeb64c6a62",
    "photo-1574629810360-7efbbe195018",
    "photo-1571902943202-507ec2618e8f",
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

BROKEN_UNSPLASH_MARKERS = STALE_IMAGE_MARKERS
BROKEN_SLIDER_IMAGE_MARKERS = STALE_IMAGE_MARKERS

IMAGE_PLACEHOLDER_THUMB = unsplash("photo-1515562141207-7a88fb7ce338", 160, 90)


def image_needs_repair(url: str) -> bool:
    text = (url or "").strip()
    if not text:
        return True
    return any(marker in text for marker in STALE_IMAGE_MARKERS)
