"""Monthly license billing windows (calendar anniversary) and free auto-renew."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.license import TenantLicense


def add_calendar_month(value: date) -> date:
    """Advance one calendar month, clamping the day (e.g. Jan 31 → Feb 28)."""
    year = value.year + (1 if value.month == 12 else 0)
    month = 1 if value.month == 12 else value.month + 1
    last_day = monthrange(year, month)[1]
    return date(year, month, min(value.day, last_day))


def initial_monthly_period(start: date | None = None) -> tuple[date, date]:
    """Return (starts_at, ends_at) for a one-month window starting today (or start)."""
    starts_at = start or date.today()
    ends_at = add_calendar_month(starts_at)
    return starts_at, ends_at


def ensure_free_monthly_license(db: Session, license_row: TenantLicense | None) -> TenantLicense | None:
    """
    While free monthly plans are enabled, keep rolling ends_at forward
    in one-month steps so access never drops for unpaid tenants.
    """
    if license_row is None:
        return None

    settings = get_settings()
    if not settings.license_auto_renew_free:
        return license_row

    if license_row.status != "active":
        return license_row

    today = date.today()
    changed = False

    if license_row.starts_at is None:
        license_row.starts_at = today
        changed = True

    if license_row.ends_at is None:
        license_row.ends_at = add_calendar_month(license_row.starts_at)
        changed = True

    while license_row.ends_at is not None and license_row.ends_at < today:
        license_row.ends_at = add_calendar_month(license_row.ends_at)
        changed = True

    if changed:
        db.add(license_row)
        db.commit()
        db.refresh(license_row)

    return license_row
