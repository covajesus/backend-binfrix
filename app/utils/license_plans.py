"""Planes de licencia SaaS (usuarios incluidos por tenant)."""

from app.core.exceptions import AppError

PLAN_STANDARD = "standard"
PLAN_FULL = "full"

LICENSE_PLANS: dict[str, dict[str, str | int]] = {
    PLAN_STANDARD: {
        "name": "Standard",
        "description": "1 usuario (principal)",
        "max_users": 1,
    },
    PLAN_FULL: {
        "name": "Full",
        "description": "Hasta 10 usuarios",
        "max_users": 10,
    },
}

PRINCIPAL_MEMBERSHIP_ROLE = "admin"
STAFF_MEMBERSHIP_ROLE = "staff"


def normalize_plan(plan: str | None) -> str:
    key = (plan or PLAN_STANDARD).strip().lower()
    if key not in LICENSE_PLANS:
        raise AppError("Plan no válido. Usa standard o full.")
    return key


def max_users_for_plan(plan: str | None) -> int:
    return int(LICENSE_PLANS[normalize_plan(plan)]["max_users"])


def resolve_plan_and_max_users(plan: str | None, max_users: int | None) -> tuple[str, int]:
    plan_key = normalize_plan(plan)
    resolved_max = max_users if max_users is not None else max_users_for_plan(plan_key)
    plan_cap = max_users_for_plan(plan_key)
    if resolved_max > plan_cap:
        raise AppError(f"El plan {plan_key} permite hasta {plan_cap} usuarios")
    return plan_key, resolved_max


def list_plan_definitions() -> list[dict[str, str | int]]:
    return [
        {
            "id": plan_id,
            "name": str(meta["name"]),
            "description": str(meta["description"]),
            "max_users": int(meta["max_users"]),
        }
        for plan_id, meta in LICENSE_PLANS.items()
    ]
