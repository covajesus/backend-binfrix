from datetime import date

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.models.customer import Customer
from app.models.license import TenantLicense
from app.models.order import Order
from app.models.payment import Payment
from app.core.roles import PLATFORM_ROLES
from app.models.platform_product import PlatformProduct
from app.models.role import Role
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.utils.orders import calc_order_total, normalize_line_items
from app.utils.payments import generate_payment_number


PLATFORM_PRODUCTS = [
    ("autolavado", "Autolavado", "Tickets, ventas, cierre de caja y liquidación de lavadores."),
    ("dynamic-landing", "Dynamic Landing Page", "Landings dinámicas para campañas y conversión."),
    ("ecommerce-b2b", "Ecommerce B2B", "Portal mayorista con intranet y presupuestos."),
    ("ecommerce-b2c", "Ecommerce B2C", "Tienda en línea para venta al consumidor final."),
    ("pagos", "Pagos", "Pasarelas de pago, checkout y conciliación de transacciones."),
    ("mantencion", "Mantención", "Soporte técnico, respaldos y monitoreo."),
    ("redes-sociales", "Redes Sociales", "Gestión de perfiles y calendario editorial."),
    ("ventas-whatsapp", "Ventas por WhatsApp", "Canal comercial con pedidos y seguimiento."),
]


def seed_database(db: Session) -> None:
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

    for product_id in ("ecommerce-b2c", "ecommerce-b2b", "pagos"):
        db.add(
            TenantLicense(
                tenant_id=tenant.id,
                platform_product_id=product_id,
                status="active",
                plan="standard",
                starts_at=date(2025, 1, 1),
                ends_at=date(2027, 12, 31),
                max_users=10,
            )
        )

    categories = [
        Category(
            tenant_id=tenant.id,
            name="Calzado",
            description="Zapatillas y calzado deportivo",
            status="active",
            created_at=date(2025, 10, 1),
        ),
        Category(
            tenant_id=tenant.id,
            name="Ropa",
            description="Prendas y accesorios de vestir",
            status="active",
            created_at=date(2025, 10, 1),
        ),
        Category(
            tenant_id=tenant.id,
            name="Accesorios",
            description="Bolsos, mochilas y complementos",
            status="active",
            created_at=date(2025, 10, 1),
        ),
    ]
    db.add_all(categories)

    db.add(
        CatalogProduct(
            tenant_id=tenant.id,
            sku="ZAP-001",
            title="Runner Pro Sneaker",
            description="Zapatilla liviana para entrenamiento y uso urbano.",
            category="Calzado",
            product_type="size_color",
            variant_mode="size_color",
            status="active",
            price=0,
            stock=42,
            images=[],
            color_images={"#111827": [], "#f9fafb": []},
            variants=[
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
        )
    )
    db.add(
        CatalogProduct(
            tenant_id=tenant.id,
            sku="POL-014",
            title="Essential Hoodie",
            description="Polerón de algodón con bolsillo frontal.",
            category="Ropa",
            product_type="simple",
            status="active",
            price=45990,
            stock=18,
            images=[],
            color_images={},
            variants=[],
        )
    )
    db.add(
        CatalogProduct(
            tenant_id=tenant.id,
            sku="BOL-008",
            title="Urban Sport Bag",
            description="Bolso compacto con compartimento para zapatillas.",
            category="Accesorios",
            product_type="simple",
            status="inactive",
            price=32990,
            stock=0,
            images=[],
            color_images={},
            variants=[],
        )
    )

    customers = [
        Customer(
            tenant_id=tenant.id,
            first_name="María",
            last_name="García",
            email="maria.garcia@email.com",
            phone="+56 9 8765 4321",
            city="Santiago",
            status="active",
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
                "product_title": "Runner Pro Sneaker",
                "sku": "ZAP-001-42-BLK",
                "quantity": 1,
                "unit_price": 89990,
            }
        ]
    )
    order_items_2 = normalize_line_items(
        [
            {
                "product_title": "Essential Hoodie",
                "sku": "POL-014",
                "quantity": 2,
                "unit_price": 45990,
            }
        ]
    )
    order_items_3 = normalize_line_items(
        [
            {
                "product_title": "Urban Sport Bag",
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

    db.commit()
