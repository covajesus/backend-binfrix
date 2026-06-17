"""Migración manual: columnas store_settings (plantilla, idioma)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db.session import init_db
from app.db.store_settings_schema import ensure_store_settings_columns

init_db()
added = ensure_store_settings_columns()
if added:
    print("Columnas creadas:", ", ".join(added))
else:
    print("store_settings ya tiene todas las columnas")
