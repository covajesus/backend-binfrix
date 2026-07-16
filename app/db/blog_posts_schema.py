"""Añade columnas faltantes en blog_posts (MySQL / tablas ya existentes)."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.session import engine


def ensure_blog_post_columns() -> list[str]:
    inspector = inspect(engine)
    if "blog_posts" not in inspector.get_table_names():
        return []

    cols = {c["name"] for c in inspector.get_columns("blog_posts")}
    added: list[str] = []

    if "cover_image_url" not in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE blog_posts "
                    "ADD COLUMN cover_image_url TEXT NULL"
                )
            )
            conn.execute(
                text(
                    "UPDATE blog_posts SET cover_image_url = '' "
                    "WHERE cover_image_url IS NULL"
                )
            )
        added.append("cover_image_url")

    return added
