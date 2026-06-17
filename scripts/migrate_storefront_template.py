"""Añade columna storefront_template a store_settings si falta."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from app.db.session import engine, init_db, SessionLocal

init_db()
inspector = inspect(engine)
cols = [c["name"] for c in inspector.get_columns("store_settings")]

if "storefront_template" not in cols:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE store_settings "
                "ADD COLUMN storefront_template VARCHAR(40) NOT NULL DEFAULT 'sports'"
            )
        )
    print("Columna storefront_template creada")
else:
    print("Columna storefront_template ya existe")

db = SessionLocal()
try:
    db.execute(
        text(
            "UPDATE store_settings "
            "SET storefront_template = 'sports' "
            "WHERE storefront_template IS NULL OR storefront_template = ''"
        )
    )
    db.commit()
    print("Plantilla por defecto aplicada")
finally:
    db.close()
