"""Catálogo de productos SaaS Binfrix (fuente de verdad para seed y licencias)."""

PLATFORM_PRODUCTS: list[tuple[str, str, str]] = [
    ("autolavado", "Autolavado", "Tickets, ventas, cierre de caja y liquidación de lavadores."),
    ("dynamic-landing", "Landing Page Dinámica", "Landings dinámicas para campañas y conversión."),
    ("ecommerce-b2b", "Ecommerce B2B", "Portal mayorista con intranet y presupuestos."),
    ("ecommerce-b2c", "Ecommerce B2C", "Tienda en línea para venta al consumidor final."),
    ("ventas-whatsapp", "Ventas por WhatsApp", "Canal comercial con pedidos y seguimiento."),
]

RETIRED_PLATFORM_PRODUCT_IDS: tuple[str, ...] = ("pagos", "redes-sociales", "mantencion")
