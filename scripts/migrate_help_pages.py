"""Crea la tabla help_pages y siembra páginas demo si está vacía."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from app.db.seed import seed_demo_help_pages_if_empty
from app.db.session import SessionLocal, init_db, engine


def main() -> None:
    init_db()
    inspector = inspect(engine)
    if "help_pages" not in inspector.get_table_names():
        sql_path = ROOT / "scripts" / "migrate_help_pages.sql"
        with engine.begin() as conn:
            raw = sql_path.read_text(encoding="utf-8-sig")
            for stmt in raw.split(";"):
                stmt = stmt.strip()
                if stmt and not stmt.upper().startswith("USE "):
                    conn.execute(text(stmt))
        print("Tabla help_pages creada (SQL)")

    db = SessionLocal()
    try:
        seed_demo_help_pages_if_empty(db)
        count = db.execute(text("SELECT COUNT(*) FROM help_pages")).scalar()
        print(f"help_pages lista: {count} página(s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
