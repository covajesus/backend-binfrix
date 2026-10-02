"""Crea/siembra páginas SEO del sitio corporativo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db.seed import seed_seo_pages_if_empty
from app.db.session import SessionLocal, init_db
from app.models.seo_page import SeoPage


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_seo_pages_if_empty(db)
        count = db.query(SeoPage).count()
        print(f"seo_pages lista: {count} página(s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
