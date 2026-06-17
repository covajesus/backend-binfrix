from datetime import date

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.models.customer import Customer
from app.models.license import TenantLicense
from app.models.order import Order
from app.models.payment import Payment
from app.models.slider import Slider
from app.models.help_page import HelpPage
from app.models.store_settings import StoreSettings
from app.db.help_seed_data import DEMO_HELP_PAGES
from app.db.store_settings_seed_data import DEMO_STORE_SETTINGS
from app.core.roles import PLATFORM_ROLES
from app.models.platform_product import PlatformProduct
from app.models.role import Role
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.utils.orders import calc_order_total, normalize_line_items
from app.utils.customer_addresses import normalize_addresses
from app.utils.payments import generate_payment_number
from app.db.demo_assets import (
    CATEGORY_IMAGES,
    image_needs_repair,
    PRODUCT_IMAGE_BY_SKU,
    PRODUCT_IMAGES,
    SLIDER_BANNERS,
)
from app.db.sports_seed_content import (
    DEMO_CATEGORY_SPECS,
    DEMO_PRODUCT_SPECS,
    DEMO_SLIDER_SPECS,
    build_catalog_product,
    build_demo_categories,
    build_demo_sliders,
)


PLATFORM_PRODUCTS = [
    ("autolavado", "Autolavado", "Tickets, ventas, cierre de caja y liquidación de lavadores."),
    ("dynamic-landing", "Dynamic Landing Page", "Landings dinámicas para campañas y conversión."),
    ("ecommerce-b2b", "Ecommerce B2B", "Portal mayorista con intranet y presupuestos."),
    ("ecommerce-b2c", "Ecommerce B2C", "Tienda en línea para venta al consumidor final."),
    ("mantencion", "Mantención", "Soporte técnico, respaldos y monitoreo."),
    ("ventas-whatsapp", "Ventas por WhatsApp", "Canal comercial con pedidos y seguimiento."),
]

RETIRED_PLATFORM_PRODUCT_IDS = ("pagos", "redes-sociales")

DEMO_TENANT_SLUG = "tienda-demo"
DEMO_TENANT_LICENSE_PRODUCTS = ("ecommerce-b2c",)


def _demo_sliders(tenant_id: str) -> list[Slider]:
    return build_demo_sliders(tenant_id)


def repair_sports_demo_content(db: Session) -> None:
    """Actualiza sliders, categorías y productos demo a temática deportiva."""
    tenant = db.query(Tenant).filter(Tenant.slug == "tienda-demo").first()
    if tenant is None:
        return

    changed = False

    sliders = (
        db.query(Slider)
        .filter(Slider.tenant_id == tenant.id)
        .order_by(Slider.sort_order)
        .all()
    )
    for index, slider in enumerate(sliders):
        spec = DEMO_SLIDER_SPECS[index % len(DEMO_SLIDER_SPECS)]
        slider.title = spec["title"]
        slider.subtitle = spec["subtitle"]
        slider.cta = spec["cta"]
        slider.link_suffix = spec["link_suffix"]
        slider.theme = spec["theme"]
        slider.sort_order = spec["sort_order"]
        slider.image_url = SLIDER_BANNERS[index % len(SLIDER_BANNERS)]
        slider.status = "active"
        changed = True

    categories = (
        db.query(Category)
        .filter(Category.tenant_id == tenant.id)
        .order_by(Category.name)
        .all()
    )
    spec_by_name = {spec["name"]: spec for spec in DEMO_CATEGORY_SPECS}
    for category in categories:
        spec = spec_by_name.get(category.name)
        if not spec:
            continue
        index = DEMO_CATEGORY_SPECS.index(spec)
        category.description = spec["description"]
        category.image_url = CATEGORY_IMAGES[index % len(CATEGORY_IMAGES)]
        changed = True

    spec_by_sku = {spec["sku"]: spec for spec in DEMO_PRODUCT_SPECS}
    products = db.query(CatalogProduct).filter(CatalogProduct.tenant_id == tenant.id).all()
    for product in products:
        spec = spec_by_sku.get(product.sku)
        if not spec:
            continue
        product.title = spec["title"]
        product.description = spec["description"]
        product.category = spec["category"]
        product.product_type = spec["product_type"]
        product.variant_mode = spec.get("variant_mode")
        product.status = spec["status"]
        product.price = spec.get("price", 0)
        product.stock = spec.get("stock", 0)
        product.variants = spec.get("variants", [])
        product.color_images = spec.get("color_images", {})
        image = PRODUCT_IMAGE_BY_SKU.get(spec["sku"])
        if image:
            product.images = [image]
        changed = True

    existing_skus = {product.sku for product in products}
    for spec in DEMO_PRODUCT_SPECS:
        if spec["sku"] in existing_skus:
            continue
        db.add(build_catalog_product(tenant.id, spec))
        changed = True

    if changed:
        db.commit()


def ensure_category_image_column(db: Session) -> None:
    from sqlalchemy import inspect, text

    from app.db.session import engine

    inspector = inspect(engine)
    if "categories" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("categories")}
    if "image_url" in columns:
        return
    db.execute(text("ALTER TABLE categories ADD COLUMN image_url TEXT NOT NULL"))
    db.commit()


def repair_broken_slider_images(db: Session) -> None:
    sliders = db.query(Slider).all()
    if not sliders:
        return
    changed = False
    for slider in sliders:
        if not image_needs_repair(slider.image_url):
            continue
        index = max(0, min((slider.sort_order or 1) - 1, len(SLIDER_BANNERS) - 1))
        slider.image_url = SLIDER_BANNERS[index]
        changed = True
    if changed:
        db.commit()


def repair_category_images(db: Session) -> None:
    categories = db.query(Category).order_by(Category.name).all()
    if not categories:
        return
    changed = False
    for index, category in enumerate(categories):
        if not image_needs_repair(category.image_url):
            continue
        category.image_url = CATEGORY_IMAGES[index % len(CATEGORY_IMAGES)]
        changed = True
    if changed:
        db.commit()


def repair_product_images(db: Session) -> None:
    products = db.query(CatalogProduct).order_by(CatalogProduct.sku).all()
    if not products:
        return
    changed = False
    for index, product in enumerate(products):
        expected = PRODUCT_IMAGE_BY_SKU.get(product.sku)
        if expected:
            current = str((product.images or [""])[0] or "").strip()
            if current != expected or image_needs_repair(current):
                product.images = [expected]
                changed = True
            continue

        images = product.images or []
        current = str(images[0] or "").strip() if images else ""
        if not image_needs_repair(current):
            continue
        product.images = [PRODUCT_IMAGES[index % len(PRODUCT_IMAGES)]]
        changed = True
    if changed:
        db.commit()


def seed_demo_help_pages_if_empty(db: Session) -> None:
    tenant = db.query(Tenant).filter(Tenant.slug == "tienda-demo").first()
    if tenant is None:
        return
    if db.query(HelpPage).filter(HelpPage.tenant_id == tenant.id).first():
        return
    for page_data in DEMO_HELP_PAGES:
        db.add(
            HelpPage(
                tenant_id=tenant.id,
                slug=page_data["slug"],
                nav_label=page_data["nav_label"],
                title=page_data["title"],
                subtitle=page_data["subtitle"],
                intro=page_data["intro"],
                sections=page_data["sections"],
                sort_order=page_data["sort_order"],
                status="active",
            )
        )
    db.commit()


def seed_demo_store_settings_if_empty(db: Session) -> None:
    tenant = db.query(Tenant).filter(Tenant.slug == "tienda-demo").first()
    if tenant is None:
        return
    if db.query(StoreSettings).filter(StoreSettings.tenant_id == tenant.id).first():
        return
    db.add(
        StoreSettings(
            tenant_id=tenant.id,
            phone=DEMO_STORE_SETTINGS["phone"],
            schedule=DEMO_STORE_SETTINGS["schedule"],
            support_label=DEMO_STORE_SETTINGS["support_label"],
            support_href=DEMO_STORE_SETTINGS["support_href"],
            contact_email=DEMO_STORE_SETTINGS["contact_email"],
            store_url=DEMO_STORE_SETTINGS["store_url"],
            store_logo_url=DEMO_STORE_SETTINGS.get("store_logo_url", ""),
            storefront_template=DEMO_STORE_SETTINGS.get("storefront_template", "sports"),
            multilingual_enabled=DEMO_STORE_SETTINGS.get("multilingual_enabled", False),
            default_locale=DEMO_STORE_SETTINGS.get("default_locale", "es"),
            account_label=DEMO_STORE_SETTINGS.get("account_label", ""),
            account_href=DEMO_STORE_SETTINGS.get("account_href", "/help"),
            promo_messages=list(DEMO_STORE_SETTINGS.get("promo_messages", [])),
            header_links=list(DEMO_STORE_SETTINGS.get("header_links", [])),
            social_links=DEMO_STORE_SETTINGS["social_links"],
        )
    )
    db.commit()


def seed_demo_sliders_if_empty(db: Session) -> None:
    if db.query(Slider).first():
        return
    tenant = db.query(Tenant).filter(Tenant.slug == "tienda-demo").first()
    if tenant is None:
        return
    db.add_all(_demo_sliders(tenant.id))
    db.commit()


DEMO_MARIA_SHIPPING_ADDRESSES = [
    {
        "id": "a1000001-0000-4000-8000-000000000001",
        "label": "Casa",
        "address": "Av. Providencia 1200, Depto 402",
        "city": "Santiago",
        "region": "Región Metropolitana",
        "phone": "+56 9 8765 4321",
        "is_default": True,
    },
    {
        "id": "a1000001-0000-4000-8000-000000000002",
        "label": "Oficina",
        "address": "Nueva Tajamar 481, Torre Sur",
        "city": "Santiago",
        "region": "Región Metropolitana",
        "phone": "+56 9 8765 4321",
        "is_default": False,
    },
]


def repair_demo_customer_portal_access(db: Session) -> None:
    tenant = db.query(Tenant).filter(Tenant.slug == "tienda-demo").first()
    if tenant is None:
        return

    maria = (
        db.query(Customer)
        .filter(
            Customer.tenant_id == tenant.id,
            Customer.email == "maria.garcia@email.com",
        )
        .first()
    )
    if maria is not None and not maria.password_hash:
        maria.password_hash = get_password_hash("demo1234")

    if maria is not None and not normalize_addresses(maria.shipping_addresses):
        maria.shipping_addresses = normalize_addresses(DEMO_MARIA_SHIPPING_ADDRESSES)

    settings = db.query(StoreSettings).filter(StoreSettings.tenant_id == tenant.id).first()
    if settings is not None and settings.account_href in ("/help", ""):
        settings.account_href = "/account"

    db.commit()


def seed_demo_business_data_if_empty(db: Session) -> None:
    tenant = db.query(Tenant).filter(Tenant.slug == "tienda-demo").first()
    if tenant is None:
        return
    if db.query(CatalogProduct).filter(CatalogProduct.tenant_id == tenant.id).first():
        return

    categories = build_demo_categories(tenant.id)
    db.add_all(categories)
    seed_demo_sliders_if_empty(db)

    for spec in DEMO_PRODUCT_SPECS:
        db.add(build_catalog_product(tenant.id, spec))

    customers = [
        Customer(
            tenant_id=tenant.id,
            first_name="María",
            last_name="García",
            email="maria.garcia@email.com",
            phone="+56 9 8765 4321",
            city="Santiago",
            status="active",
            password_hash=get_password_hash("demo1234"),
            shipping_addresses=normalize_addresses(DEMO_MARIA_SHIPPING_ADDRESSES),
            created_at=date(2025, 11, 12),
        ),
        Customer(
            tenant_id=tenant.id,
            first_name="Carlos",
            last_name="Ruiz",
            email="carlos.ruiz@email.com",
            phone="+56 9 7654 3210",
            city="Valparaíso",
            status="active",
            created_at=date(2025, 12, 3),
        ),
        Customer(
            tenant_id=tenant.id,
            first_name="Ana",
            last_name="Martín",
            email="ana.martin@email.com",
            phone="+56 9 6543 2109",
            city="Concepción",
            status="inactive",
            created_at=date(2026, 1, 18),
        ),
    ]
    db.add_all(customers)
    db.flush()

    order_items_1 = normalize_line_items(
        [
            {
                "product_title": "Zapatillas Running Pro",
                "sku": "ZAP-001-42-BLK",
                "quantity": 1,
                "unit_price": 89990,
            }
        ]
    )
    order_items_2 = normalize_line_items(
        [
            {
                "product_title": "Polerón Training Fit",
                "sku": "POL-014",
                "quantity": 2,
                "unit_price": 45990,
            }
        ]
    )
    order_items_3 = normalize_line_items(
        [
            {
                "product_title": "Mochila Gym Sport",
                "sku": "BOL-008",
                "quantity": 1,
                "unit_price": 32990,
            }
        ]
    )

    orders = [
        Order(
            tenant_id=tenant.id,
            order_number="PED-0001",
            customer_id=customers[0].id,
            customer_name="María García",
            customer_email=customers[0].email,
            customer_phone=customers[0].phone,
            shipping_address="Av. Providencia 1200, Depto 402",
            city="Santiago",
            status="delivered",
            payment_status="paid",
            items=order_items_1,
            total=calc_order_total(order_items_1),
            created_at=date(2026, 3, 8),
        ),
        Order(
            tenant_id=tenant.id,
            order_number="PED-0002",
            customer_id=customers[1].id,
            customer_name="Carlos Ruiz",
            customer_email=customers[1].email,
            customer_phone=customers[1].phone,
            shipping_address="Calle Prat 88",
            city="Valparaíso",
            status="pending",
            payment_status="pending",
            items=order_items_2,
            total=calc_order_total(order_items_2),
            created_at=date(2026, 3, 10),
        ),
        Order(
            tenant_id=tenant.id,
            order_number="PED-0003",
            customer_id=customers[2].id,
            customer_name="Ana Martín",
            customer_email=customers[2].email,
            customer_phone=customers[2].phone,
            shipping_address="Los Carrera 455",
            city="Concepción",
            status="shipped",
            payment_status="paid",
            items=order_items_3,
            total=calc_order_total(order_items_3),
            created_at=date(2026, 3, 1),
        ),
    ]
    db.add_all(orders)
    db.flush()

    if not db.query(Payment).filter(Payment.tenant_id == tenant.id).first():
        db.add_all(
            [
                Payment(
                    tenant_id=tenant.id,
                    payment_number="PAG-0001",
                    order_id=orders[0].id,
                    order_number=orders[0].order_number,
                    customer_name=orders[0].customer_name,
                    amount=orders[0].total,
                    method="webpay",
                    status="completed",
                    transaction_ref="WP-92837461",
                    paid_at=date(2026, 3, 8),
                    created_at=date(2026, 3, 8),
                ),
                Payment(
                    tenant_id=tenant.id,
                    payment_number="PAG-0002",
                    order_id=orders[1].id,
                    order_number=orders[1].order_number,
                    customer_name=orders[1].customer_name,
                    amount=orders[1].total,
                    method="transfer",
                    status="pending",
                    transaction_ref="TRF-004512",
                    paid_at=None,
                    created_at=date(2026, 3, 10),
                ),
                Payment(
                    tenant_id=tenant.id,
                    payment_number="PAG-0003",
                    order_id=orders[2].id,
                    order_number=orders[2].order_number,
                    customer_name=orders[2].customer_name,
                    amount=orders[2].total,
                    method="card",
                    status="completed",
                    transaction_ref="TC-7712044",
                    paid_at=date(2026, 3, 1),
                    created_at=date(2026, 3, 1),
                ),
            ]
        )

    db.commit()


def repair_demo_tenant_licenses(db: Session) -> None:
    """Demo tenant: solo ecommerce-b2c. Productos retirados no son servicios SaaS activos."""
    for product_id in RETIRED_PLATFORM_PRODUCT_IDS:
        retired = db.get(PlatformProduct, product_id)
        if retired is not None:
            retired.is_active = False
        db.query(TenantLicense).filter(
            TenantLicense.platform_product_id == product_id
        ).delete(synchronize_session=False)

    tenant = db.query(Tenant).filter(Tenant.slug == DEMO_TENANT_SLUG).first()
    if tenant is None:
        db.commit()
        return

    allowed = set(DEMO_TENANT_LICENSE_PRODUCTS)
    licenses = (
        db.query(TenantLicense)
        .filter(TenantLicense.tenant_id == tenant.id)
        .all()
    )
    for license_row in licenses:
        if license_row.platform_product_id not in allowed:
            db.delete(license_row)

    existing_b2c = (
        db.query(TenantLicense)
        .filter(
            TenantLicense.tenant_id == tenant.id,
            TenantLicense.platform_product_id == "ecommerce-b2c",
        )
        .first()
    )
    if existing_b2c is None:
        db.add(
            TenantLicense(
                tenant_id=tenant.id,
                platform_product_id="ecommerce-b2c",
                status="active",
                plan="standard",
                starts_at=date(2025, 1, 1),
                ends_at=None,
                max_users=1,
            )
        )
    else:
        existing_b2c.status = "active"
        existing_b2c.plan = "standard"
        existing_b2c.max_users = 1

    db.commit()


def seed_database(db: Session) -> None:
    ensure_category_image_column(db)
    seed_demo_sliders_if_empty(db)
    repair_broken_slider_images(db)
    repair_category_images(db)
    repair_product_images(db)
    repair_sports_demo_content(db)
    seed_demo_help_pages_if_empty(db)
    seed_demo_store_settings_if_empty(db)
    repair_demo_customer_portal_access(db)
    seed_demo_business_data_if_empty(db)
    repair_demo_tenant_licenses(db)
    if db.query(User).first():
        return

    role_by_slug: dict[str, Role] = {}
    for role_data in PLATFORM_ROLES:
        role = Role(**role_data)
        db.add(role)
        role_by_slug[role.slug] = role
    db.flush()

    admin = User(
        email="admin@binfrix.com",
        password_hash=get_password_hash("admin123"),
        name="Administrador",
        role_id=role_by_slug["administrador"].id,
        is_superadmin=True,
    )
    cliente1 = User(
        email="cliente1@binfrix.com",
        password_hash=get_password_hash("cliente123"),
        name="María López",
        role_id=role_by_slug["cliente_tipo_1"].id,
    )
    cliente2 = User(
        email="cliente2@binfrix.com",
        password_hash=get_password_hash("cliente123"),
        name="Carlos Ruiz",
        role_id=role_by_slug["cliente_tipo_2"].id,
    )
    db.add_all([admin, cliente1, cliente2])
    db.flush()

    tenant = Tenant(name="Tienda Demo Binfrix", slug="tienda-demo", status="active")
    db.add(tenant)
    db.flush()

    db.add_all(
        [
            TenantMembership(tenant_id=tenant.id, user_id=admin.id, role="admin"),
            TenantMembership(tenant_id=tenant.id, user_id=cliente1.id, role="staff"),
            TenantMembership(tenant_id=tenant.id, user_id=cliente2.id, role="staff"),
        ]
    )

    for product_id, name, description in PLATFORM_PRODUCTS:
        db.add(
            PlatformProduct(
                id=product_id,
                name=name,
                description=description,
                is_active=True,
            )
        )

    for product_id in DEMO_TENANT_LICENSE_PRODUCTS:
        db.add(
            TenantLicense(
                tenant_id=tenant.id,
                platform_product_id=product_id,
                status="active",
                plan="standard",
                starts_at=date(2025, 1, 1),
                ends_at=None,
                max_users=10,
            )
        )

    categories = build_demo_categories(tenant.id)
    db.add_all(categories)

    db.add_all(_demo_sliders(tenant.id))

    for spec in DEMO_PRODUCT_SPECS:
        db.add(build_catalog_product(tenant.id, spec))

    customers = [
        Customer(
            tenant_id=tenant.id,
            first_name="María",
            last_name="García",
            email="maria.garcia@email.com",
            phone="+56 9 8765 4321",
            city="Santiago",
            status="active",
            password_hash=get_password_hash("demo1234"),
            shipping_addresses=normalize_addresses(DEMO_MARIA_SHIPPING_ADDRESSES),
            created_at=date(2025, 11, 12),
        ),
        Customer(
            tenant_id=tenant.id,
            first_name="Carlos",
            last_name="Ruiz",
            email="carlos.ruiz@email.com",
            phone="+56 9 7654 3210",
            city="Valparaíso",
            status="active",
            created_at=date(2025, 12, 3),
        ),
        Customer(
            tenant_id=tenant.id,
            first_name="Ana",
            last_name="Martín",
            email="ana.martin@email.com",
            phone="+56 9 6543 2109",
            city="Concepción",
            status="inactive",
            created_at=date(2026, 1, 18),
        ),
    ]
    db.add_all(customers)
    db.flush()

    order_items_1 = normalize_line_items(
        [
            {
                "product_title": "Zapatillas Running Pro",
                "sku": "ZAP-001-42-BLK",
                "quantity": 1,
                "unit_price": 89990,
            }
        ]
    )
    order_items_2 = normalize_line_items(
        [
            {
                "product_title": "Polerón Training Fit",
                "sku": "POL-014",
                "quantity": 2,
                "unit_price": 45990,
            }
        ]
    )
    order_items_3 = normalize_line_items(
        [
            {
                "product_title": "Mochila Gym Sport",
                "sku": "BOL-008",
                "quantity": 1,
                "unit_price": 32990,
            }
        ]
    )

    orders = [
        Order(
            tenant_id=tenant.id,
            order_number="PED-0001",
            customer_id=customers[0].id,
            customer_name="María García",
            customer_email=customers[0].email,
            customer_phone=customers[0].phone,
            shipping_address="Av. Providencia 1200, Depto 402",
            city="Santiago",
            status="delivered",
            payment_status="paid",
            items=order_items_1,
            total=calc_order_total(order_items_1),
            created_at=date(2026, 3, 8),
        ),
        Order(
            tenant_id=tenant.id,
            order_number="PED-0002",
            customer_id=customers[1].id,
            customer_name="Carlos Ruiz",
            customer_email=customers[1].email,
            customer_phone=customers[1].phone,
            shipping_address="Calle Prat 88",
            city="Valparaíso",
            status="pending",
            payment_status="pending",
            items=order_items_2,
            total=calc_order_total(order_items_2),
            created_at=date(2026, 3, 10),
        ),
        Order(
            tenant_id=tenant.id,
            order_number="PED-0003",
            customer_id=customers[2].id,
            customer_name="Ana Martín",
            customer_email=customers[2].email,
            customer_phone=customers[2].phone,
            shipping_address="Los Carrera 455",
            city="Concepción",
            status="shipped",
            payment_status="paid",
            items=order_items_3,
            total=calc_order_total(order_items_3),
            created_at=date(2026, 3, 1),
        ),
    ]
    db.add_all(orders)
    db.flush()

    db.add_all(
        [
            Payment(
                tenant_id=tenant.id,
                payment_number="PAG-0001",
                order_id=orders[0].id,
                order_number=orders[0].order_number,
                customer_name=orders[0].customer_name,
                amount=orders[0].total,
                method="webpay",
                status="completed",
                transaction_ref="WP-92837461",
                paid_at=date(2026, 3, 8),
                created_at=date(2026, 3, 8),
            ),
            Payment(
                tenant_id=tenant.id,
                payment_number="PAG-0002",
                order_id=orders[1].id,
                order_number=orders[1].order_number,
                customer_name=orders[1].customer_name,
                amount=orders[1].total,
                method="transfer",
                status="pending",
                transaction_ref="TRF-004512",
                paid_at=None,
                created_at=date(2026, 3, 10),
            ),
            Payment(
                tenant_id=tenant.id,
                payment_number="PAG-0003",
                order_id=orders[2].id,
                order_number=orders[2].order_number,
                customer_name=orders[2].customer_name,
                amount=orders[2].total,
                method="card",
                status="completed",
                transaction_ref="TC-7712044",
                paid_at=date(2026, 3, 1),
                created_at=date(2026, 3, 1),
            ),
        ]
    )

    for page_data in DEMO_HELP_PAGES:
        db.add(
            HelpPage(
                tenant_id=tenant.id,
                slug=page_data["slug"],
                nav_label=page_data["nav_label"],
                title=page_data["title"],
                subtitle=page_data["subtitle"],
                intro=page_data["intro"],
                sections=page_data["sections"],
                sort_order=page_data["sort_order"],
                status="active",
            )
        )

    db.commit()
