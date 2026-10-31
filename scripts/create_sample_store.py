"""
Create a fully seeded sample store (categories, products, logo, monthly license).

Usage (from backend/):
  python scripts/create_sample_store.py
  python scripts/create_sample_store.py --slug joyeria-muestra --name "Joyería Muestra"
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.roles import ROLE_CLIENT_1  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db.session import SessionLocal, init_db  # noqa: E402
from app.models.license import TenantLicense  # noqa: E402
from app.models.platform_product import PlatformProduct  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.tenant import Tenant, TenantMembership  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.store_sample_service import StoreSampleService  # noqa: E402
from app.services.store_settings_service import StoreSettingsService  # noqa: E402
from app.schemas.store_settings import StoreSettingsUpdate  # noqa: E402
from app.utils.license_billing import initial_monthly_period  # noqa: E402
from app.utils.license_plans import PLAN_FULL, PRINCIPAL_MEMBERSHIP_ROLE, max_users_for_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a sample Binfrix store")
    parser.add_argument("--slug", default="joyeria-muestra")
    parser.add_argument("--name", default="Joyería Muestra")
    parser.add_argument("--email", default="muestra@example.com")
    parser.add_argument("--password", default="Muestra2026!")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        product = db.get(PlatformProduct, "ecommerce-b2c")
        if product is None:
            print("ERROR: platform product ecommerce-b2c missing (run API once to seed)")
            return 1

        role = db.query(Role).filter(Role.slug == ROLE_CLIENT_1).first()
        if role is None:
            print("ERROR: client role missing")
            return 1

        tenant = db.query(Tenant).filter(Tenant.slug == args.slug).first()
        if tenant is None:
            tenant = Tenant(name=args.name, slug=args.slug, status="active")
            db.add(tenant)
            db.flush()
            print(f"Created tenant {tenant.slug} ({tenant.id})")
        else:
            print(f"Tenant already exists: {tenant.slug} ({tenant.id})")

        user = db.query(User).filter(User.email == args.email).first()
        if user is None:
            user = User(
                name="Dueño Muestra",
                email=args.email,
                password_hash=get_password_hash(args.password),
                role_id=role.id,
                is_superadmin=False,
            )
            db.add(user)
            db.flush()
            print(f"Created user {user.email}")
        else:
            print(f"User already exists: {user.email}")

        membership = (
            db.query(TenantMembership)
            .filter(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == user.id,
            )
            .first()
        )
        if membership is None:
            db.add(
                TenantMembership(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    role=PRINCIPAL_MEMBERSHIP_ROLE,
                )
            )

        license_row = (
            db.query(TenantLicense)
            .filter(
                TenantLicense.tenant_id == tenant.id,
                TenantLicense.platform_product_id == "ecommerce-b2c",
            )
            .first()
        )
        starts_at, ends_at = initial_monthly_period(date.today())
        if license_row is None:
            db.add(
                TenantLicense(
                    tenant_id=tenant.id,
                    platform_product_id="ecommerce-b2c",
                    status="active",
                    plan=PLAN_FULL,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    max_users=max_users_for_plan(PLAN_FULL),
                )
            )
        else:
            license_row.status = "active"
            license_row.plan = PLAN_FULL
            license_row.starts_at = starts_at
            license_row.ends_at = ends_at
            license_row.max_users = max_users_for_plan(PLAN_FULL)

        store_url = f"https://{args.slug}.binfrix.io"
        settings = StoreSettingsService(db, tenant_id=tenant.id)
        settings.get_or_create(tenant.id)
        settings.update_settings(StoreSettingsUpdate(store_url=store_url))
        StoreSampleService(db).seed_new_store(
            tenant.id,
            store_name=args.name,
            store_url=store_url,
        )
        db.commit()

        print("OK sample store ready")
        print(f"  URL:     {store_url}")
        print(f"  Admin:   {args.email} / {args.password}")
        print(f"  License: {starts_at.isoformat()} to {ends_at.isoformat()} (monthly free)")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
