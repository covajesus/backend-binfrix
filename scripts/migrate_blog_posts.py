"""Crea la tabla blog_posts y siembra artículos corporativos si está vacía."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from app.db.seed import seed_blog_posts_if_empty
from app.db.session import SessionLocal, engine, init_db
from app.db.blog_posts_schema import ensure_blog_post_columns


def main() -> None:
    init_db()
    inspector = inspect(engine)
    if "blog_posts" not in inspector.get_table_names():
        sql_path = ROOT / "scripts" / "migrate_blog_posts.sql"
        with engine.begin() as conn:
            raw = sql_path.read_text(encoding="utf-8-sig")
            for stmt in raw.split(";"):
                stmt = stmt.strip()
                if stmt and not stmt.upper().startswith("USE "):
                    conn.execute(text(stmt))
        print("Tabla blog_posts creada (SQL)")
    else:
        print("Tabla blog_posts ya existe")

    added = ensure_blog_post_columns()
    if added:
        print(f"Columnas añadidas: {', '.join(added)}")

    db = SessionLocal()
    try:
        seed_blog_posts_if_empty(db)
        count = db.execute(text("SELECT COUNT(*) FROM blog_posts")).scalar()
        print(f"blog_posts lista: {count} artículo(s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
