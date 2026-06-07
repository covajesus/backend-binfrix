import uuid
from datetime import date


def generate_order_number(count: int) -> str:
    return f"PED-{count + 1:04d}"


def calc_order_total(items: list[dict]) -> int:
    return sum(int(item.get("quantity") or 0) * int(item.get("unit_price") or 0) for item in items)


def normalize_line_items(items: list[dict]) -> list[dict]:
    normalized = []
    for item in items:
        normalized.append(
            {
                "id": item.get("id") or f"line-{uuid.uuid4().hex[:8]}",
                "product_title": item.get("product_title", ""),
                "sku": item.get("sku", ""),
                "quantity": int(item.get("quantity") or 0),
                "unit_price": int(item.get("unit_price") or 0),
            }
        )
    return normalized


def today() -> date:
    return date.today()
