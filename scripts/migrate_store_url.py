"""Añade columna store_url a store_settings si falta."""
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

if "store_url" not in cols:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE store_settings "
                "ADD COLUMN store_url VARCHAR(500) NOT NULL DEFAULT ''"
            )
        )
    print("store_url column added")
else:
    print("store_url column already exists")

db = SessionLocal()
try:
    from app.models.store_settings import StoreSettings
    from app.models.tenant import Tenant

    tenant = db.query(Tenant).filter(Tenant.slug == "tienda-demo").first()
    if tenant:
        row = (
            db.query(StoreSettings)
            .filter(StoreSettings.tenant_id == tenant.id)
            .first()
        )
        if row and not (row.store_url or "").strip():
            row.store_url = "http://localhost:5174"
            db.commit()
            print("backfilled tienda-demo store_url")
finally:
    db.close()
