"""Añade columnas faltantes en customers (MySQL / tablas ya existentes)."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.session import engine


def ensure_customer_columns() -> list[str]:
    inspector = inspect(engine)
    if "customers" not in inspector.get_table_names():
        return []

    cols = {c["name"] for c in inspector.get_columns("customers")}
    added: list[str] = []

    if "password_hash" not in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE customers "
                    "ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''"
                )
            )
        added.append("password_hash")

    if "shipping_addresses" not in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE customers "
                    "ADD COLUMN shipping_addresses JSON NULL"
                )
            )
        added.append("shipping_addresses")

    if "shipping_addresses" in added or "shipping_addresses" in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE customers SET shipping_addresses = '[]' "
                    "WHERE shipping_addresses IS NULL"
                )
            )

    return added
