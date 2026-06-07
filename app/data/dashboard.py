from app.schemas.dashboard import ActivityOut, DashboardOut, StatOut

DEFAULT_STATS: list[StatOut] = [
    StatOut(label="Usuarios activos", value="1,284", change="+12%", up=True),
    StatOut(label="Ingresos del mes", value="$48,320", change="+8%", up=True),
    StatOut(label="Pedidos pendientes", value="37", change="-3%", up=False),
    StatOut(label="Tasa de conversión", value="4.2%", change="+0.5%", up=True),
]

DEFAULT_ACTIVITY: list[ActivityOut] = [
    ActivityOut(action="Nuevo usuario registrado", time="Hace 5 min", user="María García"),
    ActivityOut(action="Pedido #1042 completado", time="Hace 18 min", user="Carlos Ruiz"),
    ActivityOut(action="Actualización de inventario", time="Hace 1 h", user="Sistema"),
    ActivityOut(action="Reporte mensual generado", time="Hace 2 h", user="Administrador"),
]

PRODUCT_DASHBOARDS: dict[str, dict] = {
    "autolavado": {
        "stats": [
            StatOut(label="Tickets hoy", value="186", change="+9%", up=True),
            StatOut(label="Ventas del día", value="$1,240", change="+6%", up=True),
            StatOut(label="Lavadores activos", value="12", change="+0%", up=True),
            StatOut(label="Cierres pendientes", value="2", change="-1", up=False),
        ],
        "recent_activity": [
            ActivityOut(action="Ticket #A-882 emitido", time="Hace 3 min", user="Caja 1"),
            ActivityOut(action="Cierre parcial registrado", time="Hace 25 min", user="María García"),
            ActivityOut(action="Liquidación de lavador", time="Hace 1 h", user="Sistema"),
            ActivityOut(action="Gasto operativo cargado", time="Hace 2 h", user="Administrador"),
        ],
    },
    "ecommerce-b2c": {
        "stats": [
            StatOut(label="Pedidos del mes", value="842", change="+14%", up=True),
            StatOut(label="Ingresos", value="$128,400", change="+11%", up=True),
            StatOut(label="Carritos abandonados", value="96", change="-5%", up=True),
            StatOut(label="Conversión", value="3.8%", change="+0.3%", up=True),
        ],
        "recent_activity": [
            ActivityOut(action="Pedido #B2C-4412 pagado", time="Hace 7 min", user="Cliente web"),
            ActivityOut(action="Stock actualizado", time="Hace 20 min", user="Sistema"),
            ActivityOut(action="Cupón promocional creado", time="Hace 1 h", user="Administrador"),
            ActivityOut(action="Devolución aprobada", time="Hace 2 h", user="Soporte"),
        ],
    },
    "ventas-whatsapp": {
        "stats": [
            StatOut(label="Conversaciones activas", value="54", change="+18%", up=True),
            StatOut(label="Pedidos cerrados", value="29", change="+7%", up=True),
            StatOut(label="Tiempo de respuesta", value="4.2 min", change="-12%", up=True),
            StatOut(label="Leads nuevos", value="73", change="+10%", up=True),
        ],
        "recent_activity": [
            ActivityOut(action="Pedido confirmado por chat", time="Hace 2 min", user="Carlos Ruiz"),
            ActivityOut(action="Plantilla enviada", time="Hace 15 min", user="Sistema"),
            ActivityOut(action="Seguimiento de cotización", time="Hace 45 min", user="Ventas"),
            ActivityOut(action="Cliente reasignado", time="Hace 1 h", user="Administrador"),
        ],
    },
}


def get_dashboard(product_id: str, product_name: str) -> DashboardOut:
    data = PRODUCT_DASHBOARDS.get(product_id, {})
    return DashboardOut(
        product_id=product_id,
        product_name=product_name,
        stats=data.get("stats", DEFAULT_STATS),
        recent_activity=data.get("recent_activity", DEFAULT_ACTIVITY),
    )
