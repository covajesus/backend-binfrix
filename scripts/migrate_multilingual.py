"""Añade columnas multilingual_enabled y default_locale a store_settings si faltan."""
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

if "multilingual_enabled" not in cols:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE store_settings "
                "ADD COLUMN multilingual_enabled TINYINT(1) NOT NULL DEFAULT 0"
            )
        )
    print("Columna multilingual_enabled creada")
else:
    print("Columna multilingual_enabled ya existe")

if "default_locale" not in cols:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE store_settings "
                "ADD COLUMN default_locale VARCHAR(5) NOT NULL DEFAULT 'es'"
            )
        )
    print("Columna default_locale creada")
else:
    print("Columna default_locale ya existe")

db = SessionLocal()
try:
    db.execute(
        text(
            "UPDATE store_settings "
            "SET default_locale = 'es' "
            "WHERE default_locale IS NULL OR default_locale = ''"
        )
    )
    db.commit()
    print("Idioma por defecto aplicado")
finally:
    db.close()
