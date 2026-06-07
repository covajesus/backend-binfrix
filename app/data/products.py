from app.schemas.product import ProductOut

BINFRIX_PRODUCTS: list[ProductOut] = [
    ProductOut(
        id="autolavado",
        name="Autolavado",
        description="Tickets, ventas, cierre de caja y liquidación de lavadores.",
    ),
    ProductOut(
        id="dynamic-landing",
        name="Dynamic Landing Page",
        description="Landings dinámicas para campañas y conversión.",
    ),
    ProductOut(
        id="ecommerce-b2b",
        name="Ecommerce B2B",
        description="Portal mayorista con intranet y presupuestos.",
    ),
    ProductOut(
        id="ecommerce-b2c",
        name="Ecommerce B2C",
        description="Tienda en línea para venta al consumidor final.",
    ),
    ProductOut(
        id="pagos",
        name="Pagos",
        description="Pasarelas de pago, checkout y conciliación de transacciones.",
    ),
    ProductOut(
        id="mantencion",
        name="Mantención",
        description="Soporte técnico, respaldos y monitoreo.",
    ),
    ProductOut(
        id="redes-sociales",
        name="Redes Sociales",
        description="Gestión de perfiles y calendario editorial.",
    ),
    ProductOut(
        id="ventas-whatsapp",
        name="Ventas por WhatsApp",
        description="Canal comercial con pedidos y seguimiento.",
    ),
]


def get_product_by_id(product_id: str) -> ProductOut | None:
    for product in BINFRIX_PRODUCTS:
        if product.id == product_id:
            return product
    return None
