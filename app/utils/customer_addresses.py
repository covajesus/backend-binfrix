"""Normalización de direcciones de envío en clientes storefront."""

from __future__ import annotations

import uuid
from typing import Any

MAX_SHIPPING_ADDRESSES = 10


def _clean_str(value: Any, max_len: int = 500) -> str:
    return str(value or "").strip()[:max_len]


def normalize_address(raw: dict) -> dict | None:
    address = _clean_str(raw.get("address"), 500)
    city = _clean_str(raw.get("city"), 120)
    if not address or not city:
        return None

    addr_id = _clean_str(raw.get("id"), 36)
    if not addr_id:
        addr_id = str(uuid.uuid4())

    return {
        "id": addr_id,
        "label": _clean_str(raw.get("label"), 80),
        "address": address,
        "city": city,
        "region": _clean_str(raw.get("region"), 120),
        "phone": _clean_str(raw.get("phone"), 50),
        "is_default": bool(raw.get("is_default")),
    }


def normalize_addresses(raw: list | None) -> list[dict]:
    if not raw:
        return []

    seen: set[str] = set()
    result: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        normalized = normalize_address(item)
        if normalized is None or normalized["id"] in seen:
            continue
        seen.add(normalized["id"])
        result.append(normalized)

    if not result:
        return []

    if not any(item["is_default"] for item in result):
        result[0]["is_default"] = True
    else:
        default_found = False
        for item in result:
            if item["is_default"] and not default_found:
                default_found = True
            else:
                item["is_default"] = False

    return result


def ensure_single_default(addresses: list[dict], default_id: str | None = None) -> list[dict]:
    if not addresses:
        return []

    if default_id:
        found = False
        for item in addresses:
            is_default = item["id"] == default_id
            item["is_default"] = is_default
            if is_default:
                found = True
        if not found:
            addresses[0]["is_default"] = True
    elif not any(item["is_default"] for item in addresses):
        addresses[0]["is_default"] = True
    else:
        default_set = False
        for item in addresses:
            if item["is_default"] and not default_set:
                default_set = True
            else:
                item["is_default"] = False

    return addresses


def get_default_address(addresses: list[dict]) -> dict | None:
    normalized = normalize_addresses(addresses)
    return next((item for item in normalized if item["is_default"]), None)
