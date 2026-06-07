from datetime import date


def generate_payment_number(count: int) -> str:
    return f"PAG-{count + 1:04d}"


def map_payment_status_to_order(status: str) -> str:
    mapping = {
        "completed": "paid",
        "pending": "pending",
        "refunded": "refunded",
        "failed": "pending",
    }
    return mapping.get(status, "pending")


def today() -> date:
    return date.today()
