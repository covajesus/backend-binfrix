"""Columnas de facturación en pedidos."""

from sqlalchemy import inspect, text

from app.db.session import engine


def ensure_order_billing_column() -> list[str]:
    inspector = inspect(engine)
    if "orders" not in inspector.get_table_names():
        return []

    cols = {c["name"] for c in inspector.get_columns("orders")}
    added: list[str] = []
    if "billing" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE orders ADD COLUMN billing JSON NULL"))
        added.append("billing")

    with engine.begin() as conn:
        conn.execute(text("UPDATE orders SET billing = JSON_OBJECT() WHERE billing IS NULL"))

    return added
