"""Validación de licencias tenant por producto SaaS."""

from datetime import date

from app.models.license import TenantLicense


def is_tenant_license_active(license_row: TenantLicense | None) -> bool:
    if license_row is None:
        return False
    if license_row.status != "active":
        return False
    today = date.today()
    if license_row.starts_at and license_row.starts_at > today:
        return False
    if license_row.ends_at and license_row.ends_at < today:
        return False
    return True
