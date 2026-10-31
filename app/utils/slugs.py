"""Build URL-safe store slugs from commercial names."""

from __future__ import annotations

import re
import unicodedata


def slugify_store_name(value: str, *, max_length: int = 48) -> str:
    text = unicodedata.normalize("NFKD", (value or "").strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if not text:
        text = "tienda"
    return text[:max_length].strip("-") or "tienda"
